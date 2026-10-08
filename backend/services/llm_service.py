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

DEFAULT_SUMMARIZATION_TEMPERATURE = 0.3


class LLMProvider(ABC):
    @abstractmethod
    def summarize_text(self, text: str, model: str | None = None, temperature: float | None = None) -> str:
        pass

    def list_summarization_models(self) -> list[str]:
        """Return available model identifiers for summarization."""
        raise NotImplementedError("Subclass must implement list_summarization_models")

    def default_summarization_model(self) -> str | None:
        """The model used when no explicit override is supplied."""
        raise NotImplementedError("Subclass must implement default_summarization_model")

    def sanitize_text(self, text: str) -> str:
        """Removes null bytes and UTF-16 surrogates. Delegates to core.text_utils."""
        return _sanitize_text(text)

    @abstractmethod
    def generate_embedding(self, text: str, output_dimensionality: int = None) -> list[float]:
        pass

    @abstractmethod
    def chat(self, history: list, user_message: str, context: str) -> str:
        pass

    def classify_paper(self, title: str, abstract: str) -> dict:
        """Classify a paper using the V6 CoT prompt. Returns parsed JSON or None on failure."""
        raise NotImplementedError("Subclass must implement classify_paper")

_GEMINI_SUMMARIZATION_MODEL = 'gemini-3.8-flash'

# Co-located with _GEMINI_SUMMARIZATION_MODEL so additions/removals stay together.
# Gemini's /models endpoint returns embedding + legacy models we don't want to
# surface as summarization choices, so we curate this list manually based on
# models available over the API supporting generateContent.
_GEMINI_SUMMARIZATION_MODELS = [
    _GEMINI_SUMMARIZATION_MODEL,
    'gemini-3.7-flash',
    'gemini-3.6-flash',
    'gemini-3.5-flash',
    'gemini-3.5-flash-lite',
    'gemini-3.1-pro-preview',
    'gemini-3.1-flash-lite',
    'gemini-3-flash-preview',
    'gemini-2.5-pro',
    'gemini-2.5-flash',
    'gemini-flash-latest',
    'gemini-pro-latest',
    'gemini-flash-lite-latest',
]


class GeminiProvider(LLMProvider):
    def __init__(self):
        self.client = genai.Client(api_key=settings.FINAL_GOOGLE_API_KEY)
        self.model_name = _GEMINI_SUMMARIZATION_MODEL
        self.embedding_model = 'models/gemini-embedding-001'

    def summarize_text(self, text: str, model: str | None = None, temperature: float | None = None) -> str:
        prompt = SUMMARIZATION_PROMPT.format(text=self.sanitize_text(text[:30000]))
        temp = DEFAULT_SUMMARIZATION_TEMPERATURE if temperature is None else temperature
        try:
            response = self.client.models.generate_content(
                model=model or self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=temp),
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini summarization error: {e}")
            raise e

    def list_summarization_models(self) -> list[str]:
        return list(_GEMINI_SUMMARIZATION_MODELS)

    def default_summarization_model(self) -> str:
        return self.model_name

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
    """Local-LLM provider that talks to the LiteLLM gateway via OpenAI-
    compatible endpoints. Named `OllamaProvider` for continuity with the
    `AI_PROVIDER=local` code paths; the backing gateway is LiteLLM.
    """

    def __init__(self):
        self.base_url = settings.LITELLM_BASE_URL
        self.api_key = settings.LITELLM_API_KEY
        self.chat_model = settings.LLM_CHAT_MODEL
        self.summarization_model = settings.LLM_SUMMARIZATION_MODEL or self.chat_model
        self.entity_model = settings.LLM_ENTITY_MODEL or self.chat_model
        self.classification_model = settings.LLM_CLASSIFICATION_MODEL or self.chat_model
        self.embedding_model = settings.LLM_EMBEDDING_MODEL

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    def _chat_url(self) -> str:
        return f"{self.base_url.rstrip('/')}/chat/completions"

    def _embed_url(self) -> str:
        return f"{self.base_url.rstrip('/')}/embeddings"

    @staticmethod
    def _strip_md_fences(s: str) -> str:
        """Strip surrounding ```json ... ``` (or plain ```) code fences if a model
        wraps its JSON in them despite response_format=json_object."""
        s = (s or "").strip()
        if s.startswith("```"):
            nl = s.find("\n")
            if nl != -1:
                s = s[nl + 1:]
            if s.rstrip().endswith("```"):
                s = s.rstrip()[:-3]
        return s.strip()

    def _unwrap_json_list(self, content: str) -> list:
        """Parse JSON that may be a bare list, wrapped in an object, or
        wrapped in markdown code fences (some local models do this even
        with response_format=json_object)."""
        parsed = json.loads(self._strip_md_fences(content))
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict):
            # response_format=json_object forces a top-level object, so the
            # list is usually keyed by an obvious name.
            for key in ("citations", "references", "results", "data", "entities"):
                if key in parsed and isinstance(parsed[key], list):
                    return parsed[key]
            for v in parsed.values():
                if isinstance(v, list):
                    return v
            return []
        return []

    def summarize_text(self, text: str, model: str | None = None, temperature: float | None = None) -> str:
        prompt = SUMMARIZATION_PROMPT.format(text=self.sanitize_text(text))
        payload = {
            "model": model or self.summarization_model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 3000,
            "temperature": DEFAULT_SUMMARIZATION_TEMPERATURE if temperature is None else temperature,
            "stream": False,
        }
        try:
            response = requests.post(self._chat_url(), headers=self._headers(), json=payload, timeout=1800)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            logger.error(f"Gateway summarization error: {e}")
            raise e

    def list_summarization_models(self) -> list[str]:
        url = f"{self.base_url.rstrip('/')}/models"
        try:
            response = requests.get(url, headers=self._headers(), timeout=10)
            response.raise_for_status()
            data = response.json().get("data", [])
            return sorted({item["id"] for item in data if isinstance(item, dict) and item.get("id")})
        except Exception as e:
            logger.warning(f"Gateway model listing failed, falling back to configured models: {e}")
            fallbacks = [
                self.summarization_model,
                self.chat_model,
                self.entity_model,
                self.classification_model,
            ]
            seen, out = set(), []
            for m in fallbacks:
                if m and m not in seen:
                    seen.add(m)
                    out.append(m)
            return out

    def default_summarization_model(self) -> str:
        return self.summarization_model

    def summarize_text_with_metrics(self, text: str) -> dict:
        """Returns {text, num_input_tokens, num_output_tokens}"""
        prompt = SUMMARIZATION_PROMPT.format(text=self.sanitize_text(text))
        payload = {
            "model": self.summarization_model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 3000,
            "temperature": DEFAULT_SUMMARIZATION_TEMPERATURE,
            "stream": False,
        }
        try:
            response = requests.post(self._chat_url(), headers=self._headers(), json=payload, timeout=1800)
            response.raise_for_status()
            data = response.json()
            content = data['choices'][0]['message']['content']

            usage = data.get('usage', {})
            prompt_tokens = usage.get('prompt_tokens', 0)
            completion_tokens = usage.get('completion_tokens', 0)

            return {
                "text": content,
                "num_input_tokens": prompt_tokens,
                "num_output_tokens": completion_tokens
            }
        except Exception as e:
            logger.error(f"Gateway metrics error: {e}")
            raise e

    def generate_embedding(self, text: str, output_dimensionality: int = None) -> list[float]:
        """Generate an embedding through the gateway's /v1/embeddings endpoint.

        output_dimensionality is accepted for interface parity but ignored —
        the gateway-registered model decides the vector dimensionality.
        """
        text = text.replace("\x00", "")
        truncated_text = text[:settings.LLM_EMBEDDING_TRUNCATION]
        logger.info(f"Generating embedding for text ({len(truncated_text)} chars): {truncated_text[:100]}...")

        payload = {
            "model": self.embedding_model,
            "input": self.sanitize_text(truncated_text)
        }
        try:
            response = requests.post(self._embed_url(), headers=self._headers(), json=payload, timeout=900)
            response.raise_for_status()
            return response.json()['data'][0]['embedding']
        except Exception as e:
            logger.error(f"Gateway embedding error: {e}")
            if 'response' in locals():
                logger.error(f"Response body: {response.text}")
            return []

    def parse_citations(self, text: str) -> list[dict]:
        prompt = f"""Extract the bibliographic references/citations from the text below.

For each distinct cited work, output an object with:
- "raw": the full reference string as it appears
- "title": the paper/work title (string, or null if not identifiable)
- "authors": list of author names (may be empty)
- "url": a URL or arXiv id if present (string or null)

Text:
{self.sanitize_text(text)}

Respond with ONLY a JSON object of the form {{"citations": [ ... ]}} — no commentary. If there are no references, return {{"citations": []}}."""
        payload = {
            "model": self.classification_model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "response_format": {"type": "json_object"},
            # Disable the reasoning model's <think> trace (see classify_paper) and bound
            # the output — reference lists are long, so allow generous headroom.
            "chat_template_kwargs": {"enable_thinking": False},
            "max_tokens": 4096,
        }
        try:
            response = requests.post(self._chat_url(), headers=self._headers(), json=payload, timeout=600)
            response.raise_for_status()
            content = response.json()['choices'][0]['message']['content']
            return self._unwrap_json_list(content)
        except Exception as e:
            logger.error(f"Gateway citation parsing error: {e}")
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
        }
        try:
            response = requests.post(self._chat_url(), headers=self._headers(), json=payload, timeout=900)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            logger.error(f"Gateway chat error: {e}")
            return "Error generating response."

    def classify_paper(self, title: str, abstract: str) -> dict:
        """Classify a paper using V6 CoT prompt through the gateway."""
        prompt = V6_COT_PROMPT.format(
            title=self.sanitize_text(title),
            abstract=self.sanitize_text(abstract[:800])
        )
        payload = {
            "model": self.classification_model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "response_format": {"type": "json_object"},
            "temperature": 0.1,
            # Reasoning models (e.g. nemotron3:nano, a hybrid SSM-MoE) otherwise emit a
            # large unbounded <think> trace before the JSON — ~5x the output tokens and
            # ~5x slower per call. Disable native thinking: the V6 CoT "reasoning" field
            # inside the JSON is preserved (bounded) and drives classification accuracy.
            # Also bounds the JSON so a malformed run can't decode indefinitely.
            # (chat_template_kwargs survives LiteLLM drop_params; verified on the gateway.)
            "chat_template_kwargs": {"enable_thinking": False},
            "max_tokens": 1024,
        }
        try:
            response = requests.post(self._chat_url(), headers=self._headers(), json=payload, timeout=600)
            response.raise_for_status()
            content = response.json()['choices'][0]['message']['content']
            return json.loads(content)
        except Exception as e:
            logger.error(f"Gateway classify_paper error: {e}")
            return None

    def extract_entities(self, text: str) -> list[dict]:
        """Extract entities using LLM instead of GLiNER."""
        prompt = f"""Extract technical entities from the following research paper text.
For each entity, provide its type and value.

Valid entity types: Software, Dataset, Model, Loss Function, Metric, Task, Organization, Hardware

Text:
{self.sanitize_text(text[:8000])}

Return a JSON object with a single key "entities" whose value is a list of objects, each with "type" and "value" keys.
Example: {{"entities": [{{"type": "Model", "value": "GPT-4"}}, {{"type": "Dataset", "value": "ImageNet"}}]}}"""
        payload = {
            "model": self.entity_model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "response_format": {"type": "json_object"},
        }
        try:
            response = requests.post(self._chat_url(), headers=self._headers(), json=payload, timeout=600)
            response.raise_for_status()
            content = response.json()['choices'][0]['message']['content']
            entities = self._unwrap_json_list(content)
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
            logger.error(f"Gateway entity extraction error: {e}")
            return []

def get_llm_service():
    if settings.AI_PROVIDER == "gemini":
        return GeminiProvider()
    else:
        return OllamaProvider()


_gemini_summarization_provider: GeminiProvider | None = None
_local_summarization_provider: OllamaProvider | None = None


def get_summarization_provider(model: str | None) -> tuple[LLMProvider, str]:
    """Pick the right provider for a summarization request based on the chosen
    model. Returns (provider, provider_name).

    Routing rules:
    - If ``model`` is in the curated Gemini list, route to Gemini (requires GEMINI_API_KEY).
    - Else, route to the LiteLLM gateway (Ollama-compatible path).
    - If ``model`` is None, fall back to the configured ``AI_PROVIDER``.

    Both providers are lazy-constructed and cached so the dropdown can mix
    Gemini + local models regardless of which AI_PROVIDER is configured.
    """
    global _gemini_summarization_provider, _local_summarization_provider

    is_gemini = bool(model) and model in set(_GEMINI_SUMMARIZATION_MODELS)
    if model is None:
        is_gemini = settings.AI_PROVIDER == "gemini"

    if is_gemini:
        if _gemini_summarization_provider is None:
            _gemini_summarization_provider = GeminiProvider()
        return _gemini_summarization_provider, "gemini"

    if _local_summarization_provider is None:
        _local_summarization_provider = OllamaProvider()
    return _local_summarization_provider, "local"


def list_all_summarization_models() -> list[dict]:
    """Union of Gemini + local gateway models, each tagged with its provider.
    Gemini models are only included when GEMINI_API_KEY is configured;
    gateway models are only included when the gateway responds (or via the
    fallback to configured model names if it doesn't).
    """
    out: list[dict] = []

    if settings.FINAL_GOOGLE_API_KEY:
        for m in _GEMINI_SUMMARIZATION_MODELS:
            out.append({"id": m, "provider": "gemini"})

    try:
        local = OllamaProvider().list_summarization_models()
    except Exception as e:
        logger.warning(f"Local provider model listing failed: {e}")
        local = []
    for m in local:
        out.append({"id": m, "provider": "local"})

    return out

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
