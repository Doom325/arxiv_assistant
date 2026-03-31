import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import logging
from datetime import date
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Paper, UserConfig
from services.arxiv_service import arxiv_service
from ingestion import process_paper_entry
from services.email_service import email_service
from services.summarization_service import summarization_service
from config import settings
import time
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ManualTrigger")

def run_friday_digest():
    TARGET_DATE = date(2025, 12, 12) # Friday
    logger.info(f"🚀 Starting Manual Trigger for Friday: {TARGET_DATE}")
    
    db: Session = SessionLocal()
    new_papers = []
    
    try:
        # Get Categories (Same as scheduler)
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
            # Fetch a bit more to ensure we hit the date
            papers = arxiv_service.fetch_papers(query=f"cat:{category}", max_results=50) 
            
            for paper_data in papers:
                pub_date = paper_data['published_date']
                
                # STRICT DATE FILTER for Friday (or Thursday late submissions)
                target_dates = [date(2025, 12, 12), date(2025, 12, 11)]
                if pub_date not in target_dates:
                    continue
                
                logger.info(f"Found Paper: {paper_data['title']} ({paper_data['arxiv_id']})")
                
                # Ingest/Get Paper
                paper = process_paper_entry(db, paper_data)
                
                if paper:
                    # Generate Summary if missing
                    if not paper.generated_summary:
                        try:
                            logger.info(f"Generating summary for {paper.arxiv_id}...")
                            
                            # Locate PDF (standard path or v1)
                            pdf_path = f"/Volumes/External/PDFs/Arxiv Assistant/{paper.arxiv_id}.pdf"
                            if not os.path.exists(pdf_path):
                                 pdf_path = f"/Volumes/External/PDFs/Arxiv Assistant/{paper.arxiv_id}v1.pdf"
                            
                            if os.path.exists(pdf_path):
                                summary = summarization_service.generate_summary(pdf_path)
                                paper.generated_summary = summary
                                db.commit()
                                logger.info(f"✅ Summary generated for {paper.arxiv_id}")
                                # Brief cool-down to be nice to the poor Mac CPU?
                                time.sleep(2)
                            else:
                                logger.warning(f"PDF not found for {paper.arxiv_id}, skipping summary.")
                                # Try to fallback to what scheduler does? 
                                # Scheduler usually assumes ingestion downloaded it. 
                                # Since we have the MacWorker running, maybe it downloaded it?
                                pass
                                
                        except Exception as e:
                            logger.error(f"Failed to generate summary for {paper.arxiv_id}: {e}")
                    
                    new_papers.append(paper)
        
        # Deduplicate
        unique_papers = {p.arxiv_id: p for p in new_papers}.values()
        sorted_papers = sorted(unique_papers, key=lambda x: x.published_date, reverse=True)
        
        logger.info(f"Total Papers for Digest: {len(sorted_papers)}")
        
        if sorted_papers:
            logger.info("Sending Email Digest...")
            # Send to Env Recipients
            for email in settings.RECIPIENT_LIST:
                email_service.send_daily_digest(email, list(sorted_papers))
                logger.info(f"Sent to {email}")
        else:
            logger.warning("No papers found for this date. Check fetch parameters?")

    except Exception as e:
        logger.error(f"Error in manual trigger: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run_friday_digest()
