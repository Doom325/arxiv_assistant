"""Migration: create query_embeddings table for the query embedding cache.

Idempotent — safe to run multiple times.

Usage:
    python migrate_query_cache.py
"""

import logging

from sqlalchemy import text

from database import SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DDL = """
CREATE TABLE IF NOT EXISTS query_embeddings (
    id              SERIAL PRIMARY KEY,
    query_hash      VARCHAR(64) NOT NULL UNIQUE,
    query_text      TEXT NOT NULL,
    task_type       VARCHAR NOT NULL DEFAULT 'retrieval_query',
    embedding       vector(768) NOT NULL,
    model_name      VARCHAR NOT NULL,
    hit_count       INTEGER NOT NULL DEFAULT 0,
    created_at      TIMESTAMP NOT NULL DEFAULT now(),
    last_used_at    TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_query_cache_lookup
    ON query_embeddings (query_hash);
"""


def migrate() -> None:
    db = SessionLocal()
    try:
        db.execute(text(DDL))
        db.commit()
        logger.info("query_embeddings table created (or already exists).")
    except Exception:
        db.rollback()
        logger.exception("Migration failed")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    migrate()
