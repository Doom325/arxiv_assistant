import datetime
import json
import logging
import os

import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import func
from sqlalchemy.orm import Session

from config import settings
from database import SessionLocal
from ingestion import process_paper_entry
import models
from models import CategoryPollState, JobLog, Paper, UserConfig
from poll_constants import (
    DEFAULT_CATEGORIES,
    INITIAL_BACKFILL_DAYS,
    REPOLL_OVERLAP_DAYS,
)
from services.arxiv_service import arxiv_service
from services.batch_service import batch_service
from services.email_service import email_service
from services.summarization_service import summarization_service
from services import reading_queue_service as rqs
from services.query_embedding_cache import query_cache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Daily digest selection: watermark on Paper.id (ingestion order), persisted
# in the last successful email_digest JobLog. Selecting by ingestion order
# instead of arXiv's submission date means a paper the arXiv API serves a
# day late lands in the next digest instead of being dropped forever.
DIGEST_JOB_NAME = "email_digest"
DIGEST_WATERMARK_KEY = "max_paper_id"
DIGEST_MAX_AGE_DAYS = 7
DIGEST_CATEGORY = "cs.AI"


def _latest_digest_watermark(db: Session) -> int | None:
    """Max Paper.id sent by the last successful digest, or None if never."""
    last = (
        db.query(JobLog)
        .filter(JobLog.job_name == DIGEST_JOB_NAME, JobLog.status == "SUCCESS")
        .order_by(JobLog.id.desc())
        .first()
    )
    if last is None or not last.job_details:
        return None
    return last.job_details.get(DIGEST_WATERMARK_KEY)


def _select_digest_papers(db: Session, watermark: int | None) -> list[Paper]:
    """cs.AI-primary papers for today's digest, oldest id first.

    With a watermark: every matching paper ingested since the last
    successful digest, bounded to papers published in the last
    ``DIGEST_MAX_AGE_DAYS`` so a historical backfill (scripts/backfill_*)
    can't flood one digest with old papers. Bootstrap (no watermark yet):
    the legacy rule — papers published yesterday IST.
    """
    query = db.query(Paper).filter(Paper.category == DIGEST_CATEGORY)
    if watermark is None:
        ist = pytz.timezone("Asia/Kolkata")
        yesterday = datetime.datetime.now(ist).date() - datetime.timedelta(days=1)
        return (
            query.filter(func.date(Paper.published_date) == yesterday)
            .order_by(Paper.id.asc())
            .all()
        )
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(
        days=DIGEST_MAX_AGE_DAYS
    )
    return (
        query.filter(Paper.id > watermark, Paper.published_date >= cutoff)
        .order_by(Paper.id.asc())
        .all()
    )


def _collect_categories(db: Session) -> set:
    """Union of user-configured categories, falling back to defaults."""
    configs = db.query(UserConfig).all()
    categories: set = set()
    for config in configs:
        if config.categories:
            categories.update(config.categories)
    return categories or set(DEFAULT_CATEGORIES)


def _get_or_create_poll_state(
    db: Session, category: str
) -> CategoryPollState:
    state = db.query(CategoryPollState).filter(
        CategoryPollState.category == category
    ).first()
    if state is not None:
        return state
    # Commit the fresh row before the paper loop runs so that
    # process_paper_entry's per-paper rollback on the first paper cannot
    # reverse this INSERT and orphan subsequent state.last_error writes.
    # The session-attached state object still receives later attribute
    # writes, which the end-of-category commit picks up.
    state = CategoryPollState(category=category)
    db.add(state)
    db.commit()
    db.refresh(state)
    return state


def _since_date_for(state: CategoryPollState, today: datetime.date) -> datetime.date:
    """Derive the arXiv ``submittedDate`` lower bound for this category."""
    if state.last_successful_submitted_date is None:
        return today - datetime.timedelta(days=INITIAL_BACKFILL_DAYS)
    return state.last_successful_submitted_date - datetime.timedelta(
        days=REPOLL_OVERLAP_DAYS
    )


def _poll_category(db: Session, category: str, today: datetime.date) -> dict:
    """Fetch + ingest papers for one category, updating its poll state.

    Returns a per-category summary dict for inclusion in the JobLog.
    Exceptions from arXiv are caught and recorded on the state row so other
    categories still run. The high-water mark is only advanced on success,
    which means a failed category self-heals on the next run.
    """
    state = _get_or_create_poll_state(db, category)
    state.last_run_at = datetime.datetime.now(datetime.timezone.utc)
    since = _since_date_for(state, today)

    new_count = 0
    max_submitted: datetime.date | None = None
    try:
        for paper_data in arxiv_service.fetch_papers_since(
            category=category, since_date=since
        ):
            # process_paper_entry is a no-op for duplicates (arxiv_id unique),
            # so overlap between runs is absorbed silently.
            created = process_paper_entry(db, paper_data)
            if created:
                new_count += 1

            submitted = paper_data.get("published_date")
            if submitted is not None:
                submitted_d = (
                    submitted.date()
                    if isinstance(submitted, datetime.datetime)
                    else submitted
                )
                if max_submitted is None or submitted_d > max_submitted:
                    max_submitted = submitted_d
    except Exception as err:
        logger.exception("Error polling category %s", category)
        state.last_error = str(err)
        return {
            "category": category,
            "since": since.isoformat(),
            "new_papers": new_count,
            "status": "FAILED",
            "error": str(err),
        }

    if max_submitted is not None:
        prior = state.last_successful_submitted_date or datetime.date.min
        if max_submitted > prior:
            state.last_successful_submitted_date = max_submitted
    state.last_success_at = datetime.datetime.now(datetime.timezone.utc)
    state.last_error = None
    return {
        "category": category,
        "since": since.isoformat(),
        "new_papers": new_count,
        "max_submitted": (
            max_submitted.isoformat() if max_submitted else None
        ),
        "status": "SUCCESS",
    }


def process_papers():
    """Daily arXiv poll with per-category high-water-mark backfill.

    arXiv announces once per day at ~20:00 ET Sun–Thu. That converts to
    ~05:30 IST in EDT (summer) and ~06:30 IST in EST (winter), so this
    job runs at 09:00 IST to sit safely after both DST windows. It uses
    a date-range query per category and persists the max observed
    ``submittedDate``. Missed runs self-heal because the next run simply
    re-queries from the last success date onwards.
    """
    logger.info("Starting daily arXiv paper poll...")
    db: Session = SessionLocal()

    job_log = JobLog(
        job_name="scheduler_poll",
        status="RUNNING",
        start_time=datetime.datetime.now(datetime.timezone.utc),
        job_details={},
    )
    db.add(job_log)
    db.commit()
    db.refresh(job_log)

    try:
        categories = _collect_categories(db)
        logger.info("Polling %d categories: %s", len(categories), categories)

        # arXiv's ``submittedDate`` is UTC — anchor ``today`` in UTC so the
        # initial-backfill window and overlap math don't shift by a day
        # when the host's system timezone isn't UTC.
        today = datetime.datetime.now(datetime.timezone.utc).date()
        per_category: list = []
        for category in sorted(categories):
            summary = _poll_category(db, category, today)
            per_category.append(summary)
            # Commit after each category so partial progress survives crashes
            # and failed categories don't hold up state updates for others.
            db.commit()

        total_new = sum(s["new_papers"] for s in per_category)
        failed = [s for s in per_category if s["status"] == "FAILED"]
        job_log.status = "WARNING" if failed else "SUCCESS"
        job_log.job_details = {
            "new_papers": total_new,
            "categories": per_category,
            "errors": [f"{s['category']}: {s['error']}" for s in failed],
        }
        logger.info(
            "Polling complete. New papers: %d (failed categories: %d)",
            total_new,
            len(failed),
        )
    except Exception as e:
        logger.exception("Error in polling")
        job_log.status = "FAILED"
        job_log.error_message = str(e)
    finally:
        job_log.end_time = datetime.datetime.utcnow()
        db.commit()
        db.close()

def send_daily_email_digest():
    """Send the daily cs.AI digest, tracking an ingestion high-water mark.

    Selects every cs.AI paper ingested since the last successful digest
    (see ``_select_digest_papers``). The watermark (max selected Paper.id)
    is persisted in this job's JobLog and advances only after every
    recipient's send is confirmed — a failed send marks the job FAILED and
    the next run retries the same papers.
    """
    logger.info("Preparing daily email digest...")
    db: Session = SessionLocal()

    job_log = JobLog(
        job_name=DIGEST_JOB_NAME,
        status="RUNNING",
        start_time=datetime.datetime.utcnow(),
    )
    db.add(job_log)
    db.commit()

    try:
        watermark = _latest_digest_watermark(db)
        mode = "watermark" if watermark is not None else "bootstrap"
        papers = _select_digest_papers(db, watermark)
        # From the rows actually selected, not a fresh max(id) at send
        # time — a paper inserted mid-run must surface in the next digest.
        max_paper_id = max((p.id for p in papers), default=None)

        recipients = settings.RECIPIENT_LIST
        failures: list[str] = []
        if papers and recipients:
            for email in recipients:
                sent, detail = email_service.send_daily_digest(email, papers)
                if sent:
                    logger.info(f"Sent daily digest to {email}")
                else:
                    failures.append(f"{email}: {detail}")

        if failures or (papers and not recipients):
            # Nothing was confirmed delivered — don't advance the
            # watermark, the next run retries these papers. An empty
            # recipient list is the same failure class: papers would be
            # silently swallowed if we marked SUCCESS.
            job_log.status = "FAILED"
            job_log.error_message = (
                "; ".join(failures)
                if failures
                else "No recipients configured (EMAIL_RECIPIENTS empty)"
            )
            job_log.job_details = {
                "mode": mode,
                "count": len(papers),
                "max_paper_id": max_paper_id,
                "watermark_advanced": False,
            }
            logger.error("Digest send failed; watermark not advanced")
            return

        job_log.status = "SUCCESS"
        job_log.job_details = {
            "mode": mode,
            "count": len(papers),
            "max_paper_id": max_paper_id,
        }
        if not papers:
            job_log.error_message = "No new cs.AI papers since last digest"
        logger.info(
            "Digest complete: %d papers (mode=%s, watermark=%s)",
            len(papers),
            mode,
            max_paper_id,
        )
    except Exception as e:
        logger.exception("Failed to send daily digest")
        job_log.status = "FAILED"
        job_log.error_message = str(e)
    finally:
        job_log.end_time = datetime.datetime.utcnow()
        db.commit()
        db.close()


def run_daily_poll_and_digest():
    """09:00 IST entry point: poll arXiv, then send the digest.

    The digest runs even when the poll raises — papers already in the DB
    still deserve their email, and the watermark guarantees anything the
    failed poll would have ingested lands in the next digest. Kept out of
    ``process_papers`` because scripts/seed_db.py calls it directly and
    must not send email.
    """
    try:
        process_papers()
    except Exception:
        logger.exception("Daily poll raised — sending digest anyway")
    send_daily_email_digest()


def run_batch_summarization():
    logger.info("Starting Daily Batch Summarization Job...")
    db: Session = SessionLocal()
    try:
        batch_id = batch_service.create_daily_batch_job(db)
        if batch_id:
            logger.info(f"Batch Job Created: {batch_id}")
    except Exception as e:
        logger.error(f"Batch Job Failed: {e}")
    finally:
        db.close()

def rescore_reading_queues():
    """Daily job: sync library → queue, then rescore all users."""
    logger.info("Starting reading queue rescore...")
    db: Session = SessionLocal()

    job_log = JobLog(
        job_name="reading_queue_rescore",
        status="RUNNING",
        start_time=datetime.datetime.utcnow(),
    )
    db.add(job_log)
    db.commit()

    try:
        # For each user, sync and rescore
        users = db.query(models.User).all()
        total_added = 0
        total_removed = 0
        total_rescored = 0

        total_discovered = 0
        for user in users:
            added, removed = rqs.sync_queue_from_library(
                db, user_id=user.id
            )
            rescored = rqs.rescore_queue(db, user_id=user.id)
            discovered = rqs.run_discovery(
                db, user_id=user.id, since_days=7
            )
            total_added += added
            total_removed += removed
            total_rescored += rescored
            total_discovered += discovered

        job_log.status = "SUCCESS"
        job_log.job_details = {
            "users": len(users),
            "added": total_added,
            "removed": total_removed,
            "rescored": total_rescored,
            "discovered": total_discovered,
        }
        logger.info(
            "Queue rescore complete: %d users, %d rescored",
            len(users),
            total_rescored,
        )
    except Exception as e:
        logger.error("Queue rescore failed: %s", e)
        job_log.status = "FAILED"
        job_log.error_message = str(e)
    finally:
        job_log.end_time = datetime.datetime.utcnow()
        db.commit()
        db.close()


def cleanup_query_embedding_cache():
    """Weekly job: remove query embeddings unused for 30+ days."""
    logger.info("Starting query embedding cache cleanup...")
    db: Session = SessionLocal()
    try:
        deleted = query_cache.cleanup_stale(db, max_age_days=30)
        logger.info("Query cache cleanup complete: %d entries removed", deleted)
    except Exception as e:
        logger.error("Query cache cleanup failed: %s", e)
    finally:
        db.close()


scheduler = BackgroundScheduler()

ist_timezone = pytz.timezone('Asia/Kolkata')

# 1. Poll + Digest Job: Daily at 09:00 IST.
#    arXiv announces once per day at 20:00 ET. Correct conversion:
#    20:00 EDT (summer) → 05:30 IST next day; 20:00 EST (winter) →
#    06:30 IST next day. 09:00 IST sits ~2.5h after the EST announce
#    and ~3.5h after the EDT announce — safely past both DST windows.
#    The digest runs in the same wrapper right after the poll, so
#    freshly ingested papers go out the same morning. (The old separate
#    10:00 digest job selected papers by submission date and raced the
#    poll, which dropped late-arriving papers.)
scheduler.add_job(
    run_daily_poll_and_digest,
    CronTrigger(hour=9, minute=0, timezone=ist_timezone),
)

# 2. Batch Summarization Job: Daily at 11:00 PM IST
scheduler.add_job(run_batch_summarization, CronTrigger(hour=23, minute=0, timezone=ist_timezone))

# 3. Reading Queue Rescore: Daily at 2:00 AM IST (20:30 UTC)
scheduler.add_job(
    rescore_reading_queues,
    CronTrigger(hour=2, minute=0, timezone=ist_timezone),
)

# 4. Query Cache Cleanup: Weekly Sunday at 3:00 AM IST
scheduler.add_job(
    cleanup_query_embedding_cache,
    CronTrigger(day_of_week="sun", hour=3, minute=0, timezone=ist_timezone),
)

def start_scheduler():
    # Suppress scheduled jobs during a deploy's migration window. deploy.sh
    # sets MIGRATING=1 while it brings up backend alongside the DB to run
    # DDL — we don't want the scheduler to fire process_papers / batch
    # summarization / queue rescore in that window because those jobs
    # INSERT/UPDATE papers and would re-introduce the same ACCESS EXCLUSIVE
    # lock contention that hangs ALTER TABLE migrations.
    if os.getenv("MIGRATING") == "1":
        logger.info("MIGRATING=1 — skipping scheduler startup")
        return
    # Non-production stacks (e.g. staging) share the host's egress IP with
    # prod. Two stacks polling arXiv on the same cron schedule double the
    # request rate from one IP and trip arXiv's HTTP 429 rate limiter, which
    # stalls ingestion on *both* stacks. Set DISABLE_SCHEDULER=1 on every
    # non-prod stack so only one scheduler hits arXiv.
    if os.getenv("DISABLE_SCHEDULER") == "1":
        logger.info("DISABLE_SCHEDULER=1 — skipping scheduler startup")
        return
    scheduler.start()
