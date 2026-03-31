"""Migration: Add full_text_sections column to papers table.

Idempotent — safe to run multiple times.
"""

import logging

from sqlalchemy import inspect, text

from database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_migration() -> None:
    inspector = inspect(engine)
    columns = {c["name"] for c in inspector.get_columns("papers")}

    with engine.begin() as conn:
        if "full_text_sections" not in columns:
            conn.execute(text("""
                ALTER TABLE papers
                    ADD COLUMN full_text_sections JSONB;
            """))
            logger.info("Added column: papers.full_text_sections")
        else:
            logger.info(
                "Column papers.full_text_sections already exists — skipping."
            )

    logger.info("Migration complete.")


if __name__ == "__main__":
    run_migration()
