import logging
from datetime import date, datetime
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Paper, UserConfig
from services.arxiv_service import arxiv_service
from ingestion import process_paper_entry
import time
import argparse

logger = logging.getLogger("ManualTrigger")

def backfill_papers(start_date: date, end_date: date, max_results: int = 800) -> None:
    logger.info(f"🚀 Starting Manual Trigger for {start_date} to {end_date}")
    
    db: Session = SessionLocal()
    success_count = 0
    failure_count = 0
    
    try:
        # Get Categories
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

        for category in categories:
            logger.info(f"Fetching papers for category: {category}")
            papers = arxiv_service.fetch_papers(
                query=f"cat:{category}", 
                max_results=max_results
            ) 
            
            # Pre-fetch existing IDs to avoid N+1 queries
            fetched_arxiv_ids = [p['arxiv_id'] for p in papers]
            existing_papers = db.query(Paper.arxiv_id).filter(Paper.arxiv_id.in_(fetched_arxiv_ids)).all()
            existing_ids = {p.arxiv_id for p in existing_papers}
            
            for paper_data in papers:
                pub_date = paper_data['published_date'].date()
                
                if not (start_date <= pub_date <= end_date):
                    continue
                
                if paper_data['arxiv_id'] not in existing_ids:
                    logger.info(f"Found missing paper: {paper_data['title']} (Pub: {pub_date})")
                    try:
                        # Ingest
                        process_paper_entry(db, paper_data)
                        success_count += 1
                    except Exception as e:
                        logger.error(f"Failed to ingest {paper_data['arxiv_id']}: {e}")
                        failure_count += 1
                    time.sleep(1)  # small rate limit
                else:
                    logger.debug(f"Paper already exists: {paper_data['arxiv_id']}")

    except Exception as e:
        logger.error(f"Fatal error in manual trigger setup/fetch: {e}")
        raise
    finally:
        logger.info(f"Backfill Complete. Success: {success_count}, Failures: {failure_count}")
        db.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Backfill missing papers from arXiv.")
    parser.add_argument("--start", type=str, required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--max-results", type=int, default=800, help="Max results per category to fetch from arXiv")
    
    args = parser.parse_args()
    
    start_d = datetime.strptime(args.start, "%Y-%m-%d").date()
    end_d = datetime.strptime(args.end, "%Y-%m-%d").date()
    
    backfill_papers(start_d, end_d, args.max_results)
