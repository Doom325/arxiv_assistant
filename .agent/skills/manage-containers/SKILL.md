---
name: manage-containers
description: Uses the Docker MCP server to manage arxiv_assistant containers — check running services, view logs, restart containers, inspect resource usage, and troubleshoot deployment issues. Use when the user asks about container status, Docker problems, deployment health, service logs, or resource usage.
---

# Manage Containers

Use the **docker** MCP tool to manage the arxiv_assistant Docker Compose stack directly.

## arxiv_assistant Container Architecture

| Container | Image Base | Role | Port |
|-----------|-----------|------|------|
| `arxiv_assistant-backend-1` | python:3.12-slim | FastAPI API server | 8000 |
| `arxiv_assistant-worker-1` | python:3.12-slim | Background processing worker | — |
| `arxiv_assistant-frontend-1` | node:20 | Next.js web UI | 3000 |
| `arxiv_assistant-db-1` | pgvector/pgvector:pg16 | PostgreSQL + pgvector | 5434 |

## Common Operations

### Check Service Health

List all containers and their status. Healthy state means:
- All 4 containers running
- Backend responds on :8000
- Frontend responds on :3000
- Database accepts connections on :5434

### View Logs

Check container logs when diagnosing issues:
- **Backend errors:** API failures, router exceptions, startup issues
- **Worker errors:** PDF download failures, embedding errors, LLM timeouts, GLiNER OOM
- **Frontend errors:** Build failures, API proxy errors, SSR issues
- **Database errors:** Connection pool exhaustion, missing extensions, disk space

When reading logs:
- Worker logs are the most common source of issues (PDF/LLM pipeline)
- Backend logs show API request errors and scheduler output
- Look for Python tracebacks, "ERROR" level messages, and connection refused errors

### Restart Services

When to restart each service:
- **Backend:** After changing Python code (if not using --reload), after env var changes
- **Worker:** After changing worker pipeline code, after model changes
- **Frontend:** After changing next.config.ts or environment variables
- **Database:** Almost never — only after PostgreSQL config changes

### Resource Monitoring

Check container resource usage. Key thresholds for arxiv_assistant:
- **Worker memory:** Can spike during GLiNER entity extraction or large PDF processing. If OOM, increase container memory limit.
- **Database memory:** pgvector operations on 3072D embeddings are memory-intensive. Monitor during similarity searches.
- **Backend CPU:** Should be low except during concurrent API requests.

## Docker Compose Files

The project uses layered compose files:
- `docker-compose.yml` — Base configuration (always used)
- `docker-compose.framework.yml` — Framework Desktop overlay (Ollama on host, external drive mount)
- `docker-compose.khadas-ollama.yml` — Khadas with Ollama
- `docker-compose.test.yml` — Staging environment (different ports/DB)

## Troubleshooting Playbook

### Worker Not Processing Papers
1. Check if worker container is running
2. Check worker logs for errors (LLM timeouts, PDF failures)
3. Verify database connectivity (worker → db)
4. Verify Ollama is reachable (if AI_PROVIDER=local): check network_mode or host access

### Backend API Errors
1. Check backend logs for tracebacks
2. Verify database pool is not exhausted (pool size 20, overflow 30)
3. Check if scheduler is running (paper poll every 15 min)

### Frontend Not Loading
1. Check frontend container is running and built successfully
2. Check API proxy — frontend proxies `/api/*` to `http://backend:8000`
3. Verify `BACKEND_URL` or `INTERNAL_API_URL` environment variable

### Database Connection Issues
1. Verify db container is running on port 5434
2. Check if pgvector extension is installed: `SELECT * FROM pg_extension WHERE extname = 'vector';`
3. Check connection pool exhaustion in backend logs

## Guidelines

- Always check container status before attempting restarts.
- When restarting, prefer restarting individual containers over the entire stack.
- Never force-remove database containers without confirming data is backed up.
- Log output can be verbose — use tail/limit options to get recent entries.
