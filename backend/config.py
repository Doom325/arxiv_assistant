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
    OLLAMA_BASE_URL: str = "http://localhost:11434/v1"
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"
    OLLAMA_CHAT_MODEL: str = "gemma3:27b"  # Summarization, chat, entity extraction
    OLLAMA_CLASSIFICATION_MODEL: str = "gemma3:12b"  # Classification + citation parsing
    OLLAMA_EMBEDDING_TRUNCATION: int = 8000  # Chars to send for embedding (nomic-embed-text supports ~8k tokens)
    OLLAMA_NUM_CTX: int = 65536  # Context window for local models
    PDF_SAVE_DIR: str = "data"

    # Entity extraction provider: "gliner" (default) or "llm"
    ENTITY_EXTRACTION_PROVIDER: str = "gliner"

    # Query embedding cache
    QUERY_CACHE_LRU_SIZE: int = 1024

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
