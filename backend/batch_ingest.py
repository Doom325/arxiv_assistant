import argparse
import logging
from datetime import datetime, timedelta
from database import SessionLocal
from models import UserConfig
from services.arxiv_service import arxiv_service
from ingestion import process_paper_entry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def batch_ingest(days: int = 0, years: int = 0):
    # Handle None values from argparse
    days = days or 0
    years = years or 0
    db = SessionLocal()
    try:
        # Calculate start date
        if years > 0:
            start_date = datetime.now() - timedelta(days=years*365)
        else:
            start_date = datetime.now() - timedelta(days=days)
            
        logger.info(f"Starting batch ingestion from {start_date.date()}...")

        # Get categories
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
            # Note: arXiv API doesn't support strict date filtering in the search query easily 
            # without using specific syntax like submittedDate:[202301010000 TO 202301312359]
            # For simplicity in this batch script, we will fetch a larger number of results 
            # and filter client-side if needed, or rely on the fact that we sort by submittedDate descending.
            # A more robust implementation would construct the date range query.
            
            # Constructing date range query for arXiv
            # Format: YYYYMMDDHHMM
            start_str = start_date.strftime("%Y%m%d0000")
            end_str = datetime.now().strftime("%Y%m%d2359")
            query = f"cat:{category} AND submittedDate:[{start_str} TO {end_str}]"
            
            # Fetch papers (adjust max_results as needed, maybe 50-100 per category for batch)
            papers = arxiv_service.fetch_papers(query=query, max_results=20) 
            
            logger.info(f"Found {len(papers)} papers for {category}")
            
            for paper_data in papers:
                process_paper_entry(db, paper_data)

        logger.info("Batch ingestion complete.")

    except Exception as e:
        logger.error(f"Error in batch ingestion: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch ingest arXiv papers.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--days", type=int, help="Number of past days to fetch")
    group.add_argument("--years", type=int, help="Number of past years to fetch")
    
    args = parser.parse_args()
    
    batch_ingest(days=args.days, years=args.years)
