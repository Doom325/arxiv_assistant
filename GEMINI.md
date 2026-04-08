# arxiv_assistant — Antigravity Project Context

> **IMPORTANT:** You MUST also follow all rules in `AGENTS.md` — especially the **Reviewer Agent Integration** section. Never push directly to `main`. Always use feature branches + PRs and apply the `reviewer:pending` label.

AI-powered arXiv paper discovery and analysis platform. Automatically ingests papers, generates embeddings, extracts entities, builds citation graphs, classifies agentic patterns, and provides semantic search + RAG chat over a research paper library.

## Architecture

Modular monolith deployed via Docker Compose (4 containers):

| Service | Technology | Port | Entry Point |
|---------|-----------|------|-------------|
| **Backend API** | FastAPI, Python 3.12 | 8000 | `backend/main.py` |
| **Worker** | Continuous background process | — | `backend/production_worker.py` |
| **Frontend** | Next.js 16, React 19, TypeScript | 3000 | `frontend/app/layout.tsx` |
| **Database** | PostgreSQL 16 + pgvector | 5434 | `pgvector/pgvector:pg16` |

Deployment targets:
- **Framework Desktop** (AMD Ryzen AI Max+ 395, 128GB, x86_64) — primary, local LLM via Ollama
- **Khadas Edge 2** (ARM64) — original deployment target

### Framework Desktop Deployment Constraints

The Framework Desktop runs **Fedora 43 with SELinux enforcing**. These constraints are MANDATORY for any Docker/Podman configuration targeting this machine:

- **SELinux `:z` on ALL bind-mount volumes** — every volume mount MUST use the `:z` suffix (e.g. `./config.yml:/etc/config.yml:z`). Without it, containers get `Permission denied` when reading mounted files. This applies to config files, scripts, provisioning directories — everything.
- **Port 9090 is reserved (Cockpit)** — Fedora's web admin panel (Cockpit) runs on port 9090. NEVER map container ports to 9090. Use 9091 for Prometheus or any other service that defaults to 9090.
- **Podman (rootless), not Docker** — the host uses `podman compose` via the docker-compose CLI plugin. Rootless containers run under user `gsumanth`. Container networking uses Podman bridge networks.
- **Ollama is a systemd service on the host** — NOT a container. Runs at `0.0.0.0:11434` with Vulkan backend (`OLLAMA_LLM_LIBRARY=vulkan`), flash attention, and debug logging. Configured via `/etc/systemd/system/ollama.service` and override at `/etc/systemd/system/ollama.service.d/override.conf`. Use `sudo systemctl edit ollama` to modify, `sudo systemctl restart ollama` to apply.
- **External drive required** — PostgreSQL data and PDF storage live on an external drive. Set `EXTERNAL_DRIVE_PATH` env var when running compose.
- **Python venv for bare-metal scripts** — `backend/venv/` contains all Python dependencies. Run scripts with `PYTHONPATH=. venv/bin/python scripts/foo.py` from the `backend/` directory.
- **Standalone monitoring stack** — a separate `~/ollama-monitoring/docker-compose.yml` stack may be running with containers `ollama-mitmproxy`, `ollama-prometheus`, `ollama-grafana`, `ollama-metrics`. These occupy ports 3000, 8081, 8082, 8434, 9091. **Stop it before starting arxiv_assistant monitoring services** to avoid port conflicts: `cd ~/ollama-monitoring && podman compose down`.

## Tech Stack

### Backend
- FastAPI + uvicorn (async), SQLAlchemy ORM (pool 20/overflow 30), PostgreSQL 16 + pgvector (3072D embeddings)
- LLM: Gemini API (embeddings, summarization, chat) + Ollama (Gemma 3 27B chat, Gemma 3 12B classification)
- Entity extraction: GLiNER (8 types), PDF: PyPDF + PyMuPDF, Email: Resend API, Scheduling: APScheduler
- Provider abstraction: `AI_PROVIDER`, `EMBEDDING_PROVIDER`, `ENTITY_EXTRACTION_PROVIDER` are independent

### Frontend
- Next.js 16 App Router (React Compiler enabled, standalone output), Tailwind CSS v4
- Framer Motion, Three.js (@react-three/fiber), Recharts, cmdk, KaTeX, react-markdown
- API proxy: `app/api/[...path]/route.ts` → backend at `http://backend:8000`

## Key Patterns

- **Hybrid Search:** pgvector cosine + PostgreSQL full-text (GIN index) merged via Reciprocal Rank Fusion (RRF)
- **Provider Abstraction:** `LLMProvider` base class for Gemini/Ollama/MLX swapping
- **Service Singletons:** Lazy-loaded globals (`llm_service`, `arxiv_service`, `email_service`)
- **DB Sessions:** FastAPI dependency injection via `database.get_db`
- **Worker Pipeline:** Poll → PDF download → text extraction → 3072D embedding → GLiNER entities → LLM citation parsing → pattern classification (V6 CoT)

## API Routers (backend/routers/)

| Router | Prefix | Purpose |
|--------|--------|---------|
| `papers.py` | `/papers` | CRUD, list, similarity search, manual add |
| `search.py` | `/papers` | Hybrid search + RRF, metadata filters, RAG chat |
| `library.py` | `/library` | Bookmarks, list management |
| `citations.py` | `/citations` | Citation analytics, most-cited |
| `patterns.py` | `/patterns` | Agentic pattern taxonomy & results |
| `analytics.py` | `/analytics` | Dashboard stats, papers-over-time |
| `batch.py` | `/batch` | Batch job management |
| `users.py` | `/users` | User config (keywords, categories) |
| `integrations.py` | (multiple) | Summarization, email, Google Drive |

## Services (backend/services/)

`llm_service.py` (provider abstraction), `arxiv_service.py` (arXiv API, 3s rate limit), `pdf_service.py` (extraction pipeline), `citation_service.py` (graph building), `email_service.py` (Resend), `nlp_service.py` (GLiNER), `batch_service.py` (Gemini Batch API), `summarization_service.py`, `gdrive.py` (OAuth2), `prompts.py` (centralized prompts)

## Models (backend/models/)

`Paper` + `PaperEmbedding` (pgvector 3072D), `User` + `UserConfig` + `UserLibrary`, `JobLog` + `SummarizationMetric` + `BatchQueue`, `CitationLink` (directed graph), `PromptTemplate` + `PatternExperimentResult`

## Development

```bash
# Local dev
docker compose up -d db                    # Database only (port 5434)
cd backend && uvicorn main:app --reload     # API on :8000
cd frontend && npm run dev                  # UI on :3000

# Framework Desktop (full stack with local LLM)
EXTERNAL_DRIVE_PATH=/mnt/external GEMINI_API_KEY=xxx docker compose \
  -f docker-compose.yml -f docker-compose.framework.yml up

# Testing
cd backend && make test-unit    # Unit tests (excludes remote/live/mlx)
cd backend && make test-fast    # Stop on first failure
cd backend && make lint         # Syntax check
```

## Configuration

All via env vars in `backend/config.py` (Pydantic BaseSettings):
- `DATABASE_URL` — PostgreSQL (default: localhost:5434)
- `GEMINI_API_KEY` / `GOOGLE_API_KEY`
- `AI_PROVIDER` — "gemini" or "local" (Ollama)
- `EMBEDDING_PROVIDER` — override for embeddings only
- `OLLAMA_BASE_URL` — Ollama API entry point (e.g. `http://localhost:11434/v1`)
- `OLLAMA_EMBEDDING_MODEL` — model used for 3072D embeddings (e.g. `nomic-embed-text`)
- `OLLAMA_CHAT_MODEL` — Primary RAG chat model and default fallback for others
- `OLLAMA_SUMMARIZATION_MODEL` — Dedicated summarization model (falls back to `OLLAMA_CHAT_MODEL`)
- `OLLAMA_ENTITY_MODEL` — Dedicated entity extraction model (falls back to `OLLAMA_CHAT_MODEL`)
- `OLLAMA_CLASSIFICATION_MODEL` — Citation parsing and Pattern Taxonomy classification (defaults to `OLLAMA_CHAT_MODEL`)
- `PDF_SAVE_DIR`, `RESEND_API_KEY`, `ENTITY_EXTRACTION_PROVIDER`

### OLLAMA Model Mapping

| Env Var | Provider Attribute | Implementation Path |
|---------|--------------------|---------------------|
| `OLLAMA_CHAT_MODEL` | `self.chat_model` | `OllamaProvider.chat` |
| `OLLAMA_SUMMARIZATION_MODEL` | `self.summarization_model` | `OllamaProvider.summarize_text[_with_metrics]` |
| `OLLAMA_ENTITY_MODEL` | `self.entity_model` | `OllamaProvider.extract_entities` |
| `OLLAMA_CLASSIFICATION_MODEL` | `self.classification_model` | `OllamaProvider.classify_paper`, `parse_citations` |

> [!WARNING]
> **Naming Gotcha**: `OLLAMA_CHAT_MODEL` is the primary fallback for summarization and entity extraction. Ensure this is set to a capable model (e.g., Gemma 3 27B) if dedicated models are not configured.

## Conventions

- Conventional commits: `feat:`, `fix:`, `refactor:`, `chore:`, `test:`, `config:`, `security:`
- Backend: Python 3.12, PEP 484 type hints, async FastAPI endpoints, SQLAlchemy ORM
- Frontend: TypeScript strict, React Server Components by default, `"use client"` only when needed
- Testing: pytest with markers (`remote`, `live`, `mlx`), conftest uses SQLite in-memory + mocked pgvector
- All new routers must be registered in `main.py`, all new models exported from `models/__init__.py`
