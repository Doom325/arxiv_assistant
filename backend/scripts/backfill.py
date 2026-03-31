import os
import re
import datetime
import logging
import time
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Paper
from ingestion import process_paper_entry
from services.arxiv_service import arxiv_service
import arxiv

from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PDF_DIR = settings.PDF_SAVE_DIR
CUTOFF_DATE = datetime.date(2026, 2, 3)

def get_arxiv_id_from_filename(filename):
    # Matches 2312.12345 or 2312.12345v1
    match = re.search(r"(\d{4}\.\d{4,5})(v\d+)?", filename)
    if match:
        # Standardize to base ID for API lookup usually
        return match.group(1) 
    return None

def ingest_local_files(db: Session):
    logger.info("PHASE 1: Ingesting existing local PDFs...")
    if not os.path.exists(PDF_DIR):
        logger.warning(f"{PDF_DIR} does not exist. Skipping Phase 1.")
        return

    files = [f for f in os.listdir(PDF_DIR) if f.endswith(".pdf") and not f.startswith("._")]
    local_map = {}
    for f in files:
        aid = get_arxiv_id_from_filename(f)
        if aid:
            local_map[aid] = f

    logger.info(f"Found {len(local_map)} local PDFs.")
    
    # 2. Check DB for missing ones - Bulk optimization
    logger.info("Checking database for existing papers...")
    # Fetch all base IDs from DB to avoid N^2 loop
    existing_base_ids = {id_[0].split('v')[0] for id_ in db.query(Paper.arxiv_id).all()}
    
    ids_to_fetch = []
    for aid in local_map.keys():
        if aid not in existing_base_ids:
            ids_to_fetch.append(aid)

    if not ids_to_fetch:
        logger.info("All local PDFs are already in the database.")
        return

    logger.info(f"Found {len(ids_to_fetch)} local PDFs not in DB. Fetching metadata...")

    # 3. Batch fetch metadata from Arxiv
    # Arxiv API allows searching by ID list. Process in batches of 200 max.
    batch_size = 200
    for i in range(0, len(ids_to_fetch), batch_size):
        batch_ids = ids_to_fetch[i : i + batch_size]
        logger.info(f"Fetching metadata for batch {i//batch_size + 1} ({len(batch_ids)} papers)...")
        
        try:
            search = arxiv.Search(id_list=batch_ids)
            results = list(arxiv_service.client.results(search))
            
            for result in results:
                arxiv_id = result.entry_id.split('/')[-1]
                logger.info(f"Ingesting local paper metadata: {arxiv_id}")
                
                paper_data = {
                    "arxiv_id": arxiv_id,
                    "title": result.title,
                    "authors": [author.name for author in result.authors],
                    "summary": result.summary,
                    "published_date": result.published.date(),
                    "pdf_url": result.pdf_url,
                    "category": result.primary_category
                }
                
                # Use skip_ai=True to just create DB entry + ensure PDF is there (it is)
                process_paper_entry(db, paper_data, skip_ai=True)
            
            # Commit and clear session to free memory
            db.commit()
            db.expunge_all()
                
            time.sleep(2) # Be nice to API

        except Exception as e:
            logger.error(f"Error fetching batch metadata: {e}")


def date_based_fetch(db: Session):
    logger.info(f"PHASE 2: Fetching new papers since {CUTOFF_DATE}...")
    
    # We can expand this list or fetch from users.
    categories = ["cs.AI", "cs.LG", "cs.CL", "cs.CV", "cs.RO", "cs.MA", "cs.NE", "cs.IR", "cs.SI", "cs.HC", "cs.CY"] 
    
    for category in categories:
        logger.info(f"Scanning category: {category}")
        
        search = arxiv.Search(
            query=f"cat:{category}",
            max_results=1000, 
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending
        )
        
        processed_count = 0
        
        for result in arxiv_service.client.results(search):
            paper_date = result.published.date()
            
            if paper_date < CUTOFF_DATE:
                logger.info(f"Reached cutoff date {paper_date} for {category}. Stopping category.")
                break
                
            arxiv_id = result.entry_id.split('/')[-1]
            base_id = arxiv_id.split('v')[0] 
            
            # Check DB (Phase 1 might have just added it)
            existing = db.query(Paper).filter(Paper.arxiv_id.like(f"{base_id}%")).first()
            if existing:
                continue
                
            logger.info(f"Downloading NEW paper: {arxiv_id} ({paper_date})")
            
            paper_data = {
                    "arxiv_id": arxiv_id,
                    "title": result.title,
                    "authors": [author.name for author in result.authors],
                    "summary": result.summary,
                    "published_date": result.published.date(),
                    "pdf_url": result.pdf_url,
                    "category": result.primary_category
            }
            
            try:
                # This will download PDF and create DB entry. No AI.
                process_paper_entry(db, paper_data, skip_ai=True)
                processed_count += 1
                
                # Minimal throttle since we aren't doing heavy AI
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Failed to process {arxiv_id}: {e}")
                
        logger.info(f"Finished category {category}. Added {processed_count} papers.")


def run_comprehensive_backfill():
    db: Session = SessionLocal()
    try:
        ingest_local_files(db)
        date_based_fetch(db)
    finally:
        db.close()
    logger.info("Comprehensive Backfill Complete.")

if __name__ == "__main__":
    run_comprehensive_backfill()
