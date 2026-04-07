from google import genai
from google.genai import types
import requests
import json
from abc import ABC, abstractmethod
from config import settings
from core.text_utils import sanitize_text as _sanitize_text
from services.prompts import SUMMARIZATION_PROMPT
from taxonomy import V6_COT_PROMPT
import logging

logger = logging.getLogger(__name__)

class LLMProvider(ABC):
    @abstractmethod
    def summarize_text(self, text: str) -> str:
        pass

    def sanitize_text(self, text: str) -> str:
        """Removes null bytes and UTF-16 surrogates. Delegates to core.text_utils."""
        return _sanitize_text(text)

    @abstractmethod
    def generate_embedding(self, text: str, output_dimensionality: int = None) -> list[float]:
        pass

    @abstractmethod
    def parse_citations(self, text: str) -> list[dict]:
        pass

    @abstractmethod
    def chat(self, history: list, user_message: str, context: str) -> str:
        pass

    def classify_paper(self, title: str, abstract: str) -> dict:
        """Classify a paper using the V6 CoT prompt. Returns parsed JSON or None on failure."""
        raise NotImplementedError("Subclass must implement classify_paper")

class GeminiProvider(LLMProvider):
    def __init__(self):
        self.client = genai.Client(api_key=settings.FINAL_GOOGLE_API_KEY)
        self.model_name = 'gemini-3-flash-preview' # User requested Gemini 3 Flash
        self.embedding_model = 'models/gemini-embedding-001'

    def summarize_text(self, text: str) -> str:
        prompt = SUMMARIZATION_PROMPT.format(text=self.sanitize_text(text[:30000]))
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini summarization error: {e}")
            raise e

    def generate_embedding(self, text: str, task_type: str = "retrieval_document", output_dimensionality: int = 3072) -> list[float]:
        try:
            content = self.sanitize_text(text)
            # task_type mapping if needed, but google-genai might handle it differently.
            # For now simple embed.
            
            result = self.client.models.embed_content(
                model=self.embedding_model,
                contents=content,
                config=types.EmbedContentConfig(
                    output_dimensionality=768,
                    task_type=task_type,
                )
            )
            return result.embeddings[0].values
        except Exception as e:
            logger.error(f"Gemini embedding error: {e}")
            return []

    def parse_citations(self, text: str) -> list[dict]:
        import json
        prompt = f"""
        Extract the papers cited in the following text. 
        For each citation, extract:
        1. Title: The title of the paper.
        2. Authors: A list of author names.
        3. URL: Any URL or link mentioned.
        4. Raw: The full original citation text.

        Text:
        {self.sanitize_text(text)}

        Return the result as a JSON list of objects. Each object should have keys: "title", "authors", "url", "raw".
        If you cannot find specific fields, use null or empty list for authors.
        Respond ONLY with the JSON.
        """
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            # Find JSON block
            # Find JSON block - non-greedy to avoid capturing extra data
            import re
            # Try to find the first balanced [ ] block
            # This is safer than greedy .*
            match = re.search(r'(\[[\s\S]*\])', response.text)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    # Retry with a stricter match if first one failed
                    # Often Gemini adds text after the block
                    clean_json = match.group(1)
                    # Simple attempt to find the last closing bracket
                    last_bracket = clean_json.rfind(']')
                    if last_bracket != -1:
                        return json.loads(clean_json[:last_bracket+1])
            return []
        except Exception as e:
            logger.error(f"Gemini citation parsing error: {e}")
            return []

    def chat(self, history: list, user_message: str, context: str) -> str:
        prompt = f"""
        Context from research papers:
        {context}

        User Question: {user_message}

        Answer the question based on the context provided.
        """
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini chat error: {e}")
            return "Error generating response."

    def classify_paper(self, title: str, abstract: str) -> dict:
        """Classify a paper using V6 CoT prompt via Gemini with JSON output."""
        prompt = V6_COT_PROMPT.format(
            title=self.sanitize_text(title),
            abstract=self.sanitize_text(abstract[:800])
        )
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1,
                )
            )
            return json.loads(response.text)
        except Exception as e:
            logger.error(f"Gemini classify_paper error: {e}")
            return None

class OllamaProvider(LLMProvider):
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.chat_model = settings.OLLAMA_CHAT_MODEL  # Gemma 3 27B: summarization, chat, entity extraction
        self.classification_model = settings.OLLAMA_CLASSIFICATION_MODEL or self.chat_model  # Gemma 3 12B: classification, citations
        self.embedding_model = settings.OLLAMA_EMBEDDING_MODEL
        self.num_ctx = settings.OLLAMA_NUM_CTX

    def _ollama_native_url(self) -> str:
        """Get the native Ollama API URL (without /v1 suffix)."""
        return self.base_url.replace("/v1", "")

    def _unwrap_json_list(self, content: str) -> list:
        """Parse JSON that may be a bare list or wrapped in an object."""
        parsed = json.loads(content)
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict):
            # Ollama's format:json may wrap the list in an object
            for key in ("citations", "references", "results", "data", "entities"):
                if key in parsed and isinstance(parsed[key], list):
                    return parsed[key]
            # Last resort: return first list value found
            for v in parsed.values():
                if isinstance(v, list):
                    return v
            return []
        return []

    def summarize_text(self, text: str) -> str:
        prompt = SUMMARIZATION_PROMPT.format(text=self.sanitize_text(text))
        payload = {
            "model": self.chat_model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"num_ctx": self.num_ctx}
        }
        try:
            response = requests.post(f"{self.base_url}/chat/completions", json=payload, timeout=1800)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            logger.error(f"Ollama summarization error: {e}")
            raise e

    def summarize_text_with_metrics(self, text: str) -> dict:
        """Returns {text, num_input_tokens, num_output_tokens}"""
        prompt = SUMMARIZATION_PROMPT.format(text=self.sanitize_text(text))
        payload = {
            "model": self.chat_model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"num_ctx": self.num_ctx}
        }
        try:
            response = requests.post(f"{self.base_url}/chat/completions", json=payload, timeout=1800)
            response.raise_for_status()
            data = response.json()
            content = data['choices'][0]['message']['content']

            usage = data.get('usage', {})
            prompt_tokens = usage.get('prompt_tokens', 0)
            completion_tokens = usage.get('completion_tokens', 0)

            # Fallback for native Ollama API keys if not using OpenAI compat
            if not prompt_tokens:
                prompt_tokens = data.get('prompt_eval_count', 0)
            if not completion_tokens:
                completion_tokens = data.get('eval_count', 0)

            return {
                "text": content,
                "num_input_tokens": prompt_tokens,
                "num_output_tokens": completion_tokens
            }
        except Exception as e:
            logger.error(f"Ollama metrics error: {e}")
            raise e

    def generate_embedding(self, text: str, output_dimensionality: int = None) -> list[float]:
        """
        Generates an embedding. output_dimensionality is ignored for Ollama
        as it depends on the model, but included for interface compatibility.
        """
        text = text.replace("\x00", "")
        truncated_text = text[:settings.OLLAMA_EMBEDDING_TRUNCATION]
        logger.info(f"Generating embedding for text ({len(truncated_text)} chars): {truncated_text[:100]}...")

        payload = {
            "model": self.embedding_model,
            "input": self.sanitize_text(truncated_text)
        }
        try:
            response = requests.post(f"{self.base_url}/embeddings", json=payload, timeout=900)
            response.raise_for_status()
            return response.json()['data'][0]['embedding']
        except Exception as e:
            logger.error(f"Ollama embedding error: {e}")
            if 'response' in locals():
                logger.error(f"Response body: {response.text}")
            return []

    def parse_citations(self, text: str) -> list[dict]:
        prompt = f"""
        Extract paper citations from the text below as a JSON list.
        Provide: title, authors (list), url (string or null), raw (full text).

        Text: {self.sanitize_text(text)}

        Respond ONLY with a JSON list.
        """
        # Use classification model (Gemma 3 12B) for citation parsing
        ollama_native_url = self._ollama_native_url()
        payload = {
            "model": self.classification_model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "format": "json",
            "options": {"num_ctx": self.num_ctx}
        }
        try:
            response = requests.post(f"{ollama_native_url}/api/chat", json=payload, timeout=600)
            response.raise_for_status()
            content = response.json().get("message", {}).get("content", "")
            return self._unwrap_json_list(content)
        except Exception as e:
            logger.error(f"Ollama citation parsing error: {e}")
            return []

    def chat(self, history: list, user_message: str, context: str) -> str:
        system_prompt = f"""
        You are a helpful AI research assistant. Use the following context to answer the user's question.

        Context:
        {context}
        """

        messages = [{"role": "system", "content": system_prompt}]
        messages.append({"role": "user", "content": user_message})

        payload = {
            "model": self.chat_model,
            "messages": messages,
            "stream": False,
            "options": {"num_ctx": self.num_ctx}
        }
        try:
            response = requests.post(f"{self.base_url}/chat/completions", json=payload, timeout=900)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            logger.error(f"Ollama chat error: {e}")
            return "Error generating response."

    def classify_paper(self, title: str, abstract: str) -> dict:
        """Classify a paper using V6 CoT prompt via Ollama with JSON output mode."""
        prompt = V6_COT_PROMPT.format(
            title=self.sanitize_text(title),
            abstract=self.sanitize_text(abstract[:800])
        )
        # Use classification model (Gemma 3 12B) via native Ollama API for JSON format
        ollama_native_url = self._ollama_native_url()
        payload = {
            "model": self.classification_model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "format": "json",
            "options": {"num_ctx": self.num_ctx, "temperature": 0.1}
        }
        try:
            response = requests.post(f"{ollama_native_url}/api/chat", json=payload, timeout=600)
            response.raise_for_status()
            content = response.json().get("message", {}).get("content", "")
            return json.loads(content)
        except Exception as e:
            logger.error(f"Ollama classify_paper error: {e}")
            return None

    def extract_entities(self, text: str) -> list[dict]:
        """Extract entities using LLM instead of GLiNER. Uses chat model (Gemma 3 27B)."""
        prompt = f"""Extract technical entities from the following research paper text.
For each entity, provide its type and value.

Valid entity types: Software, Dataset, Model, Loss Function, Metric, Task, Organization, Hardware

Text:
{self.sanitize_text(text[:8000])}

Return a JSON list of objects, each with "type" and "value" keys.
Example: [{{"type": "Model", "value": "GPT-4"}}, {{"type": "Dataset", "value": "ImageNet"}}]
Return ONLY the JSON list."""
        ollama_native_url = self._ollama_native_url()
        payload = {
            "model": self.chat_model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "format": "json",
            "options": {"num_ctx": self.num_ctx}
        }
        try:
            response = requests.post(f"{ollama_native_url}/api/chat", json=payload, timeout=600)
            response.raise_for_status()
            content = response.json().get("message", {}).get("content", "")
            entities = self._unwrap_json_list(content)
            # Deduplicate
            seen = set()
            unique = []
            for ent in entities:
                if isinstance(ent, dict) and "type" in ent and "value" in ent:
                    pair = (ent["type"].strip(), ent["value"].strip())
                    if pair not in seen:
                        unique.append({"type": pair[0], "value": pair[1]})
                        seen.add(pair)
            return unique
        except Exception as e:
            logger.error(f"Ollama entity extraction error: {e}")
            return []

def get_llm_service():
    if settings.AI_PROVIDER == "gemini":
        return GeminiProvider()
    else:
        return OllamaProvider()

def get_embedding_service():
    """Returns the provider used for embeddings. Can differ from the main LLM provider.

    This allows using Gemini for embeddings (MRL support, better retrieval quality)
    while using local models for everything else.
    """
    provider = settings.EMBEDDING_PROVIDER or settings.AI_PROVIDER
    if provider == "gemini":
        return GeminiProvider()
    else:
        return OllamaProvider()

llm_service = get_llm_service()
embedding_service = get_embedding_service()
