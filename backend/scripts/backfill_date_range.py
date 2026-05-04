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


def _process_one_query(
    db: Session,
    category: str,
    since: datetime.date,
    until: datetime.date,
    safety_cap: int,
    skip_ai: bool,
) -> tuple[int, int]:
    """Run a single ``fetch_papers_since`` and ingest. Returns (new, seen).

    Caller owns commits/rollbacks at the granularity that makes sense for
    its loop (per-day or per-category).
    """
    new_count = 0
    seen_count = 0
    for paper_data in arxiv_service.fetch_papers_since(
        category=category,
        since_date=since,
        until_date=until,
        safety_cap=safety_cap,
        descending=True,
    ):
        seen_count += 1
        try:
            created = process_paper_entry(
                db, paper_data, skip_ai=skip_ai
            )
            if created:
                new_count += 1
        except Exception:
            # process_paper_entry rolls back inside its own try block, but
            # its initial existence-check SELECT runs *outside* it — so a
            # poisoned session reaches us here without being cleaned up.
            # Roll back so the next paper's SELECT starts fresh.
            logger.exception(
                "Skipping paper %s due to ingestion error",
                paper_data.get("arxiv_id"),
            )
            db.rollback()
    return new_count, seen_count


def _iter_dates(
    start: datetime.date,
    end: datetime.date,
    descending: bool = True,
) -> list[datetime.date]:
    """Inclusive list of dates between ``start`` and ``end``.
    ``descending=True`` returns newest → oldest (default for backfill).
    """
    span = (end - start).days
    dates = [start + datetime.timedelta(days=i) for i in range(span + 1)]
    if descending:
        dates.reverse()
    return dates


def backfill(
    start: datetime.date,
    end: datetime.date,
    categories: list[str],
    skip_ai: bool = True,
    safety_cap: int = POLL_SAFETY_CAP,
    per_day: bool = True,
) -> dict:
    """Per-day mode (default) iterates day-by-day, each query is single-day.
    No realistic single category produces >100 papers/day, so cap truncation
    becomes effectively impossible. Multi-day failures are also isolated:
    if April 30 fails, May 1 still runs.

    Bulk mode (``per_day=False``) issues one multi-day query per category.
    Faster (fewer HTTP round-trips), but needs ``safety_cap`` set high
    enough to cover the busiest category × full range.
    """
    db: Session = SessionLocal()
    summary: dict = {"categories": {}, "total_new": 0, "total_seen": 0}
    # Pre-seed per-category counters so categories with zero results still
    # appear in the summary.
    for cat in sorted(categories):
        summary["categories"][cat] = {"new": 0, "seen": 0, "truncated": False}
    try:
        if per_day:
            for day in _iter_dates(start, end, descending=True):
                logger.info("=== Day: %s ===", day)
                for category in sorted(categories):
                    try:
                        new_c, seen_c = _process_one_query(
                            db, category, day, day, safety_cap, skip_ai
                        )
                        db.commit()
                    except Exception:
                        logger.exception(
                            "Day %s category %s failed mid-stream",
                            day, category,
                        )
                        db.rollback()
                        new_c, seen_c = 0, 0
                    summary["categories"][category]["new"] += new_c
                    summary["categories"][category]["seen"] += seen_c
                    summary["total_new"] += new_c
                    summary["total_seen"] += seen_c
                    if seen_c >= safety_cap:
                        # Per-day shouldn't ever hit this realistically, but
                        # if it does, flag the category so the summary is
                        # honest.
                        summary["categories"][category]["truncated"] = True
                        logger.warning(
                            "Day %s category %s hit safety_cap=%d",
                            day, category, safety_cap,
                        )
                    if seen_c:
                        logger.info(
                            "  %s: new=%d seen=%d", category, new_c, seen_c
                        )
        else:
            for category in sorted(categories):
                logger.info(
                    "Polling category=%s since=%s until=%s",
                    category, start, end,
                )
                try:
                    new_c, seen_c = _process_one_query(
                        db, category, start, end, safety_cap, skip_ai
                    )
                    db.commit()
                    truncated = seen_c >= safety_cap
                    if truncated:
                        logger.warning(
                            "Category %s hit safety_cap=%d — truncated. "
                            "Re-run with a tighter range or higher "
                            "--max-per-category.",
                            category, safety_cap,
                        )
                except Exception:
                    logger.exception(
                        "Category %s failed mid-stream", category,
                    )
                    db.rollback()
                    new_c, seen_c, truncated = 0, 0, False
                summary["categories"][category] = {
                    "new": new_c, "seen": seen_c, "truncated": truncated,
                }
                summary["total_new"] += new_c
                summary["total_seen"] += seen_c
                logger.info(
                    "Category %s done: new=%d seen=%d%s",
                    category, new_c, seen_c,
                    " (TRUNCATED)" if truncated else "",
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
    parser.add_argument(
        "--bulk",
        action="store_true",
        help=(
            "Issue one multi-day query per category instead of iterating "
            "day-by-day (default). Bulk mode is faster on long ranges but "
            "needs --max-per-category set high enough to cover the busiest "
            "category × full range. Per-day mode (the default) avoids "
            "cap truncation by keeping every query single-day."
        ),
    )
    args = parser.parse_args(argv)

    if args.start > args.end:
        parser.error(f"--start ({args.start}) must be <= --end ({args.end})")

    logger.info(
        "Backfill: %s → %s, categories=%s, skip_ai=%s, mode=%s",
        args.start,
        args.end,
        args.categories,
        not args.with_ai,
        "bulk" if args.bulk else "per-day",
    )
    result = backfill(
        start=args.start,
        end=args.end,
        categories=args.categories,
        skip_ai=not args.with_ai,
        safety_cap=args.max_per_category,
        per_day=not args.bulk,
    )
    logger.info("Done: total_new=%d total_seen=%d", result["total_new"], result["total_seen"])
    for cat, stats in result["categories"].items():
        logger.info("  %s: new=%d seen=%d", cat, stats["new"], stats["seen"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
