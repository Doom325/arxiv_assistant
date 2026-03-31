import logging
import time
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Paper, UserConfig
from services.arxiv_service import arxiv_service
from ingestion import process_paper_entry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def catchup_papers():
    logger.info("Starting Smart Catchup...")
    db: Session = SessionLocal()
    
    try:
        # Get categories
        configs = db.query(UserConfig).all()
        categories = set()
        for config in configs:
            if config.categories:
                categories.update(config.categories)
        
        if not categories:
            categories = {
                "cs.AI", "cs.LG", "cs.CL", "cs.CV", "cs.RO"
            } # Default fallback

        for category in categories:
            logger.info(f"Catching up on category: {category}")
            
            # Fetch generic search, sorted by date descending
            import arxiv
            search = arxiv.Search(
                query=f"cat:{category}",
                max_results=100, # Safety limit, but loop breaks early
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending
            )
            
            new_count = 0
            # Use the client to iterate
            # arxiv_service.client is available
            
            for result in arxiv_service.client.results(search):
                arxiv_id = result.entry_id.split('/')[-1]
                
                # Check if exists in DB
                # Note: Filenames often have v1, API ID might not. Check both?
                # Usually API ID is versionless or versioned. 
                # Let's check fuzzy or specific. Use the exact ID from API first.
                
                existing = db.query(Paper).filter(Paper.arxiv_id.like(f"{arxiv_id}%")).first()
                if existing:
                    logger.info(f"Found existing paper {arxiv_id} (DB: {existing.arxiv_id}). Catchup for {category} complete.")
                    break
                
                # New paper! Process it.
                paper_data = {
                    "arxiv_id": arxiv_id,
                    "title": result.title,
                    "authors": [author.name for author in result.authors],
                    "summary": result.summary,
                    "published_date": result.published.date(),
                    "pdf_url": result.pdf_url,
                    "category": result.primary_category
                }
                
                process_paper_entry(db, paper_data)
                new_count += 1
                
                # Thermal constraint
                time.sleep(10)
            
            logger.info(f"Category {category}: Added {new_count} new papers.")
            
    except Exception as e:
        logger.error(f"Error in catchup: {e}")
    finally:
        db.close()
        logger.info("Smart Catchup Finished.")

if __name__ == "__main__":
    catchup_papers()
