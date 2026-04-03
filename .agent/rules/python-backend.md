# Python Backend Standards

These rules apply when working on files in `backend/`.

## FastAPI Conventions

- All route handlers must be `async def`.
- Use Pydantic models for request/response schemas (defined in `schemas.py` or co-located).
- Use `Depends(get_db)` for database sessions — never create `SessionLocal()` manually in routers.
- Register new routers in `main.py` with `app.include_router()`.
- Return structured responses: `{"data": ...}` for success, raise `HTTPException` for errors.

## Service Layer

- Business logic lives in `services/`, not in routers. Routers are thin wrappers.
- Follow the singleton pattern: create a module-level instance (e.g., `email_service = EmailService()`).
- All services that call external APIs must handle exceptions and log errors.
- LLM calls go through `services/llm_service.py` — never call Gemini/Ollama APIs directly.

## Provider Architecture

- `AI_PROVIDER` controls LLM tasks (summarization, chat, classification, entity extraction).
- `EMBEDDING_PROVIDER` controls embeddings independently (can use Gemini embeddings with local LLMs).
- `ENTITY_EXTRACTION_PROVIDER` controls entity extraction ("gliner" or "llm").
- When adding a new LLM capability, extend both `GeminiProvider` and `OllamaProvider` in `llm_service.py`.

## Models & Database

- ORM models go in `backend/models/` (one file per domain: paper, user, jobs, citation, pattern).
- Export all models from `models/__init__.py`.
- Use Alembic-style migration scripts (`migrate_*.py`) for schema changes.
- pgvector columns use 3072 dimensions. Embedding operations use cosine distance.
- Use the existing `text_utils.py` for sanitization (null bytes, UTF-16 surrogates) before DB insertion.

## Worker Pipeline

- The worker (`production_worker.py`) processes papers in batches of 5, polling every 15 seconds.
- Pipeline order: PDF download → text extraction → embedding → entity extraction → citation parsing → pattern classification.
- Never add synchronous PDF processing to API route handlers.
- Use `JobLog` model to audit all worker operations.

## Python Style

- PEP 484 type annotations on all function signatures.
- Use `pathlib.Path` over `os.path`.
- Use `ruff` for linting/formatting.
- Prefer `async/await` for I/O-bound operations.
- Never use mutable default arguments.
- Docstrings in Google format for public functions and classes.
