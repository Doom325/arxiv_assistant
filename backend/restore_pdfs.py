
import os
import re
import logging
import arxiv
from database import SessionLocal
from models import Paper
from config import settings
from datetime import datetime
import time

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def chunk_list(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def restore_papers():
    db = SessionLocal()
    # Updated to point to /app/data directly as per new docker-compose mapping
    pdf_dir = settings.PDF_SAVE_DIR 
    
    if not os.path.exists(pdf_dir):
        logger.error(f"PDF Directory {pdf_dir} not found!")
        return

    logger.info(f"Scanning {pdf_dir} for PDFs...")
    
    all_files = [f for f in os.listdir(pdf_dir) if f.endswith(".pdf") and not f.startswith("._")]
    total_files = len(all_files)
    logger.info(f"Found {total_files} PDF files.")
    
    # Filter out papers already in DB
    existing_ids = {p.arxiv_id for p in db.query(Paper.arxiv_id).all()}
    
    files_to_process = []
    for f in all_files:
        arxiv_id = f.replace(".pdf", "")
        # Remove version suffix if needed for matching only (API handles it)
        # But we store exact ID usually.
        if arxiv_id not in existing_ids:
            files_to_process.append(arxiv_id)
            
    logger.info(f"Found {len(files_to_process)} new papers to restore.")
    
    restored_count = 0
    batch_size = 100
    
    for i, batch_ids in enumerate(chunk_list(files_to_process, batch_size)):
        logger.info(f"Processing batch {i+1} ({len(batch_ids)} papers)...")
        try:
            # Batch fetch from Arxiv
            search = arxiv.Search(id_list=batch_ids, max_results=len(batch_ids))
            results = list(search.results())
            
            # Map results by ID for easy lookup
            # Arxiv API might return versioned or unversioned IDs.
            # We need to map back to our requested ID.
            result_map = {}
            for r in results:
                # result.entry_id is like http://arxiv.org/abs/2101.00001v1
                # extract ID part
                r_id = r.entry_id.split('/')[-1]
                # Handle version mismatch
                short_id = r_id.split('v')[0]
                result_map[r_id] = r
                result_map[short_id] = r

            for requested_id in batch_ids:
                # Try finding exact match or versionless match
                result = result_map.get(requested_id)
                if not result:
                     # Attempt version stripping
                     short_req_id = requested_id.split('v')[0]
                     result = result_map.get(short_req_id)
                
                if result:
                    new_paper = Paper(
                        arxiv_id=requested_id, # Keep the ID from filename
                        title=result.title,
                        authors=[a.name for a in result.authors], # Save as List[str] for JSON compatibility
                        summary=result.summary,
                        published_date=result.published.date(),
                        category=result.primary_category,
                        pdf_url=result.pdf_url,
                        is_downloaded=True,
                        extracted_abstract=None,
                        generated_summary=None
                    )
                    db.add(new_paper)
                    restored_count += 1
                else:
                    logger.warning(f"Metadata not found for {requested_id}")

            db.commit()
            logger.info(f"Batch complete. Total restored: {restored_count}")
            time.sleep(1) # Polite delay
            
        except Exception as e:
            logger.error(f"Batch failed: {e}")
            db.rollback()
            
    db.close()
    logger.info(f"Restoration Complete. Successfully restored {restored_count} papers.")

if __name__ == "__main__":
    restore_papers()
