import datetime
import json
import logging

import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import func
from sqlalchemy.orm import Session

from config import settings
from database import SessionLocal
from ingestion import process_paper_entry
import models
from models import JobLog, Paper, UserConfig
from services.arxiv_service import arxiv_service
from services.batch_service import batch_service
from services.email_service import email_service
from services.summarization_service import summarization_service
from services import reading_queue_service as rqs
from services.query_embedding_cache import query_cache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_papers():
    logger.info("Starting periodic paper poll...")
    db: Session = SessionLocal()
    
    # 1. Create Job Log
    job_log = JobLog(
        job_name="scheduler_poll",
        status="RUNNING",
        start_time=datetime.datetime.utcnow(),
        job_details={}
    )
    db.add(job_log)
    db.commit()
    db.refresh(job_log)
    
    new_papers_count = 0
    errors = []
    
    try:
        # Get all unique categories
        configs = db.query(UserConfig).all()
        categories = set()
        for config in configs:
            if config.categories:
                categories.update(config.categories)
        
        if not categories:
            categories = {
                "cs.AI", "cs.LG", "cs.CL", "cs.CV", "cs.RO", 
                "cs.MA", "cs.NE", "cs.IR", "cs.SI", "cs.HC", "cs.CY"
            }

        logger.info(f"Polling categories: {categories}")

        for category in categories:
            try:
                # Fetch recent papers (100 is enough for 15-min window)
                # We fetch "submittedDate" effectively via API ordering
                papers = arxiv_service.fetch_papers(query=f"cat:{category}", max_results=50) 
                
                for paper_data in papers:
                    # Ingestion: stored in DB, status will be default (is_downloaded=False)
                    # This effectively adds it to the "Processing Queue"
                    paper = process_paper_entry(db, paper_data)
                    
                    if paper:
                        new_papers_count += 1
                        
            except Exception as cat_err:
                logger.error(f"Error fetching {category}: {cat_err}")
                errors.append(f"{category}: {str(cat_err)}")

        job_log.status = "SUCCESS"
        if errors:
            job_log.status = "WARNING"
            
        job_log.job_details = {
            "new_papers": new_papers_count,
            "errors": errors
        }
        logger.info(f"Polling complete. New Papers: {new_papers_count}")

    except Exception as e:
        logger.error(f"Error in polling: {e}")
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

# 1. Ingestion Job: Every 15 minutes
scheduler.add_job(process_papers, IntervalTrigger(minutes=15))

# 2. Email Job: Daily at 6:00 AM IST
ist_timezone = pytz.timezone('Asia/Kolkata')
scheduler.add_job(send_daily_email_digest, CronTrigger(hour=6, minute=0, timezone=ist_timezone))

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
