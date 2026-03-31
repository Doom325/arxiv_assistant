import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import logging
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Paper
from services.email_service import email_service
from config import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PartialDigest")

# Explicit port 5434
DB_URL = "postgresql://user:password@localhost:5434/arxiv_db"

def send_partial():
    engine = create_engine(DB_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        target_dates = [date(2025, 12, 12), date(2025, 12, 11)]
        
        # Get all papers for the date range
        papers = db.query(Paper).filter(Paper.published_date.in_(target_dates)).all()
        
        # Filter: ONLY those with summaries
        ready_papers = [p for p in papers if p.generated_summary]
        
        logger.info(f"Target Dates: {target_dates}")
        logger.info(f"Total Papers Found: {len(papers)}")
        logger.info(f"Papers with Summaries (Ready to Send): {len(ready_papers)}")
        
        if ready_papers:
            # Sort by date
            ready_papers.sort(key=lambda x: x.published_date, reverse=True)
            
            logger.info(f"Sending Partial Email Digest with {len(ready_papers)} papers...")
            
            for email in settings.RECIPIENT_LIST:
                 email_service.send_daily_digest(email, ready_papers)
                 logger.info(f"✅ Sent partial digest to {email}")
        else:
            logger.warning("No papers with summaries found to send.")

    except Exception as e:
        logger.error(f"Failed to send partial digest: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    send_partial()
