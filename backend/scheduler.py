import datetime
import json
import logging

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
from poll_constants import INITIAL_BACKFILL_DAYS, REPOLL_OVERLAP_DAYS
from services.arxiv_service import arxiv_service
from services.batch_service import batch_service
from services.email_service import email_service
from services.summarization_service import summarization_service
from services import reading_queue_service as rqs
from services.query_embedding_cache import query_cache

DEFAULT_CATEGORIES = {
    "cs.AI", "cs.LG", "cs.CL", "cs.CV", "cs.RO",
    "cs.MA", "cs.NE", "cs.IR", "cs.SI", "cs.HC", "cs.CY",
}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    """Separate job for sending emails once a day."""
    logger.info("Preparing Daily Email Digest...")
    db: Session = SessionLocal()
    
    # Track this job too!
    job_log = JobLog(
        job_name="email_digest",
        status="RUNNING",
        start_time=datetime.datetime.utcnow()
    )
    db.add(job_log)
    db.commit()
    
    try:
        # 1. Determine Date Range (Yesterday IST)
        ist = pytz.timezone('Asia/Kolkata')
        yesterday = datetime.datetime.now(ist).date() - datetime.timedelta(days=1)
        
        logger.info(f"Generating digest for date: {yesterday}")
        
        # 2. Fetch papers from LOCAL DB
        # Restrict to CS.AI category as requested by user
        # Also use a date range to be safe with datetime comparisons
        papers = db.query(Paper).filter(
            func.date(Paper.published_date) == yesterday,
            Paper.category == "cs.AI"
        ).all()
        
        digest_count = len(papers)
        
        if papers:
            for email in settings.RECIPIENT_LIST:
                email_service.send_daily_digest(email, papers)
                logger.info(f"Sent daily digest to {email}")
        
        job_log.status = "SUCCESS"
        job_log.job_details = {"date": str(yesterday), "count": digest_count}
        if not papers:
            job_log.error_message = "No papers found for date"
                
    except Exception as e:
        logger.error(f"Failed to send daily digest: {e}")
        job_log.status = "FAILED"
        job_log.error_message = str(e)
    finally:
        job_log.end_time = datetime.datetime.utcnow()
        db.commit()
        db.close()

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

# 1. Ingestion Job: Daily at 09:00 IST.
#    arXiv announces once per day at 20:00 ET. Correct conversion:
#    20:00 EDT (summer) → 05:30 IST next day; 20:00 EST (winter) →
#    06:30 IST next day. 09:00 IST sits ~2.5h after the EST announce
#    and ~3.5h after the EDT announce — safely past both DST windows.
#    Must run before the email-digest job below so yesterday's papers
#    are ingested first.
scheduler.add_job(
    process_papers,
    CronTrigger(hour=9, minute=0, timezone=ist_timezone),
)

# 2. Email Job: Daily at 10:00 IST.
#    Runs one hour after the 09:00 IST paper poll — ordering matters
#    because the digest reads yesterday's cs.AI papers from the local
#    DB, which the poll is responsible for populating.
scheduler.add_job(
    send_daily_email_digest,
    CronTrigger(hour=10, minute=0, timezone=ist_timezone),
)

# 3. Batch Summarization Job: Daily at 11:00 PM IST
scheduler.add_job(run_batch_summarization, CronTrigger(hour=23, minute=0, timezone=ist_timezone))

# 4. Reading Queue Rescore: Daily at 2:00 AM IST (20:30 UTC)
scheduler.add_job(
    rescore_reading_queues,
    CronTrigger(hour=2, minute=0, timezone=ist_timezone),
)

# 5. Query Cache Cleanup: Weekly Sunday at 3:00 AM IST
scheduler.add_job(
    cleanup_query_embedding_cache,
    CronTrigger(day_of_week="sun", hour=3, minute=0, timezone=ist_timezone),
)

def start_scheduler():
    scheduler.start()
