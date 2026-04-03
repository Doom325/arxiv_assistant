# Docker & Deployment Rules

## Docker Compose Configurations

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Base: 4 services (backend, worker, frontend, db) |
| `docker-compose.framework.yml` | Framework Desktop override (local Ollama, external drive) |
| `docker-compose.khadas-ollama.yml` | Khadas with Ollama support |
| `docker-compose.test.yml` | Staging (separate ports/DB) |
| `docker-compose-local-backfill.yml` | Local backfill processing |

## Container Details

- **backend**: Python 3.12-slim, exposes port 8000, depends on db.
- **worker**: Same image as backend, runs `production_worker.py`, depends on db.
- **frontend**: Node 20 multi-stage build, standalone output, port 3000.
- **db**: `pgvector/pgvector:pg16`, port 5434, persistent volume.

## Deployment Targets

### Framework Desktop (Primary)
```bash
EXTERNAL_DRIVE_PATH=/mnt/external GEMINI_API_KEY=xxx docker compose \
  -f docker-compose.yml -f docker-compose.framework.yml up
```
- Requires Ollama running on host with `gemma3:27b` and `gemma3:12b` pulled.
- External drive mounted for PDF storage.
- Ollama accessed via host network (`host.docker.internal` or host IP).

### Khadas Edge 2 (ARM64)
```bash
./deploy.sh          # Production: rsync + Docker Compose to 192.168.1.49
./deploy-staging.sh  # Staging: ~/arxiv_assistant_staging/ with separate ports
```
- Deploy scripts use rsync for file transfer.
- Always verify network connectivity before deploying.

## Dockerfile Changes

- Backend Dockerfile: keep `python:3.12-slim` base. Install system deps for PyMuPDF, psycopg2.
- Frontend Dockerfile: multi-stage build (deps → build → runner). Standalone output mode.
- When adding Python dependencies, update `requirements.txt` and rebuild.
- When adding npm packages, update `package.json`/`package-lock.json` and rebuild.

## Environment Variables

- Passed via `.env` file (Docker Compose `env_file` directive) or inline.
- Never bake secrets into Docker images.
- The `BACKEND_URL` / `INTERNAL_API_URL` frontend env var controls the API proxy target.
