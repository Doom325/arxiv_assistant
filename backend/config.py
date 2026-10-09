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
    FRONTEND_URL: str = "http://localhost:3000"

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
    NVIDIA_API_KEY: str = ""
    NVIDIA_BASE_URL: str = "https://integrate.api.nvidia.com/v1"
    LLM_NVIDIA_MODEL: str = "meta/llama-3.3-70b-instruct"
    LLM_EMBEDDING_MODEL: str = "embeddinggemma:latest"
    LLM_CHAT_MODEL: str = "nemotron3:nano"  # RAG chat + summarization + universal fallback. nemotron-3-nano (hybrid SSM-MoE) — ~4-7x faster than gemma4:31b at equal/better quality
    LLM_SUMMARIZATION_MODEL: str | None = None  # Falls back to LLM_CHAT_MODEL if unset
    LLM_ENTITY_MODEL: str | None = None  # Falls back to LLM_CHAT_MODEL if unset
    LLM_CLASSIFICATION_MODEL: str = "nemotron3:nano"  # Classification + citation parsing (consolidated onto nemotron3:nano)
    LLM_EMBEDDING_TRUNCATION: int = 8000  # Chars to send for embedding (client-side truncation)
    PDF_SAVE_DIR: str = "data"

    # GROBID (academic PDF → structured references). Replaces the old LLM-
    # based citation extraction. Runs as a Docker service; see docker-compose.yml.
    GROBID_URL: str = "http://grobid:8070"

    # Entity extraction provider: "gliner" (default) or "llm"
    ENTITY_EXTRACTION_PROVIDER: str = "gliner"

    # Query embedding cache
    QUERY_CACHE_LRU_SIZE: int = 1024

    # Background worker concurrency. Each in-flight paper holds one DB session
    # plus active HTTP connections to the LiteLLM gateway. The worker creates
    # its own engine in production_worker.py sized to WORKER_CONCURRENCY+5
    # (max_overflow=20), so these knobs control both pool pressure and gateway
    # load.
    WORKER_CONCURRENCY: int = 4         # Number of papers processed in parallel
    WORKER_BATCH_SIZE: int = 20         # How many papers fetched per loop iteration
    WORKER_LLM_CONCURRENCY: int = 2     # Cap simultaneous LLM/embedding calls
    WORKER_BACKLOG_DAYS: int = 0        # 0 = no date filter (process full backlog); >0 = recent-N-days only
    WORKER_IDLE_SLEEP_SECONDS: int = 30 # Sleep when nothing to process
    WORKER_BATCH_PAUSE_SECONDS: int = 2 # Brief pause between batches

    # Summarization concurrency guard. A POST to /papers/{id}/summarize is
    # rejected with 409 if another attempt is already pending/running and was
    # touched within this many seconds. After the threshold, the prior attempt
    # is assumed dead (worker crash, lost background task) and the retry is
    # allowed to claim the slot.
    SUMMARY_RUN_STALE_THRESHOLD_SECONDS: int = 600

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
