# Query Embedding Cache — Design Proposal

## Problem

Every search, chat, and timeline request generates a fresh embedding via a synchronous Gemini API call (~100-500ms). There is zero caching — if a user searches "large language models" ten times, that's ten API calls returning identical vectors. Three endpoints hit this path:

| Endpoint | Route | Task Type |
|----------|-------|-----------|
| Search | `POST /papers/search` | `retrieval_query` |
| Chat | `POST /papers/chat` | `retrieval_document` (bug — should be `retrieval_query`) |
| Timeline | `GET /timeline/topic?q=...` | `retrieval_query` |

**Impact:**
- **Latency**: 100-500ms added to every request, synchronous/blocking
- **Cost**: Each call is billed ($0.10-0.20/M tokens); popular queries multiply cost
- **Rate limits**: Tier 1 allows limited RPM; concurrent users can exhaust quota
- **Reliability**: If Gemini API is slow or down, all search/chat/timeline fails

## Options Analyzed

### Option A: In-Memory LRU Cache (functools)

**How it works:** Python `@lru_cache` or a dict with TTL on `generate_embedding()`, keyed by `(text, task_type, dimensions)`.

```python
from functools import lru_cache

@lru_cache(maxsize=2048)
def generate_embedding_cached(text: str, task_type: str, dims: int) -> tuple:
    return tuple(llm_service.generate_embedding(text, task_type, dims))
```

| Pros | Cons |
|------|------|
| Zero infrastructure — pure Python | Lost on process restart |
| Sub-microsecond cache hits | Not shared across workers/containers |
| No dependencies | Memory grows unbounded without eviction tuning |
| Trivial to implement (~10 lines) | No persistence across deploys |

**Best for:** Single-process deployments (which Khadas is — one uvicorn worker).

### Option B: PostgreSQL Table (Query Embedding Store)

**How it works:** A new `query_embeddings` table storing `(query_hash, query_text, task_type, embedding, created_at)`. Check the table before calling Gemini; insert after generating.

```sql
CREATE TABLE query_embeddings (
    id SERIAL PRIMARY KEY,
    query_hash VARCHAR(64) UNIQUE NOT NULL,  -- SHA256 of normalized query + task_type
    query_text TEXT NOT NULL,
    task_type VARCHAR(32) NOT NULL,
    embedding vector(768) NOT NULL,
    hit_count INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW(),
    last_used_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_query_emb_hash ON query_embeddings(query_hash);
```

| Pros | Cons |
|------|------|
| Survives restarts and deploys | Extra DB round-trip per query (~5-10ms) |
| Shared across all workers | Schema migration needed |
| Queryable — analytics on popular queries | Stale embeddings if model changes |
| Natural TTL via `created_at` cleanup | Slightly more complex implementation |
| Can pre-warm with known popular queries | |

**Best for:** Persistent, observable cache with analytics potential.

### Option C: Redis / Valkey

**How it works:** Embedding vectors stored in Redis with TTL, keyed by query hash.

| Pros | Cons |
|------|------|
| Sub-millisecond lookups | New infrastructure dependency |
| Built-in TTL expiry | Another container on memory-constrained Khadas |
| Shared across workers | Serialization overhead for 768-float vectors |
| Industry standard | Overkill for single-user/low-traffic system |

**Best for:** High-traffic, multi-worker deployments. Overkill for Khadas.

### Option D: Hybrid — In-Memory + PostgreSQL

**How it works:** Two-tier cache. Check in-memory LRU first (hot queries), then PostgreSQL (warm queries), then Gemini API (cold queries). Write-through: new embeddings go to both layers.

```
Request → LRU cache (hit?) → PostgreSQL (hit?) → Gemini API
                                    ↓ write-back
                              LRU + PostgreSQL
```

| Pros | Cons |
|------|------|
| Fastest possible hot path | Two cache layers to maintain |
| Persistent across restarts | Invalidation across layers |
| Observable (DB analytics) | Marginal benefit if traffic is low |
| No new infrastructure | More code complexity |

**Best for:** When you want the speed of in-memory with the durability of PostgreSQL.

## Comparison Matrix

| Criteria | A: LRU | B: PostgreSQL | C: Redis | D: Hybrid |
|----------|--------|---------------|----------|-----------|
| **Latency (cache hit)** | <1μs | ~5ms | ~1ms | <1μs (hot) / ~5ms (warm) |
| **Survives restart** | No | Yes | Yes (with persistence) | Yes |
| **New infrastructure** | None | None (existing DB) | Redis container | None |
| **Implementation effort** | ~10 lines | ~60 lines + migration | ~80 lines + Docker | ~80 lines + migration |
| **Observability** | None | Full (SQL queries) | Limited | Full |
| **Memory on Khadas** | ~12MB for 2K queries | DB handles it | ~50MB Redis container | ~12MB + DB |
| **Multi-worker safe** | No | Yes | Yes | Yes |
| **Model change handling** | Clear on deploy | Delete by `created_at` | TTL expiry | Both |

## Recommendation: Option D — Hybrid (In-Memory LRU + PostgreSQL)

**Why both layers:**

- **LRU (hot layer):** Eliminates DB round-trips for repeated queries within a session — common when a user searches, refines, then builds a timeline on the same topic. ~10 extra lines of code, no downside.
- **PostgreSQL (warm layer):** Survives restarts and deploys. Gives observability, analytics, and pre-warming capability. No new infrastructure — uses existing DB.

Together they cover both use cases: rapid-fire same-session queries (LRU) and returning-user / cross-deploy persistence (PostgreSQL). On Khadas where DB connections and API calls are both relatively expensive, avoiding unnecessary work at either layer matters.

**Additional reasons:**

1. **No new infrastructure** — LRU is pure Python, PostgreSQL is already running
2. **Observability** — `hit_count` and `query_text` columns give free "popular searches" analytics
3. **Model migration friendly** — `DELETE FROM query_embeddings WHERE model_name != 'current-model'`
4. **Pre-warming** — batch-insert embeddings for known popular queries before users hit the system
5. **Negligible complexity** — LRU is a decorator, PostgreSQL is a table + lookup; together ~80 lines

## Proposed Schema

```sql
CREATE TABLE query_embeddings (
    id SERIAL PRIMARY KEY,
    query_hash VARCHAR(64) UNIQUE NOT NULL,
    query_text TEXT NOT NULL,
    task_type VARCHAR(32) NOT NULL DEFAULT 'retrieval_query',
    embedding vector(768) NOT NULL,
    model_name VARCHAR(64) NOT NULL DEFAULT 'gemini-embedding-2-preview',
    hit_count INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW(),
    last_used_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_query_emb_hash ON query_embeddings(query_hash);
CREATE INDEX idx_query_emb_last_used ON query_embeddings(last_used_at);
```

**Cache key:** `SHA256(normalize(query_text) + task_type + model_name)`

**Normalization:** lowercase, strip whitespace, collapse multiple spaces.

## Proposed Implementation

### 1. New model: `models/query_cache.py`

```python
class QueryEmbedding(Base):
    __tablename__ = "query_embeddings"
    id, query_hash, query_text, task_type, embedding, model_name, hit_count, created_at, last_used_at
```

### 2. Cache-aware wrapper in `llm_service.py`

```python
def get_or_generate_query_embedding(query: str, task_type: str, db: Session) -> list[float]:
    normalized = normalize_query(query)
    cache_key = sha256(f"{normalized}|{task_type}|{model_name}")

    # Check cache
    cached = db.query(QueryEmbedding).filter_by(query_hash=cache_key).first()
    if cached:
        cached.hit_count += 1
        cached.last_used_at = now()
        db.commit()
        return cached.embedding

    # Generate fresh
    embedding = llm_service.generate_embedding(normalized, task_type=task_type)

    # Store in cache
    db.add(QueryEmbedding(query_hash=cache_key, query_text=normalized, ...))
    db.commit()
    return embedding
```

### 3. Update callers (3 locations)

- `routers/search.py` line 83: Replace `llm_service.generate_embedding(...)` with `get_or_generate_query_embedding(..., db)`
- `routers/search.py` line 191 (chat): Same replacement + fix task_type bug
- `services/timeline_service.py` line 594: Same replacement

### 4. Maintenance: periodic cleanup

```sql
-- Remove queries not used in 30 days
DELETE FROM query_embeddings WHERE last_used_at < NOW() - INTERVAL '30 days';

-- Remove stale model embeddings after model switch
DELETE FROM query_embeddings WHERE model_name != 'gemini-embedding-2-preview';
```

Can add to the existing scheduler as a weekly job.

## Files to Modify

| File | Change |
|------|--------|
| `backend/models/query_cache.py` | New file — QueryEmbedding ORM model |
| `backend/models/__init__.py` | Export QueryEmbedding |
| `backend/services/llm_service.py` | Add `get_or_generate_query_embedding()` wrapper |
| `backend/routers/search.py` | Use cached wrapper in search + chat (+ fix chat task_type bug) |
| `backend/services/timeline_service.py` | Use cached wrapper in topic search |
| `backend/scheduler.py` | Add weekly cache cleanup job |
| Migration script | Create `query_embeddings` table |

## Additional Benefits

- **Popular queries dashboard** — `SELECT query_text, hit_count FROM query_embeddings ORDER BY hit_count DESC LIMIT 20`
- **Search analytics** — track what users search for over time
- **Pre-warming** — insert embeddings for known topics before users hit the system
- **A/B testing** — compare embedding models by storing model_name per cache entry
