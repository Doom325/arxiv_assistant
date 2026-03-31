import logging
from typing import List, Dict
from config import settings

logger = logging.getLogger(__name__)

DEFAULT_ENTITY_LABELS = ["Software", "Dataset", "Model", "Loss Function", "Metric", "Task", "Organization", "Hardware"]


class GLiNEREntityExtractor:
    """Entity extraction using GLiNER (lightweight, no LLM needed)."""

    def __init__(self, model_name: str = "urchade/gliner_small-v2.1"):
        try:
            from gliner import GLiNER
            logger.info(f"Loading GLiNER model: {model_name}")
            self.model = GLiNER.from_pretrained(model_name)
        except Exception as e:
            logger.error(f"Failed to load GLiNER model: {e}")
            self.model = None

    def extract_entities(self, text: str, labels: List[str] = None) -> List[Dict]:
        if not self.model or not text:
            return []
        if labels is None:
            labels = DEFAULT_ENTITY_LABELS
        try:
            entities = self.model.predict_entities(text, labels, threshold=0.5)
            seen = set()
            unique_entities = []
            for ent in entities:
                pair = (ent['label'].strip(), ent['text'].strip())
                if pair not in seen:
                    unique_entities.append({"type": pair[0], "value": pair[1]})
                    seen.add(pair)
            return unique_entities
        except Exception as e:
            logger.error(f"GLiNER entity extraction failed: {e}")
            return []


class LLMEntityExtractor:
    """Entity extraction using local LLM via Ollama (higher quality, requires GPU)."""

    def extract_entities(self, text: str, labels: List[str] = None) -> List[Dict]:
        if not text:
            return []
        try:
            from services.llm_service import llm_service
            if hasattr(llm_service, 'extract_entities'):
                return llm_service.extract_entities(text)
            else:
                logger.warning("LLM provider does not support extract_entities, falling back to GLiNER")
                return _gliner_fallback.extract_entities(text, labels)
        except Exception as e:
            logger.error(f"LLM entity extraction failed, falling back to GLiNER: {e}")
            return _gliner_fallback.extract_entities(text, labels)


# Lazy-loaded GLiNER fallback (only initialized if needed)
_gliner_fallback = None


def _get_gliner():
    global _gliner_fallback
    if _gliner_fallback is None:
        _gliner_fallback = GLiNEREntityExtractor()
    return _gliner_fallback


class NLPService:
    """Unified entity extraction service. Routes to GLiNER or LLM based on config."""

    def __init__(self):
        self._provider = None

    @property
    def provider(self):
        if self._provider is None:
            if settings.ENTITY_EXTRACTION_PROVIDER == "llm":
                logger.info("Using LLM-based entity extraction")
                self._provider = LLMEntityExtractor()
            else:
                logger.info("Using GLiNER entity extraction")
                self._provider = _get_gliner()
        return self._provider

    def extract_entities(self, text: str, labels: List[str] = None) -> List[Dict]:
        return self.provider.extract_entities(text, labels)


nlp_service = NLPService()
