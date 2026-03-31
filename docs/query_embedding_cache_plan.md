# Query Embedding Cache — Implementation Plan

> **Design doc:** `docs/query_embedding_cache_proposal.md`
> **Review notes:** `docs/query_embedding_cache_review.md`
> **Approach:** Option D — Hybrid (In-Memory LRU + PostgreSQL)

---

## Design Invariants

- **Query embeddings are corpus-independent.** The vector for "transformer attention" is always the same regardless of how many papers exist. New paper ingestion does NOT invalidate the cache. The only reasons to invalidate: (1) model change, (2) task_type change.
- **Never cache invalid embeddings.** If Gemini returns `[]` or a wrong-dimension vector, it must NOT be written to either cache layer. `generate_embedding()` returns `[]` on failure — this is the primary poisoning risk.
- **LRU is per-process by design.** PostgreSQL is the shared durable layer. On Khadas (single uvicorn worker) this is a non-issue; document it for future multi-worker deployments.

---

## Phase 0: Fix Chat task_type Bug (separate commit)

- **File:** `backend/routers/search.py` line ~191
- Change `llm_service.generate_embedding(query)` to `llm_service.generate_embedding(query, task_type="retrieval_query")`
- This is a behavior change (queries were using `retrieval_document` task type, matching paper embeddings by accident). Separating it from the caching work makes it easy to validate or revert independently.
- **Commit separately before any caching work.**

---

## Phase 1: Data Layer (Model + Migration)

### 1.1 Create ORM model
- **File:** `backend/models/query_cache.py` (new)
- Create `QueryEmbedding` model:
  - `id` — Serial primary key
  - `query_hash` — VARCHAR(64), unique, indexed — `SHA256(normalized_query|task_type|model_name)`
  - `query_text` — TEXT, the normalized query string (truncated to 1000 chars)
  - `task_type` — VARCHAR(32), default `"retrieval_query"`
  - `embedding` — Vector(768), the cached embedding
  - `model_name` — VARCHAR(64), read from `llm_service.embedding_model` (not hardcoded)
  - `hit_count` — INTEGER, default 1
  - `created_at` — TIMESTAMP, default NOW()
  - `last_used_at` — TIMESTAMP, default NOW()
- Indexes: `query_hash` (unique), `last_used_at` (for cleanup)

### 1.2 Register model in `__init__.py`
- **File:** `backend/models/__init__.py`
- Add `from .query_cache import QueryEmbedding` export

### 1.3 Migration script
- **File:** `backend/migrate_query_cache.py` (new)
- `CREATE TABLE IF NOT EXISTS query_embeddings` with columns, indexes
- Idempotent — safe to re-run. Follow existing pattern in `migrate_reading_queue.py`
- Note: `Base.metadata.create_all()` in `main.py` will also auto-create, but explicit migration is preferred for production

### 1.4 Add config setting for LRU size
- **File:** `backend/config.py`
- Add `QUERY_CACHE_LRU_SIZE: int = 1024` to settings
- Configurable via environment variable

---

## Phase 2: Cache Service

### 2.1 Cache class
- **File:** `backend/services/query_embedding_cache.py` (new)
- Implement `QueryEmbeddingCache` class:
  - `_lru: OrderedDict` with max size from `settings.QUERY_CACHE_LRU_SIZE` (default 1024)
  - `_lock: threading.Lock` — **all LRU access must be under this lock** (FastAPI sync endpoints run in threadpool)
  - `_normalize(query: str) -> str` — lowercase, strip, collapse whitespace, **truncate to 1000 chars**
  - `_cache_key(query: str, task_type: str) -> str` — SHA256 of `f"{normalized}|{task_type}|{model_name}"` where model_name comes from `llm_service.embedding_model`
  - `_lru_get(key: str) -> list[float] | None` — check in-memory cache (under lock)
  - `_lru_put(key: str, embedding: list[float])` — insert with LRU eviction (under lock)
  - `_validate(embedding: list[float]) -> bool` — returns `True` only if `isinstance(embedding, list) and len(embedding) == 768`
  - `get_or_generate(query: str, task_type: str, db: Session) -> list[float]` — full flow (see 2.2)

### 2.2 Lookup flow (inside `get_or_generate`)
```
1. Normalize query (lowercase, strip, collapse spaces, truncate 1000 chars)
2. Compute cache key (SHA256)
3. Check LRU dict (under lock)
   → if hit: log "cache_hit source=lru", return immediately (NO DB write)
4. Check PostgreSQL query_embeddings table by query_hash
   → if hit:
     - Update hit_count and last_used_at ONLY if last_used_at > 24 hours old
     - Populate LRU (under lock)
     - Log "cache_hit source=postgres"
     - Return embedding
5. Call llm_service.generate_embedding(normalized, task_type=task_type)
6. Validate embedding (_validate) — if invalid, log warning and return [] WITHOUT caching
7. Write to PostgreSQL (INSERT ON CONFLICT DO NOTHING — handles race conditions)
8. Write to LRU (under lock)
9. Log "cache_miss source=gemini latency_ms=..."
10. Return embedding
```

**Key hardening details:**
- **Step 3:** LRU hits skip the DB entirely — no hit_count update, no last_used_at update. Hot queries never touch PostgreSQL.
- **Step 4:** Lazy update — only write to DB if `last_used_at` is >24h stale. Avoids write amplification on popular queries.
- **Step 6:** Never cache empty or malformed embeddings. `generate_embedding()` returns `[]` on Gemini failure — this MUST NOT be cached.
- **Step 7:** `INSERT ON CONFLICT DO NOTHING` handles concurrent requests for the same uncached query. Two threads may both call Gemini and try to insert — the second one silently no-ops. This is cheaper than a per-key lock and acceptable at our scale (duplicate Gemini call is rare, costs ~$0.000002).

### 2.3 Logging
- Every cache interaction logs: `logger.info("query_cache event=%s source=%s query_hash=%s latency_ms=%d", ...)`
- Events: `hit`, `miss`, `error`, `skip_invalid`
- Sources: `lru`, `postgres`, `gemini`

### 2.4 Singleton instance
- Create module-level `query_cache = QueryEmbeddingCache()` singleton
- Mirrors the pattern used by `llm_service`, `arxiv_service`, etc.

---

## Phase 3: Integrate with Callers

### 3.1 Search endpoint
- **File:** `backend/routers/search.py`
- **Line ~83:** Replace:
  ```python
  query_embedding = llm_service.generate_embedding(clean_query, task_type="retrieval_query")
  ```
  With:
  ```python
  query_embedding = query_cache.get_or_generate(clean_query, task_type="retrieval_query", db=db)
  ```

### 3.2 Chat endpoint
- **File:** `backend/routers/search.py`
- **Line ~191:** Replace:
  ```python
  query_embedding = llm_service.generate_embedding(query)
  ```
  With:
  ```python
  query_embedding = query_cache.get_or_generate(query, task_type="retrieval_query", db=db)
  ```
- Note: The task_type bug fix was already applied in Phase 0.

### 3.3 Timeline topic search
- **File:** `backend/services/timeline_service.py`
- **Line ~594:** Replace:
  ```python
  query_embedding = llm_service.generate_embedding(query, task_type="retrieval_query")
  ```
  With:
  ```python
  query_embedding = query_cache.get_or_generate(query, task_type="retrieval_query", db=db)
  ```
- Note: `db` session is already available in `build_timeline_from_topic()`

---

## Phase 4: Maintenance & Cleanup

### 4.1 Scheduled cache cleanup
- **File:** `backend/scheduler.py`
- Add weekly job (Sunday 3 AM IST):
  ```python
  def cleanup_query_cache():
      db = SessionLocal()
      deleted = db.execute(text(
          "DELETE FROM query_embeddings WHERE last_used_at < NOW() - INTERVAL '30 days'"
      ))
      db.commit()
      logger.info(f"Query cache cleanup: deleted {deleted.rowcount} stale entries")
      db.close()
  ```

### 4.2 Model migration helper
- **File:** `backend/services/query_embedding_cache.py`
- Add `invalidate_model(old_model: str, db: Session)` method:
  ```python
  def invalidate_model(self, old_model: str, db: Session):
      deleted = db.execute(text(
          "DELETE FROM query_embeddings WHERE model_name = :model"
      ), {"model": old_model})
      db.commit()
      self._lru.clear()  # Also flush LRU
      logger.info(f"Invalidated {deleted.rowcount} cached embeddings for model {old_model}")
  ```

---

## Phase 5: Verification & Testing

### 5.1 Unit tests
- **File:** `backend/tests/test_query_cache.py` (new)
- Test normalize: `"  Large   Language Models  "` → `"large language models"`
- Test normalize truncation: 2000-char input → truncated to 1000 chars
- Test cache key determinism: same input → same hash
- Test cache key differs by task_type: `retrieval_query` vs `clustering` → different hash
- Test LRU eviction: insert 1025 entries with max 1024 → oldest evicted
- Test thread safety: concurrent `_lru_get`/`_lru_put` from multiple threads → no crash
- Test `_validate`: `[]` → False, `[0.1]*768` → True, `[0.1]*100` → False
- Test get_or_generate: mock Gemini, verify first call generates, second call returns cached
- Test negative caching prevention: mock Gemini returning `[]`, verify NOT cached

### 5.2 Integration test
- Test full flow against local DB:
  1. Search "attention mechanism" — verify Gemini API called, log shows `cache_miss source=gemini`
  2. Search "attention mechanism" again — verify Gemini API NOT called, log shows `cache_hit source=lru`
  3. Restart process (clear LRU), search same query — log shows `cache_hit source=postgres`
  4. Search "ATTENTION mechanism" — verify cache hit (normalization works)
  5. Check `query_embeddings` table has 1 row

### 5.3 Production verification
```sql
-- After deploying, run a few searches then check:
SELECT query_text, hit_count, model_name, created_at, last_used_at
FROM query_embeddings ORDER BY created_at DESC LIMIT 10;

-- Cache effectiveness after a few days:
SELECT
  COUNT(*) AS total_cached,
  SUM(hit_count) AS total_hits,
  ROUND(AVG(hit_count), 1) AS avg_hits_per_query,
  COUNT(*) FILTER (WHERE hit_count > 1) AS reused_queries
FROM query_embeddings;
```

---

## File Summary

| File | Action | Phase |
|------|--------|-------|
| `backend/routers/search.py` | Fix chat task_type bug (separate commit) | 0 |
| `backend/models/query_cache.py` | New — ORM model | 1 |
| `backend/models/__init__.py` | Add export | 1 |
| `backend/migrate_query_cache.py` | New — migration script | 1 |
| `backend/config.py` | Add `QUERY_CACHE_LRU_SIZE` setting | 1 |
| `backend/services/query_embedding_cache.py` | New — cache service with LRU + PG | 2 |
| `backend/routers/search.py` | Use cache in search + chat | 3 |
| `backend/services/timeline_service.py` | Use cache in topic search | 3 |
| `backend/scheduler.py` | Add weekly cleanup job | 4 |
| `backend/tests/test_query_cache.py` | New — unit + integration tests | 5 |

**Total new files:** 4
**Total modified files:** 5
**Estimated lines:** ~200 new, ~15 modified

---

## Review-Driven Hardening (addressed gaps)

| Gap | Resolution |
|-----|-----------|
| Thread safety (LRU) | `threading.Lock` wrapping all `OrderedDict` access |
| Caching empty embeddings | `_validate()` check before any cache write; `[]` never cached |
| Thundering herd | `INSERT ON CONFLICT DO NOTHING`; duplicate Gemini calls acceptable at our scale |
| Wasteful DB writes on hits | LRU hits skip DB entirely; PG hits update only if `last_used_at` > 24h old |
| Chat task_type fix | Separate Phase 0 commit before caching work |
| LRU memory on ARM64 | Default 1024 entries (~8MB), configurable via `QUERY_CACHE_LRU_SIZE` |
| No observability | Structured logging on every hit/miss with source and latency |
| Ollama provider | Model name read from `llm_service.embedding_model`, not hardcoded |
| Query length | Truncate to 1000 chars before normalize and hash |
| Migration safety | `CREATE TABLE IF NOT EXISTS`, follows existing idempotent pattern |
| Corpus-independent invariant | Documented in Design Invariants section |
