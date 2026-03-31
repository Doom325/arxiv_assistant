"""Migration: Create reading_queue and user_interest_profiles tables.

Idempotent — safe to run multiple times.
"""

import logging

from sqlalchemy import inspect, text

from database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_migration() -> None:
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    with engine.begin() as conn:
        # --- reading_queue ---
        if "reading_queue" not in existing_tables:
            conn.execute(text("""
                CREATE TABLE reading_queue (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL
                        REFERENCES users(id),
                    paper_id INTEGER NOT NULL
                        REFERENCES papers(id),
                    priority_score FLOAT DEFAULT 0.0,
                    interest_similarity FLOAT DEFAULT 0.0,
                    citation_impact FLOAT DEFAULT 0.0,
                    freshness_score FLOAT DEFAULT 0.0,
                    category_score FLOAT DEFAULT 0.0,
                    entity_overlap FLOAT DEFAULT 0.0,
                    peer_reads_score FLOAT DEFAULT 0.0,
                    read_status VARCHAR NOT NULL DEFAULT 'unread',
                    manual_priority INTEGER,
                    added_at TIMESTAMP DEFAULT NOW(),
                    scored_at TIMESTAMP,
                    read_at TIMESTAMP,
                    CONSTRAINT uq_user_paper
                        UNIQUE (user_id, paper_id)
                );
            """))
            conn.execute(text("""
                CREATE INDEX idx_queue_user_status_score
                    ON reading_queue (
                        user_id, read_status, priority_score DESC
                    );
            """))
            logger.info("Created table: reading_queue")
        else:
            logger.info("Table reading_queue already exists — skipping.")

        # --- user_interest_profiles ---
        if "user_interest_profiles" not in existing_tables:
            conn.execute(text("""
                CREATE TABLE user_interest_profiles (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL
                        REFERENCES users(id) UNIQUE,
                    interest_vector vector(768),
                    top_categories JSONB,
                    top_entities JSONB,
                    papers_used INTEGER DEFAULT 0,
                    computed_at TIMESTAMP DEFAULT NOW()
                );
            """))
            logger.info("Created table: user_interest_profiles")
        else:
            logger.info(
                "Table user_interest_profiles already exists — skipping."
            )

    # --- Discovery columns on reading_queue ---
    # Use a fresh inspector after the first block committed
    inspector = inspect(engine)
    rq_exists = "reading_queue" in inspector.get_table_names()
    if rq_exists:
        columns = {
            c["name"]
            for c in inspector.get_columns("reading_queue")
        }
        with engine.begin() as conn:
            if "source" not in columns:
                conn.execute(text("""
                    ALTER TABLE reading_queue
                        ADD COLUMN source VARCHAR
                            NOT NULL DEFAULT 'bookmark';
                """))
                conn.execute(text("""
                    CREATE INDEX idx_queue_source
                        ON reading_queue (user_id, source);
                """))
                logger.info("Added column: reading_queue.source")
            if "best_match_paper_id" not in columns:
                conn.execute(text("""
                    ALTER TABLE reading_queue
                        ADD COLUMN best_match_paper_id INTEGER
                            REFERENCES papers(id),
                        ADD COLUMN best_match_score FLOAT;
                """))
                logger.info(
                    "Added columns: best_match_paper_id, "
                    "best_match_score"
                )

    logger.info("Migration complete.")


if __name__ == "__main__":
    run_migration()
