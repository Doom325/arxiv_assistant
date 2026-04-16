import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://user:password@localhost/arxiv_db"
    GOOGLE_API_KEY: str = ""
    GEMINI_API_KEY: str = ""

    @property
    def FINAL_GOOGLE_API_KEY(self) -> str:
        return self.GEMINI_API_KEY or self.GOOGLE_API_KEY

    EMAIL_SENDER: str = "user@example.com"
    EMAIL_PASSWORD: str = "password"
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    EMAIL_RECIPIENTS: str = "sumanth.gttpt@gmail.com" # Comma separated list
    RESEND_API_KEY: str = ""

    @property
    def RECIPIENT_LIST(self) -> list[str]:
        return [email.strip() for email in self.EMAIL_RECIPIENTS.split(",") if email.strip()]

    # AI Provider Config
    AI_PROVIDER: str = "local" # "local" or "gemini" — controls LLM tasks (summarization, classification, etc.)
    EMBEDDING_PROVIDER: str = ""  # Override for embeddings only. If empty, falls back to AI_PROVIDER. Set to "gemini" to keep Gemini embeddings while using local LLMs.
    # LiteLLM gateway (replaces the old direct-to-Ollama connection). Model
    # names below stay Ollama-compatible — the gateway aliases them.
    LITELLM_BASE_URL: str = "http://192.168.1.32:4000/v1"
    LITELLM_API_KEY: str = ""
    LLM_EMBEDDING_MODEL: str = "embeddinggemma:latest"
    LLM_CHAT_MODEL: str = "gemma3:27b"  # RAG chat + universal fallback for dedicated *_MODEL vars
    LLM_SUMMARIZATION_MODEL: str | None = None  # Falls back to LLM_CHAT_MODEL if unset
    LLM_ENTITY_MODEL: str | None = None  # Falls back to LLM_CHAT_MODEL if unset
    LLM_CLASSIFICATION_MODEL: str = "gemma3:12b"  # Classification + citation parsing
    LLM_EMBEDDING_TRUNCATION: int = 8000  # Chars to send for embedding (client-side truncation)
    PDF_SAVE_DIR: str = "data"

    # Entity extraction provider: "gliner" (default) or "llm"
    ENTITY_EXTRACTION_PROVIDER: str = "gliner"

    # Query embedding cache
    QUERY_CACHE_LRU_SIZE: int = 1024

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
