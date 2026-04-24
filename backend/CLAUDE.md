# arxiv_assistant — Backend

FastAPI backend serving the arxiv_assistant API, background workers, and scheduled tasks.

## Stack

- **Framework:** FastAPI + uvicorn, Python 3.12
- **Database:** PostgreSQL 16 + pgvector via SQLAlchemy ORM (pool size 20, overflow 30)
- **LLM:** Google Gemini API (embeddings 768-3072D, summarization, chat, citation parsing, pattern classification)
- **Local LLM:** Ollama (fallback), MLX (Apple Silicon dev via `mac_worker.py`)
- **Entity extraction:** GLiNER (Software, Dataset, Model, Loss Function, Metric, Task, Organization, Hardware)
- **Email:** Resend API for daily digest delivery
- **Google Drive:** OAuth2 integration for bookmark export
- **Testing:** pytest with markers (remote, live, mlx)

## Entry Points

- `main.py` — FastAPI app (CORS, lifespan, router registration, error handling, static files, scheduler startup)
- `production_worker.py` — Background worker (PDF download/extraction, embedding generation, entity extraction, citation parsing, pattern classification)
- `scheduler.py` — APScheduler daemon: paper poll (daily 05:30 IST, date-range query with per-category high-water mark), email digest (7 AM IST), batch summarization (11 PM IST)
- `batch_embed_manager.py` — Bulk embedding processing via Gemini Batch API
- `mac_worker.py` — Development worker for Apple Silicon using local MLX models

## API Routers

| Router | Prefix | Purpose |
|--------|--------|---------|
| `papers.py` | `/papers` | Paper CRUD, list with category/date filters, similar papers (vector similarity), manual add by ID/URL |
| `search.py` | `/papers` | Hybrid semantic + keyword search with RRF ranking, metadata filters (category:, after:, before:, author:, entity:) |
| `integrations.py` | (multiple) | On-demand summarization, email sending, Google Drive bookmark sync |
| `library.py` | `/library` | User bookmarks: add/remove, list management, fetch with metadata |
| `users.py` | `/users` | User config: keywords, arXiv categories, schedule preferences |
| `batch.py` | `/batch` | Batch job management: trigger daily job, queue papers, view pending |
| `citations.py` | `/citations` | Citation analytics: most-cited papers with category/date filters |
| `patterns.py` | `/patterns` | Agentic pattern taxonomy overview, paper classification results, filter by pattern/date |
| `analytics.py` | `/analytics` | Dashboard stats: papers-over-time (day/week/month), category distribution, summary counts |

## Services

| Service | Purpose |
|---------|---------|
| `llm_service.py` | `LLMProvider` abstraction with `GeminiProvider` and `OllamaProvider` — embeddings, summarization, chat, citation parsing, classification |
| `arxiv_service.py` | arXiv API client with 3s rate limiting — fetch papers, get by ID, download PDF |
| `pdf_service.py` | PDF pipeline — text extraction, citation extraction (LLM or MLX fallback), section extraction (Abstract, Introduction) |
| `email_service.py` | Resend API — daily digest emails, paper summary emails (HTML + text) |
| `gdrive.py` | Google Drive OAuth2 flow, file upload (resumable), list, delete |
| `batch_service.py` | Gemini Batch API wrapper — JSONL creation, upload, job submission, result processing |
| `citation_service.py` | Citation resolution — regex arXiv ID extraction, link to local papers in CitationLink table |
| `summarization_service.py` | Gemini + MLX summarization with metrics tracking |
| `nlp_service.py` | GLiNER entity extraction with deduplication |
| `prompts.py` | Centralized system prompts (summarization, retrieval) |

## Models (SQLAlchemy ORM)

| File | Models |
|------|--------|
| `paper.py` | `Paper` (metadata, pgvector embedding, tsvector search, extracted sections, citations/entities JSON), `PaperEmbedding` (multi-embedding support) |
| `user.py` | `User`, `UserConfig` (per-email keywords/categories/schedule), `UserLibrary` (bookmarks with list_name grouping) |
| `jobs.py` | `JobLog` (audit trail), `SummarizationMetric` (token/memory metrics), `BatchQueue` (pending summarization) |
| `citation.py` | `CitationLink` (directed source → target graph with resolved_paper_id) |
| `pattern.py` | `PromptTemplate`, `PatternExperimentResult` (is_agentic, primary_category, patterns JSON, taxonomy violations, quality metrics) |

## Project Structure

```
backend/
├── main.py                 # FastAPI app entry point
├── config.py               # Pydantic settings from env vars
├── database.py             # SQLAlchemy engine & session factory
├── schemas.py              # Pydantic response models
├── production_worker.py    # Background PDF/embedding/entity/citation worker
├── mac_worker.py           # Dev worker for Apple Silicon (MLX)
├── scheduler.py            # APScheduler daemon (3 scheduled jobs)
├── batch_embed_manager.py  # Bulk historical embeddings via Batch API
├── ingestion.py            # Paper ingestion pipeline (metadata only)
├── taxonomy.py             # V6 CoT prompt for agentic pattern classification
├── run_pattern_experiment.py # Batch paper classification
├── backfill_patterns.py    # Backfill pattern results
├── bulk_ingest.py          # Bulk ingestion utilities
├── batch_ingest.py         # Batch ingestion utilities
├── pdf_processor.py        # Local PDF processing (Mac dev)
├── migrate_*.py            # 8 migration scripts for schema evolution
├── models/                 # SQLAlchemy ORM models (split by domain)
│   ├── __init__.py         # Re-exports all 12 models
│   ├── base.py             # Declarative base
│   ├── paper.py            # Paper, PaperEmbedding
│   ├── user.py             # User, UserConfig, UserLibrary
│   ├── jobs.py             # JobLog, SummarizationMetric, BatchQueue
│   ├── citation.py         # CitationLink
│   └── pattern.py          # PromptTemplate, PatternExperimentResult
├── routers/                # API endpoint modules (9 routers)
│   ├── papers.py           # Paper CRUD, similarity search
│   ├── search.py           # Hybrid semantic + keyword search, RAG chat
│   ├── integrations.py     # Google Drive, email, paper ingestion
│   ├── library.py          # User bookmarks/library
│   ├── users.py            # User management
│   ├── batch.py            # Batch job management
│   ├── citations.py        # Citation analytics
│   ├── patterns.py         # Pattern taxonomy & experiments
│   └── analytics.py        # Dashboard analytics (papers-over-time, category distribution, stats)
├── services/               # Business logic layer (10 services)
│   ├── llm_service.py      # Gemini/Ollama provider abstraction
│   ├── arxiv_service.py    # arXiv API client
│   ├── pdf_service.py      # PDF text/section/citation extraction
│   ├── batch_service.py    # Gemini Batch API wrapper
│   ├── citation_service.py # Citation extraction & linking
│   ├── email_service.py    # Resend email integration
│   ├── summarization_service.py # Gemini + MLX summarization
│   ├── nlp_service.py      # GLiNER entity extraction
│   ├── gdrive.py           # Google Drive integration
│   └── prompts.py          # System prompts for LLM
├── core/                   # Shared utilities
│   ├── pdf_utils.py        # PDF download, local path management
│   └── text_utils.py       # Text sanitization (null bytes, UTF-16 surrogates)
├── scripts/                # Utility scripts
│   ├── backfill.py         # Historical data population
│   ├── backfill_embeddings.py
│   ├── extract_entities_backfill.py
│   ├── benchmark_models.py # Performance testing
│   ├── seed_db.py          # Sample data initialization
│   ├── repair/             # 7 data integrity fix scripts
│   ├── diagnostics/        # 32 debugging/analysis scripts
│   ├── email/              # 7 email template test scripts
│   ├── node_bulk/          # 9 Node-based bulk processing prototypes
│   └── prototypes/         # 5 experimental feature scripts
├── tests/                  # 34 pytest test files
├── requirements.txt
├── Dockerfile              # Python 3.12-slim container
└── Makefile                # Test/lint targets
```

## Key Patterns

- **Hybrid Search:** Semantic (pgvector cosine/L2 distance) + keyword (PostgreSQL full-text on tsvector with GIN index) merged via Reciprocal Rank Fusion (RRF)
- **Embeddings:** Gemini generates 768-3072 dimension vectors stored in pgvector columns
- **Provider Abstraction:** `LLMProvider` base class enables Gemini/Ollama/MLX swapping via `AI_PROVIDER` config
- **Service Singletons:** Lazy-loaded global instances (llm_service, arxiv_service, email_service, etc.)
- **DB Sessions:** SQLAlchemy sessions via FastAPI dependency injection (`database.get_db`)
- **Lifespan Management:** FastAPI lifespan hook starts scheduler and creates default user on startup
- **Batch Processing:** Gemini Batch API for cost-effective bulk summarization and embeddings
- **Citation Graph:** Directed citation links with arXiv ID resolution to local papers

## Processing Pipeline

1. **Ingestion:** Scheduler polls arXiv daily at 05:30 IST using a `submittedDate` range query with a per-category high-water mark (`CategoryPollState`) → `ingestion.process_paper_entry()` → creates Paper record (metadata only). Missed runs self-heal because the next run re-queries from the last success date onwards.
2. **Worker Processing:** `production_worker` polls for unprocessed papers (batch of 5, last 20 days) → downloads PDF → extracts text/sections → generates 3072D embedding → extracts entities (GLiNER) → parses citations (LLM) → resolves citations → classifies patterns (V6 CoT taxonomy)
3. **Batch Summarization:** Nightly job (11 PM IST) collects unsummarized papers → submits to Gemini Batch API → polls for completion
4. **Email Digest:** Daily at 7 AM IST (after the 05:30 IST poll) → queries yesterday's cs.AI papers → sends via Resend

## Testing

```bash
make test          # All tests
make test-unit     # Unit tests only (exclude remote/live/mlx markers)
make test-fast     # Stop on first failure (-x flag)
make lint          # Syntax check critical files
make check         # Verify imports work
```

## Configuration

All config via environment variables, loaded in `config.py` (Pydantic BaseSettings). Key vars:
- `DATABASE_URL` — PostgreSQL connection string
- `GEMINI_API_KEY` / `GOOGLE_API_KEY` — Google API credentials
- `AI_PROVIDER` — "gemini" or "local" (LiteLLM gateway)
- `PDF_SAVE_DIR` — Local PDF storage path
- `RESEND_API_KEY` — Email service
- `LITELLM_BASE_URL` — LiteLLM gateway entry point (e.g. `http://192.168.1.32:4000/v1`)
- `LLM_EMBEDDING_MODEL` — model used for 3072D embeddings
- `LLM_CHAT_MODEL` — Primary RAG chat model and default fallback for others
- `LLM_SUMMARIZATION_MODEL` — Dedicated summarization model (falls back to `LLM_CHAT_MODEL`)
- `LLM_ENTITY_MODEL` — Dedicated entity extraction model (falls back to `LLM_CHAT_MODEL`)
- `LLM_CLASSIFICATION_MODEL` — Citation parsing and Pattern Taxonomy classification (defaults to `LLM_CHAT_MODEL`)

> [!WARNING]
> **Naming Gotcha**: `LLM_CHAT_MODEL` is the primary fallback for summarization and entity extraction. Ensure this is set to a capable model if dedicated models are not configured.
