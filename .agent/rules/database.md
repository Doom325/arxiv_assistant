# Database Standards

These rules apply when working with PostgreSQL, pgvector, or SQLAlchemy models.

## PostgreSQL Configuration

- PostgreSQL 16 + pgvector extension. Port **5434** (not the default 5432).
- Database container: `pgvector/pgvector:pg16`.
- Connection pool: size 20, max overflow 30 (configured in `database.py`).
- Tables are auto-created on FastAPI startup via the lifespan hook.

## pgvector & Embeddings

- Embedding dimension: **3072** (Gemini embedding-001).
- Vector columns use `pgvector.sqlalchemy.Vector(3072)`.
- Similarity search: cosine distance (`<=>` operator) or L2 distance (`<->` operator).
- Embedding generation goes through `llm_service.py` — never call the embedding API directly.
- The `PaperEmbedding` model supports multi-embedding storage per paper.

## SQLAlchemy ORM

- Use the declarative base from `models/base.py`.
- One model file per domain: `paper.py`, `user.py`, `jobs.py`, `citation.py`, `pattern.py`.
- All models must be exported from `models/__init__.py`.
- Use the `get_db` dependency for session management in FastAPI routes.
- Never create sessions manually in routers — always use `Depends(get_db)`.

## Schema Changes

- Write migration scripts as `migrate_<description>.py` in the backend root.
- Migrations must be backward-compatible: add columns as nullable, don't drop columns in the same release.
- Test migrations against a copy of the production database before deploying.
- Document the migration in the script's docstring.

## Query Patterns

- Use SQLAlchemy ORM for standard CRUD operations.
- Raw SQL is acceptable only for pgvector-specific operations (vector search, index creation).
- Always use parameterized queries — never string-interpolate values into SQL.
- Full-text search uses PostgreSQL `tsvector` columns with GIN indexes.
- Hybrid search combines vector similarity + full-text via Reciprocal Rank Fusion (RRF).

## Data Integrity

- The `Paper` model has a unique constraint on `arxiv_id`.
- `CitationLink` represents directed edges (source_paper_id → target_arxiv_id) with optional `resolved_paper_id`.
- `UserLibrary` uses `list_name` for bookmark grouping per user.
- Use `text_utils.sanitize_text()` before inserting any text extracted from PDFs.
