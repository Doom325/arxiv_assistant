#!/usr/bin/env python3
"""Send catch-up digest emails for days the daily digest under-delivered.

Before issue #50 the digest selected papers by ``published_date == yesterday``
and the cs.AI poll failed on most mornings, so most cs.AI papers were never
emailed. This script sends one compact email per publish day.

It partitions cleanly with the daily digest's ingestion watermark
(``max_paper_id`` on the latest SUCCESS ``email_digest`` JobLog):

    daily digest sends   Paper.id >  watermark
    this script sends    Paper.id <= watermark   (``--max-paper-id``)

Run order, inside the backend container:

    # 1. after re-ingesting the missing papers (scripts/backfill_date_range.py),
    #    pin the daily digest's watermark to the current max id so it doesn't
    #    send the whole refilled backlog in one email; prints the id.
    python scripts/email/backfill_digest.py --seed-watermark

    # 2. preview (default: dry run — counts and sizes, nothing sent)
    python scripts/email/backfill_digest.py --start 2026-09-15 --end 2026-09-29 --max-paper-id <id>

    # 3. send
    python scripts/email/backfill_digest.py --start ... --end ... --max-paper-id <id> --send

Each sent day is logged as an ``email_digest_backfill`` JobLog; re-running
skips days already sent, so an interrupted run resumes. It never writes
``email_digest`` rows except the explicit ``--seed-watermark`` one.
"""

import argparse
import datetime
import logging
import os
import sys

_BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

from sqlalchemy import func
from sqlalchemy.orm import Session

from config import settings
from database import SessionLocal
from models import JobLog, Paper
from services.email_service import email_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("backfill_digest")

BACKFILL_JOB_NAME = "email_digest_backfill"
DIGEST_JOB_NAME = "email_digest"  # must match scheduler.DIGEST_JOB_NAME
CATEGORY = "cs.AI"
# ~290 papers fit under Gmail's ~102KB clip limit in the compact template;
# split larger days into parts with headroom.
MAX_PAPERS_PER_EMAIL = 250


def seed_watermark(db: Session) -> int:
    """Record max(Paper.id) as the daily digest's watermark and return it."""
    max_id = db.query(func.max(Paper.id)).scalar() or 0
    db.add(
        JobLog(
            job_name=DIGEST_JOB_NAME,
            status="SUCCESS",
            start_time=datetime.datetime.utcnow(),
            end_time=datetime.datetime.utcnow(),
            job_details={"mode": "seed", "count": 0, "max_paper_id": max_id},
            error_message="Watermark seeded by scripts/email/backfill_digest.py",
        )
    )
    db.commit()
    return max_id


def papers_for_day(db: Session, day: datetime.date, max_paper_id: int) -> list[Paper]:
    """cs.AI-primary papers published on ``day`` (UTC) at or below the watermark."""
    return (
        db.query(Paper)
        .filter(
            Paper.category == CATEGORY,
            func.date(Paper.published_date) == day,
            Paper.id <= max_paper_id,
        )
        .order_by(Paper.published_date.asc(), Paper.id.asc())
        .all()
    )


def already_sent(db: Session, day: datetime.date) -> bool:
    rows = db.query(JobLog).filter(
        JobLog.job_name == BACKFILL_JOB_NAME, JobLog.status == "SUCCESS"
    )
    return any((r.job_details or {}).get("date") == day.isoformat() for r in rows)


def chunks(papers: list[Paper], size: int = MAX_PAPERS_PER_EMAIL) -> list[list[Paper]]:
    return [papers[i : i + size] for i in range(0, len(papers), size)] or [[]]


def send_day(db: Session, day: datetime.date, papers: list[Paper], recipients: list[str]) -> bool:
    """Send every part for ``day`` to every recipient; log one JobLog for the day."""
    parts = chunks(papers)
    failures: list[str] = []
    for n, part in enumerate(parts, 1):
        heading = f"arXiv cs.AI catch-up — {day:%a %d %b %Y}"
        if len(parts) > 1:
            heading += f" (part {n}/{len(parts)})"
        for email in recipients:
            ok, detail = email_service.send_catchup_digest(email, part, heading)
            if not ok:
                failures.append(f"{email} part {n}: {detail}")
    db.add(
        JobLog(
            job_name=BACKFILL_JOB_NAME,
            status="FAILED" if failures else "SUCCESS",
            start_time=datetime.datetime.utcnow(),
            end_time=datetime.datetime.utcnow(),
            job_details={"date": day.isoformat(), "count": len(papers), "parts": len(parts)},
            error_message="; ".join(failures) or None,
        )
    )
    db.commit()
    return not failures


def run(start: datetime.date, end: datetime.date, max_paper_id: int, send: bool, db: Session) -> int:
    recipients = settings.RECIPIENT_LIST
    if send and not recipients:
        logger.error("EMAIL_RECIPIENTS is empty — nothing to send to")
        return 1
    failed = 0
    day = start
    while day <= end:
        papers = papers_for_day(db, day, max_paper_id)
        size_kb = len(email_service._generate_compact_html(chunks(papers)[0], "x").encode()) // 1024
        if not papers:
            logger.info("%s: 0 papers — skipping", day)
        elif already_sent(db, day):
            logger.info("%s: %d papers — already sent, skipping", day, len(papers))
        elif not send:
            logger.info("%s: %d papers, %d part(s), first part ~%dKB [dry run]",
                        day, len(papers), len(chunks(papers)), size_kb)
        elif send_day(db, day, papers, recipients):
            logger.info("%s: sent %d papers to %s", day, len(papers), ", ".join(recipients))
        else:
            failed += 1
            logger.error("%s: send FAILED — re-run to retry this day", day)
        day += datetime.timedelta(days=1)
    return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--seed-watermark", action="store_true",
                        help="Record max(Paper.id) as the daily digest watermark, print it, and exit.")
    parser.add_argument("--start", type=datetime.date.fromisoformat, help="First publish day (UTC), YYYY-MM-DD.")
    parser.add_argument("--end", type=datetime.date.fromisoformat, help="Last publish day (UTC), inclusive.")
    parser.add_argument("--max-paper-id", type=int,
                        help="Only papers with id <= this (the seeded watermark).")
    parser.add_argument("--send", action="store_true", help="Actually send (default: dry run).")
    args = parser.parse_args(argv)

    db = SessionLocal()
    try:
        if args.seed_watermark:
            print(f"Seeded daily digest watermark: max_paper_id={seed_watermark(db)}")
            return 0
        if not (args.start and args.end and args.max_paper_id):
            parser.error("--start, --end and --max-paper-id are required unless --seed-watermark")
        if args.start > args.end:
            parser.error("--start must be <= --end")
        return run(args.start, args.end, args.max_paper_id, args.send, db)
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
