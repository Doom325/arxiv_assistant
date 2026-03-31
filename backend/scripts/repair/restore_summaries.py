import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import logging
from database import SessionLocal
from models import Paper
from services.summarization_service import summarization_service
from services.arxiv_service import arxiv_service
import os
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def restore_summaries():
    db = SessionLocal()
    papers = db.query(Paper).filter(Paper.generated_summary.is_(None)).all()
    
    logger.info(f"Found {len(papers)} papers needing summaries.")
    
    for paper in papers:
        logger.info(f"Summarizing {paper.arxiv_id}...")
        try:
            # 1. Locate PDF
            # Use same logic as router or worker
            # Assuming worker already downloaded/restored to PDF_DIR
            pdf_path = f"/app/data/pdfs/{paper.arxiv_id}.pdf" # Explicit path based on restoration
            if not os.path.exists(pdf_path):
                 # Fallback to standard path
                 pdf_path = f"/app/data/{paper.arxiv_id}.pdf"
            
            if not os.path.exists(pdf_path):
                # Try download if missing (shouldn't happen for restored ones)
                logger.warning(f"PDF missing for {paper.arxiv_id}, skipping.")
                continue

            # 2. Generate
            summary = summarization_service.generate_summary(pdf_path)
            
            # 3. Save
            paper.generated_summary = summary
            db.commit()
            logger.info("Success.")
            
        except Exception as e:
            logger.error(f"Failed to summarize {paper.arxiv_id}: {e}")
            
    db.close()
    logger.info("Summary restoration complete.")

if __name__ == "__main__":
    restore_summaries()
