import logging
import os
from services.arxiv_service import arxiv_service
from services.llm_service import llm_service, get_summarization_provider
from services.prompts import SUMMARIZATION_PROMPT_MLX

# Try importing MLX (only works on Apple Silicon)
try:
    from mlx_lm import load, generate
    HAS_MLX = True
except ImportError:
    HAS_MLX = False

# Configure logger
logger = logging.getLogger(__name__)
# Do not add StreamHandler here; rely on the root logger configuration from main.py/worker.py

class SummarizationService:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.model_repo = "mlx-community/gemma-3-4b-it-4bit"

    def load_model(self):
        if HAS_MLX and not self.model:
            logger.info(f"Loading model {self.model_repo}...")
            self.model, self.tokenizer = load(self.model_repo)
            logger.info("Model loaded.")

    def generate_summary(
        self,
        pdf_path: str,
        model: str | None = None,
        temperature: float | None = None,
        provider: str | None = None,
        endpoint: str | None = None,
    ) -> str:
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        # 1. Extract Text
        text = arxiv_service.extract_text(pdf_path)
        if not text:
            raise ValueError("Failed to extract text from PDF")

        # MLX is a Mac dev-only fallback used by mac_worker and ignores
        # user-supplied model/temperature. On real deployments (Khadas, Framework)
        # HAS_MLX is False and routing is decided per-model/provider:
        if HAS_MLX and not model and not provider and not endpoint:
            return self._generate_with_mlx(text, pdf_path)

        provider_inst, provider_name = get_summarization_provider(
            model=model, provider=provider, endpoint=endpoint
        )
        logger.info(
            f"Routing summarization of {pdf_path} via provider={provider_name} "
            f"(model={model or 'default'}, temp={temperature}, endpoint={endpoint or 'default'})"
        )
        return provider_inst.summarize_text(text, model=model, temperature=temperature)

    def _generate_with_mlx(self, text: str, pdf_path: str) -> str:
        # Load Model (Lazy load)
        self.load_model()

        prompt = SUMMARIZATION_PROMPT_MLX.format(text=text)

        # Generate
        logger.info(f"Starting MLX summary generation for {pdf_path}...")
        
        response = generate(
            self.model, 
            self.tokenizer, 
            prompt=prompt, 
            max_tokens=1024, 
            verbose=True  # Enable verbose to see tokens in console
        )
        
        logger.info("Summary generation complete!")
        return response

    def generate_summary_with_metrics(self, pdf_path: str):
        """Returns summary AND metrics: {text, input_tokens, output_tokens, chars}"""
        self.load_model()
        
        if not os.path.exists(pdf_path):
             return None
             
        text = arxiv_service.extract_text(pdf_path)
        if not text:
             return None

        # Fallback for non-MLX environments (e.g. Khadas with Ollama)
        if not HAS_MLX:
            logger.info(f"MLX not available, falling back to LLM service metrics for {pdf_path}")
            llm_metrics = llm_service.summarize_text_with_metrics(text)
            return {
                "text": llm_metrics["text"],
                "num_chars": len(text),
                "num_input_tokens": llm_metrics["num_input_tokens"],
                "num_output_tokens": llm_metrics["num_output_tokens"]
            }
             
        prompt = SUMMARIZATION_PROMPT_MLX.format(text=text)
        # Count Input Tokens
        input_ids = self.tokenizer.encode(prompt)
        num_input_tokens = len(input_ids)
        
        logger.info(f"Generating summary for {pdf_path} (Input: {num_input_tokens} tokens)...")
        
        response = generate(
            self.model, 
            self.tokenizer, 
            prompt=prompt, 
            max_tokens=1024, 
            verbose=False # We handle logging
        )
        
        # Count Output Tokens
        output_ids = self.tokenizer.encode(response)
        num_output_tokens = len(output_ids)
        
        return {
            "text": response,
            "num_chars": len(text),
            "num_input_tokens": num_input_tokens,
            "num_output_tokens": num_output_tokens
        }

summarization_service = SummarizationService()
