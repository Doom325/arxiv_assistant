# arxiv_assistant

> **IMPORTANT:** You MUST also follow all rules in `AGENTS.md` — especially the **Reviewer Agent Integration** section. Never push directly to `main`. Always use feature branches + PRs and apply the `reviewer:pending` label.

AI-powered arXiv paper discovery and analysis platform. Automatically ingests papers, generates embeddings, extracts entities, builds citation graphs, classifies agentic patterns, and provides semantic search + RAG chat over a research paper library.

## Architecture

Modular monolith deployed via Docker Compose (4 containers). Supports two deployment targets:
- **Framework Desktop** (AMD Ryzen AI Max+ 395, 128GB, x86_64) — primary, with local LLM processing via Ollama
- **Khadas Edge 2** (ARM64) — original deployment target

- **backend/** — FastAPI (Python 3.12) API server on port 8000 (9 routers, 10 services, 12 ORM models)
- **worker** — `production_worker.py` running in a separate container (PDF processing, 3072D embeddings, entity extraction, citation parsing, pattern classification)
- **frontend/** — Next.js 16 (React 19, TypeScript, Tailwind v4) on port 3000 — dark-themed with space background, glassmorphism, Framer Motion, Three.js
- **db** — PostgreSQL 16 + pgvector (`pgvector/pgvector:pg16`) on port 5434
- **chrome_extension/** — Manifest V3 browser extension for saving arXiv papers to NotebookLM
- **docs/** — Design docs, feature plans, architecture notes (15 planning/design documents)

### Background Processes

- `production_worker.py` — Continuously polls for unprocessed papers (batch of 5, last 20 days). Pipeline: download PDF → extract text/sections → generate 3072D embedding → extract entities (GLiNER) → parse citations (LLM) → resolve citations → classify patterns (V6 CoT taxonomy)
- `scheduler.py` — APScheduler started in FastAPI lifespan: paper poll (every 15 min, 50 papers/category), email digest (6 AM IST), batch summarization (11 PM IST)
- `batch_embed_manager.py` — Bulk historical embedding processing via Gemini Batch API

## External Services

- **Google Gemini API** — embeddings (768D, MRL-supported via gemini-embedding-001), search queries
- **Ollama** — local LLM inference on Framework Desktop (Gemma 3 27B for summarization/chat/entities, Gemma 3 12B for classification/citations)
- **arXiv API** — paper metadata and PDF downloads (3s rate limit)
- **Resend** — email digest delivery (HTML + text)
- **Google Drive** — OAuth2 bookmark export (resumable uploads)
- **MLX** — Apple Silicon local dev (via `mac_worker.py`)
- **GLiNER** — entity extraction fallback (Software, Dataset, Model, Loss Function, Metric, Task, Organization, Hardware)

### Provider Architecture

Split provider design — `llm_service` handles LLM tasks, `embedding_service` handles embeddings independently:
- `AI_PROVIDER` — controls summarization, classification, citations, chat, entity extraction ("gemini" or "local")
- `EMBEDDING_PROVIDER` — controls embeddings only (defaults to AI_PROVIDER, set to "gemini" to keep Gemini embeddings while using local LLMs)
- `ENTITY_EXTRACTION_PROVIDER` — "gliner" (default) or "llm" for LLM-based extraction
- `OLLAMA_CHAT_MODEL` — Gemma 3 27B (summarization, chat, entity extraction)
- `OLLAMA_CLASSIFICATION_MODEL` — Gemma 3 12B (classification, citation parsing)

## Key Features

- **Hybrid Search** — Semantic (pgvector cosine/L2) + keyword (PostgreSQL full-text with GIN index) merged via Reciprocal Rank Fusion (RRF). Metadata filters: `category:`, `after:`, `before:`, `author:`, `entity:`
- **RAG Chat** — Conversational interface over paper library
- **Citation Graph** — Directed citation links with arXiv ID resolution to local papers, top-cited analytics
- **Agentic Pattern Classification** — V6 CoT taxonomy classifying papers by agentic patterns
- **Analytics Dashboard** — Papers-over-time (day/week/month), category distribution, summary stats
- **User Library** — Bookmarks with named lists, Google Drive export
- **Daily Digest** — Scheduled email with yesterday's cs.AI papers
- **Command Palette (Cmd+K)** — Global search and navigation
- **Keyboard Navigation** — `j/k` nav, `space` quick-peek, `b` bookmark, `g+letter` chord nav, `?` shortcuts

## Environment Setup

```bash
cp .env.example .env              # Root .env (DB credentials, general config)
cp backend/.env.example backend/.env  # Backend .env (API keys)
```

Key variables: `GEMINI_API_KEY`, `GOOGLE_API_KEY`, `RESEND_API_KEY`, `DATABASE_URL`, `AI_PROVIDER` (gemini|local), `PDF_SAVE_DIR`, `OLLAMA_BASE_URL`.

## Development

```bash
# Khadas deployment
docker compose up              # Start all 4 services (backend, worker, frontend, db)

# Framework Desktop deployment (local LLM + Gemini embeddings)
# Prerequisites: Ollama running on host with gemma3:27b and gemma3:12b pulled
EXTERNAL_DRIVE_PATH=/mnt/external GEMINI_API_KEY=xxx docker compose \
  -f docker-compose.yml -f docker-compose.framework.yml up

docker compose up -d db        # Database only (for local dev)
```

Backend local dev: `cd backend && pip install -r requirements.txt && uvicorn main:app --reload --port 8000`
Frontend local dev: `cd frontend && npm install && npm run dev`

## Testing

```bash
cd backend
make test          # All tests (pytest, 34 test files)
make test-unit     # Unit tests only (excludes remote/live/mlx markers)
make test-fast     # Stop on first failure
make lint          # Syntax check
make check         # Import verification
```

## Deployment

```bash
./deploy.sh          # Full deploy to Khadas Edge 2 via rsync + Docker Compose (192.168.1.49)
./deploy-staging.sh  # Staging deployment to ~/arxiv_assistant_staging/ (separate containers/ports/DB)
```

## Git Conventions

Conventional commits: `fix:`, `feat:`, `refactor:`, `chore:`, `test:`, `config:`, `security:`

## Directory Layout

```
arxiv_assistant/
├── backend/                    # FastAPI API, services, models, workers
│   ├── routers/                #   9 API routers (papers, search, library, citations, patterns, analytics, ...)
│   ├── services/               #   10 services (llm, arxiv, pdf, email, gdrive, citation, nlp, ...)
│   ├── models/                 #   12 SQLAlchemy ORM models
│   ├── core/                   #   Shared utilities (pdf_utils, text_utils)
│   ├── scripts/                #   Backfill, repair, diagnostics, benchmarks
│   └── tests/                  #   34 pytest test files
├── frontend/                   # Next.js web UI
│   ├── app/                    #   8 routes (dashboard, paper, research, chat, bookmarks, patterns, analysis, settings)
│   ├── components/             #   12 core + dashboard/ + animations/ + parallax/ sub-components
│   └── lib/                    #   API client, category colors, keyboard nav hook
├── chrome_extension/           # Manifest V3 browser extension (arXiv → NotebookLM)
├── docs/                       # 15 design & planning documents
├── docker-compose.yml          # Base orchestration (4 containers)
├── docker-compose.framework.yml # Framework Desktop override (local LLM, external drive)
├── docker-compose.test.yml     # Staging orchestration
├── docker-compose-local-backfill.yml
├── deploy.sh                   # Khadas production deployment
├── deploy-staging.sh           # Khadas staging deployment
└── .env.example                # Environment template
```
