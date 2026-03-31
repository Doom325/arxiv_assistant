# Walkthrough: Fixing the ArXiv Assistant Dashboard

## Problem
The dashboard at `http://192.168.1.49:3000` showed **"No papers found"** despite having ~79,000 papers in the database. The browser console showed `500 Internal Server Error` on every API call.

## Root Causes Found

### 1. Backend: `ResponseValidationError` (Pydantic Schema)
Some papers had citation `url` fields stored as **lists** (`["url1", "url2"]`) instead of strings. The strict `Citation` schema rejected them, crashing the entire response.

**Fix:** Relaxed `Citation` and `PaperResponse` fields to `Any` in [schemas.py](file:///Users/sumanthgottipati/git/arxiv_assistant/backend/schemas.py).

### 2. Frontend: Next.js `rewrites()` Broken in Docker (THE REAL CULPRIT)
The Next.js `rewrites()` in `next.config.ts` was resolving `process.env.BACKEND_URL` to `localhost:8000` inside the container — but `localhost` in a Docker container refers to the container itself, not the backend service. Every proxy request hit a dead end:

```
Failed to proxy http://localhost:8000/papers — ECONNREFUSED
```

**Fix:** Removed `rewrites()` entirely and created an explicit API route handler at [route.ts](file:///Users/sumanthgottipati/git/arxiv_assistant/frontend/app/api/%5B...path%5D/route.ts) that correctly proxies to `http://backend:8000` via Docker networking.

## Files Changed

| File | Change |
|------|--------|
| [schemas.py](file:///Users/sumanthgottipati/git/arxiv_assistant/backend/schemas.py) | Relaxed `Citation` and `PaperResponse` fields to `Any` |
| [main.py](file:///Users/sumanthgottipati/git/arxiv_assistant/backend/main.py) | Added `Request`/`Response` imports, `ResponseValidationError` handler |
| [next.config.ts](file:///Users/sumanthgottipati/git/arxiv_assistant/frontend/next.config.ts) | Removed broken `rewrites()` |
| [route.ts](file:///Users/sumanthgottipati/git/arxiv_assistant/frontend/app/api/%5B...path%5D/route.ts) | **New** — Catch-all API proxy (GET/POST/DELETE) |
| [deploy.sh](file:///Users/sumanthgottipati/git/arxiv_assistant/deploy.sh) | Added `--force-recreate`, `RSYNC_RSH`, internal schema verification |

## Verification

```
$ curl -s -o /dev/null -w "%{http_code}" "http://192.168.1.49:3000/api/papers/?skip=0&limit=5"
200  ✅

$ curl -s -o /dev/null -w "%{http_code}" "http://192.168.1.49:8000/papers/?skip=0&limit=1000"
200  ✅ (1.7MB, 1000 papers)
```

User confirmed: **"I can confirm that the papers are showing now!!"** ✅

## Key Lesson
> Next.js `standalone` output mode bakes `rewrites()` destinations at **build time**. Environment variables injected via `docker-compose.yml` are runtime-only and won't be available in the built server. Use explicit API route handlers (`app/api/[...path]/route.ts`) for reliable Docker-to-Docker proxying.
