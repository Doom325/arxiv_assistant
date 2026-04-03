---
name: optimize-search
description: Optimizes hybrid search performance including semantic search, keyword search, RRF ranking, and query embedding caching. Use when the user asks about search quality, relevance tuning, or search performance.
---

# Optimize Search

The search system uses hybrid retrieval: semantic (pgvector) + keyword (PostgreSQL full-text) merged via Reciprocal Rank Fusion (RRF).

## Architecture

- **Semantic search:** `backend/routers/search.py` generates a query embedding via `llm_service`, then finds nearest neighbors using pgvector cosine distance (`<=>`).
- **Keyword search:** PostgreSQL full-text search on `tsvector` columns with GIN index.
- **Fusion:** RRF merges both result sets: `score = sum(1 / (k + rank))` with `k=60` default.
- **Metadata filters:** Parsed from query string — `category:cs.AI`, `after:2024-01`, `before:2025-01`, `author:smith`, `entity:transformer`.
- **Caching:** `query_embedding_cache.py` provides LRU caching for repeated query embeddings.

## Key Files

| File | Purpose |
|------|---------|
| `backend/routers/search.py` | Search endpoint, RRF implementation, filter parsing |
| `backend/services/llm_service.py` | Query embedding generation |
| `backend/services/query_embedding_cache.py` | LRU cache for query embeddings |
| `backend/models/paper.py` | Paper model with pgvector column and tsvector column |

## Tuning Parameters

### RRF Constant (k)
- Default `k=60`. Lower values weight top results more heavily.
- Adjust in `search.py` where RRF scores are computed.

### Semantic vs Keyword Weight
- Currently equal weight. To favor semantic: multiply semantic RRF scores by a factor > 1.
- To favor keyword: multiply keyword RRF scores by a factor > 1.

### Embedding Dimensions
- Current: 3072D (Gemini embedding-001). Supports MRL (Matryoshka Representation Learning) for 768D queries.
- Smaller dimensions = faster search but potentially lower quality.

### pgvector Index
- Ensure IVFFlat or HNSW index exists on the embedding column.
- HNSW: better recall, slower builds. IVFFlat: faster builds, needs tuning of `lists` parameter.
- Check: `SELECT indexname FROM pg_indexes WHERE tablename = 'papers';`

## Debugging Search Quality

1. Compare semantic-only vs keyword-only results for the same query.
2. Check if the query embedding is in the same space as paper embeddings (same model, same dimensions).
3. Verify tsvector content matches expected terms: `SELECT to_tsvector('english', title || ' ' || abstract) FROM papers WHERE id = X;`
4. Check the GIN index is being used: `EXPLAIN ANALYZE SELECT ... WHERE tsv @@ to_tsquery(...)`.

## Performance Optimization

- Add query embedding caching for repeated/similar queries.
- Use pgvector approximate nearest neighbor (ANN) instead of exact search for large collections.
- Consider pre-filtering by metadata (date, category) before vector search to reduce candidate set.
- Monitor query latency via the existing benchmark scripts in `backend/scripts/benchmarks/`.

## Reference

See `Optimizing Search Retrieval.md` in the project root for an in-depth analysis of search optimization strategies specific to this project.
