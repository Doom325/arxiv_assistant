"""Migration: create category_poll_state and seed default categories.

Creates the ``category_poll_state`` table that backs the daily arXiv poller's
per-category high-water mark. For each of the default categories we seed a
row with ``last_successful_submitted_date = today - 14 days`` so the first
daily run performs a bounded initial backfill (NOT the full arXiv history).

Idempotent — safe to re-run.

Usage:
    python migrate_category_poll_state.py
"""

import datetime
import logging
from datetime import timedelta

from sqlalchemy import inspect, text

from database import engine
from poll_constants import INITIAL_BACKFILL_DAYS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_CATEGORIES = [
    "cs.AI", "cs.LG", "cs.CL", "cs.CV", "cs.RO",
    "cs.MA", "cs.NE", "cs.IR", "cs.SI", "cs.HC", "cs.CY",
]


def run_migration() -> None:
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    with engine.begin() as conn:
        if "category_poll_state" not in existing_tables:
            conn.execute(text("""
                CREATE TABLE category_poll_state (
                    category VARCHAR PRIMARY KEY,
                    last_successful_submitted_date DATE,
                    last_run_at TIMESTAMP,
                    last_success_at TIMESTAMP,
                    last_error TEXT
                );
            """))
            logger.info("Created table: category_poll_state")
        else:
            logger.info(
                "Table category_poll_state already exists — skipping create."
            )

    # arXiv's ``submittedDate`` is UTC — anchor the seed in UTC so the
    # bounded 14-day backfill window doesn't shift by a day on hosts
    # whose system timezone isn't UTC.
    today_utc = datetime.datetime.now(datetime.timezone.utc).date()
    seed_date = today_utc - timedelta(days=INITIAL_BACKFILL_DAYS)
    with engine.begin() as conn:
        for category in DEFAULT_CATEGORIES:
            # INSERT ... ON CONFLICT DO NOTHING keeps re-runs safe and never
            # clobbers a category's existing high-water mark.
            conn.execute(
                text("""
                    INSERT INTO category_poll_state (
                        category, last_successful_submitted_date
                    )
                    VALUES (:category, :seed_date)
                    ON CONFLICT (category) DO NOTHING;
                """),
                {"category": category, "seed_date": seed_date},
            )
        logger.info(
            "Seeded %d default categories with backfill floor %s "
            "(existing rows preserved).",
            len(DEFAULT_CATEGORIES),
            seed_date.isoformat(),
        )

    logger.info("Migration complete.")


if __name__ == "__main__":
    run_migration()
