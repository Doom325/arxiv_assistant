#!/usr/bin/env python3
"""Backfill paper metadata for an explicit date range and category list.

Uses arXiv's ``submittedDate:[since TO until]`` range query (the same one
the daily scheduler uses) and ingests via ``process_paper_entry``. Idempotent:
papers already in the DB are skipped on the unique ``arxiv_id`` constraint.

Usage:
    python scripts/backfill_date_range.py \\
        --start 2026-01-01 --end 2026-01-31 \\
        --categories cs.AI,cs.LG,cs.CL

Defaults: categories = the scheduler's DEFAULT_CATEGORIES.
``--end`` defaults to today (UTC). ``--start`` is required.

Notes:
- ``submittedDate`` is UTC. We pass dates as-is; arXiv applies UTC bounds.
- Order is oldest → newest within each category, matching the scheduler.
- Per-paper exceptions are logged and skipped — bad rows don't stall the run.
"""

import argparse
import datetime
import logging
import os
import sys

# Backend root on sys.path so ``database`` etc. resolve when run as a script.
_BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

from sqlalchemy.orm import Session

from database import SessionLocal
from ingestion import process_paper_entry
from poll_constants import DEFAULT_CATEGORIES, POLL_SAFETY_CAP
from services.arxiv_service import arxiv_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger("backfill_date_range")


def _parse_date(s: str) -> datetime.date:
    return datetime.datetime.strptime(s, "%Y-%m-%d").date()


def backfill(
    start: datetime.date,
    end: datetime.date,
    categories: list[str],
    skip_ai: bool = True,
    safety_cap: int = POLL_SAFETY_CAP,
) -> dict:
    db: Session = SessionLocal()
    summary: dict = {"categories": {}, "total_new": 0, "total_seen": 0}
    try:
        for category in sorted(categories):
            new_count = 0
            seen_count = 0
            logger.info(
                "Polling category=%s since=%s until=%s", category, start, end
            )
            try:
                for paper_data in arxiv_service.fetch_papers_since(
                    category=category,
                    since_date=start,
                    until_date=end,
                    safety_cap=safety_cap,
                ):
                    seen_count += 1
                    try:
                        created = process_paper_entry(
                            db, paper_data, skip_ai=skip_ai
                        )
                        if created:
                            new_count += 1
                    except Exception:
                        # process_paper_entry rolls back inside its own try
                        # block, but its initial existence-check SELECT runs
                        # *outside* it — so a poisoned session reaches us
                        # here without being cleaned up. Roll back so the
                        # next paper's SELECT can start a fresh transaction.
                        logger.exception(
                            "Skipping paper %s due to ingestion error",
                            paper_data.get("arxiv_id"),
                        )
                        db.rollback()
                # Commit per-category so a later category failure doesn't
                # discard everything we just did.
                db.commit()
                if seen_count >= safety_cap:
                    # fetch_papers_since stops at safety_cap; on a
                    # multi-week backfill of a busy category that means
                    # silent truncation. Surface it clearly so the
                    # operator knows to re-run with a smaller range or
                    # higher --max-per-category.
                    logger.warning(
                        "Category %s hit safety_cap=%d — results truncated. "
                        "Re-run with a tighter date range or pass "
                        "--max-per-category > %d.",
                        category, safety_cap, safety_cap,
                    )
            except Exception:
                logger.exception("Category %s failed mid-stream", category)
                db.rollback()
            summary["categories"][category] = {
                "new": new_count,
                "seen": seen_count,
                "truncated": seen_count >= safety_cap,
            }
            summary["total_new"] += new_count
            summary["total_seen"] += seen_count
            logger.info(
                "Category %s done: new=%d seen=%d%s",
                category,
                new_count,
                seen_count,
                " (TRUNCATED)" if seen_count >= safety_cap else "",
            )
    finally:
        db.close()
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Backfill arXiv papers for a date range."
    )
    parser.add_argument(
        "--start",
        required=True,
        type=_parse_date,
        help="Start date (inclusive), YYYY-MM-DD.",
    )
    parser.add_argument(
        "--end",
        type=_parse_date,
        default=datetime.datetime.now(datetime.timezone.utc).date(),
        help="End date (inclusive), YYYY-MM-DD. Defaults to today (UTC).",
    )
    parser.add_argument(
        "--categories",
        type=lambda s: [c.strip() for c in s.split(",") if c.strip()],
        default=sorted(DEFAULT_CATEGORIES),
        help=(
            "Comma-separated arXiv categories. "
            f"Defaults to scheduler default: {','.join(sorted(DEFAULT_CATEGORIES))}"
        ),
    )
    parser.add_argument(
        "--with-ai",
        action="store_true",
        help=(
            "Run AI processing inline (slow). Default: metadata-only — "
            "the production_worker picks up unprocessed rows."
        ),
    )
    parser.add_argument(
        "--max-per-category",
        type=int,
        default=POLL_SAFETY_CAP,
        help=(
            f"Hard ceiling on papers fetched per category (default: {POLL_SAFETY_CAP}). "
            "Hitting the cap logs a warning and truncates the category — "
            "re-run with a tighter date range or a higher value."
        ),
    )
    args = parser.parse_args(argv)

    if args.start > args.end:
        parser.error(f"--start ({args.start}) must be <= --end ({args.end})")

    logger.info(
        "Backfill: %s → %s, categories=%s, skip_ai=%s",
        args.start,
        args.end,
        args.categories,
        not args.with_ai,
    )
    result = backfill(
        start=args.start,
        end=args.end,
        categories=args.categories,
        skip_ai=not args.with_ai,
        safety_cap=args.max_per_category,
    )
    logger.info("Done: total_new=%d total_seen=%d", result["total_new"], result["total_seen"])
    for cat, stats in result["categories"].items():
        logger.info("  %s: new=%d seen=%d", cat, stats["new"], stats["seen"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
