import os
import logging
from sqlalchemy.orm import Session
from models import Paper
from services.arxiv_service import arxiv_service
from services.llm_service import llm_service

from config import settings

logger = logging.getLogger(__name__)

def process_paper_entry(db: Session, paper_data: dict, skip_ai: bool = False):
    """
    Processes a single paper entry: checks for existence, downloads PDF, 
    extracts text, summarizes, embeds, and saves to DB.
    """
    existing_paper = db.query(Paper).filter(Paper.arxiv_id == paper_data['arxiv_id']).first()
    if existing_paper:
        return
    
    logger.info(f"Processing new paper: {paper_data['title']}")
    
    try:
        # PURE METADATA INGESTION
        # We do not download or process here. That is for the Worker.
        
        # Save to DB
        new_paper = Paper(
            arxiv_id=paper_data['arxiv_id'],
            title=paper_data['title'],
            authors=paper_data['authors'],
            summary=paper_data.get('summary'), # Store Arxiv Abstract as metadata
            published_date=paper_data['published_date'],
            updated_date=paper_data.get('updated_date'),
            category=paper_data['category'],
            pdf_url=paper_data['pdf_url'],
            is_downloaded=False,
            generated_summary=None
        )
        db.add(new_paper)
        db.commit()
        logger.info(f"Successfully saved paper: {paper_data['arxiv_id']}")
        return new_paper

    except Exception as e:
        # Check for integrity error (duplicate)
        if "UniqueViolation" in str(e) or "duplicate key" in str(e):
            logger.warning(f"Paper {paper_data['arxiv_id']} already exists (race condition), skipping.")
            db.rollback()
            return
            
        logger.error(f"Failed to process paper {paper_data['arxiv_id']}: {e}")
        db.rollback()
        # Clean up partial file if needed, though keeping it might be useful for retry
