import os
import logging
import arxiv
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Paper
from services.arxiv_service import arxiv_service
from services.llm_service import llm_service, embedding_service
from services.summarization_service import summarization_service
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PDF_DIR = "data/pdfs"

def get_existing_arxiv_ids(db: Session):
    """Get set of arxiv_ids already in the database."""
    papers = db.query(Paper.arxiv_id).all()
    return {p[0] for p in papers}

def process_batch(db: Session, batch_ids: list):
    """Process a batch of arXiv IDs."""
    if not batch_ids:
        return

    logger.info(f"Fetching metadata for {len(batch_ids)} papers...")
    try:
        search = arxiv.Search(id_list=batch_ids)
        results = list(search.results())
    except Exception as e:
        logger.error(f"Failed to fetch metadata from arXiv: {e}")
        return

    # Create a map for quick lookup
    metadata_map = {r.get_short_id(): r for r in results}
    
    # Also handle versioned IDs if get_short_id strips them or vice versa
    # arxiv library result.entry_id usually is full URL, result.get_short_id() is like 2101.12345v1
    
    for arxiv_id in batch_ids:
        # Find metadata
        # Try exact match first
        paper_meta = metadata_map.get(arxiv_id)
        
        # If not found, try stripping version or adding version?
        # The batch_ids come from filenames which might have v1.
        # arxiv.Search expects IDs.
        
        if not paper_meta:
            # Try to find by matching base ID
            base_id = arxiv_id.split('v')[0]
            for k, v in metadata_map.items():
                if k.startswith(base_id):
                    paper_meta = v
                    break
        
        if not paper_meta:
            logger.warning(f"Metadata not found for {arxiv_id}, skipping.")
            continue

        try:
            logger.info(f"Processing {arxiv_id}...")
            pdf_path = os.path.join(PDF_DIR, f"{arxiv_id}.pdf")
            
            if not os.path.exists(pdf_path):
                logger.warning(f"PDF missing for {arxiv_id} at {pdf_path}")
                continue

            # 1. Extract Text
            text = arxiv_service.extract_text(pdf_path)
            if not text:
                logger.warning(f"Could not extract text for {arxiv_id}")
                continue

            # 2. Generate Embedding
            embedding = embedding_service.generate_embedding(text)

            # 3. Generate Summary
            # We use the summarization service (Gemma)
            # Note: This is slow, so maybe we make it optional or just do it?
            # User requested "along with summary".
            # summary = summarization_service.generate_summary(pdf_path)
            summary = None # Skip AI summary for bulk ingest

            # 4. Save to DB
            new_paper = Paper(
                arxiv_id=arxiv_id,
                title=paper_meta.title,
                authors=", ".join([a.name for a in paper_meta.authors]),
                summary=paper_meta.summary, # Abstract
                generated_summary=summary, # AI Summary
                published_date=paper_meta.published.date(),
                category=paper_meta.primary_category,
                pdf_url=paper_meta.pdf_url,
                embedding=embedding
            )
            db.add(new_paper)
            db.commit()
            logger.info(f"Successfully saved {arxiv_id}")

        except Exception as e:
            logger.error(f"Failed to process {arxiv_id}: {e}")
            db.rollback()

def main():
    if not os.path.exists(PDF_DIR):
        logger.error(f"PDF directory {PDF_DIR} does not exist.")
        return

    db = SessionLocal()
    try:
        # 1. Get all PDF filenames
        files = [f for f in os.listdir(PDF_DIR) if f.endswith(".pdf")]
        all_ids = [f.replace(".pdf", "") for f in files]
        logger.info(f"Found {len(all_ids)} PDFs in {PDF_DIR}")

        # 2. Filter out existing
        existing_ids = get_existing_arxiv_ids(db)
        to_process = [pid for pid in all_ids if pid not in existing_ids]
        logger.info(f"Found {len(to_process)} papers to process.")

        # 3. Process in batches
        BATCH_SIZE = 20 # arXiv API limit is usually around 100, but let's be safe and also consider processing time
        
        for i in range(0, len(to_process), BATCH_SIZE):
            batch = to_process[i:i+BATCH_SIZE]
            process_batch(db, batch)
            
            # Sleep a bit to be nice to arXiv API?
            # processing takes time so maybe not needed, but good practice.
            # time.sleep(1) 

    finally:
        db.close()

if __name__ == "__main__":
    main()
