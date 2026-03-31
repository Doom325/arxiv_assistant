
import os
import json
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from batch_embed_manager import BatchEmbedManager
from config import settings
from models import Paper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Consolidator")

# Database Setup
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def consolidate():
    manager = BatchEmbedManager()
    db = SessionLocal()
    try:
        # Get all papers missing embeddings
        missing_ids = [row[0] for row in db.execute(text(
            "SELECT id FROM papers WHERE embedding IS NULL"
        )).fetchall()]
        
        total = len(missing_ids)
        logger.info(f"Total papers missing embeddings: {total}")
        
        if total == 0:
            logger.info("No papers missing embeddings. Done.")
            return

        # Split into 2 batches
        midpoint = total // 2
        batch_1_ids = missing_ids[:midpoint]
        batch_2_ids = missing_ids[midpoint:]

        batches = [
            ("consolidated_batch_1.jsonl", batch_1_ids),
            ("consolidated_batch_2.jsonl", batch_2_ids)
        ]

        for filename, ids in batches:
            logger.info(f"Preparing {filename} with {len(ids)} papers...")
            current_batch_count = 0
            with open(filename, "w") as f:
                # Process in chunks of 500
                chunk_size = 500
                for i in range(0, len(ids), chunk_size):
                    chunk_ids = ids[i : i + chunk_size]
                    papers = db.query(Paper).filter(Paper.id.in_(chunk_ids)).all()
                    for paper in papers:
                        content = None
                        if paper.extracted_abstract:
                            content = f"{paper.title} {paper.extracted_abstract}"
                        elif paper.extracted_introduction:
                            content = f"{paper.title} {paper.extracted_introduction}"
                        else:
                            # Try to extract if missing
                            content = manager.extract_content(paper)
                            db.flush()

                        if content and content != "CORRUPTED":
                            request = {
                                "task_type": "RETRIEVAL_DOCUMENT",
                                "content": {"parts": [{"text": content}]},
                                "title": paper.title,
                                "output_dimensionality": 768
                            }
                            f.write(json.dumps({
                                "request": request,
                                "metadata": {"key": paper.arxiv_id}
                            }) + "\n")
                            current_batch_count += 1
                    
                    db.commit()
                    logger.info(f"Progress {filename}: {i + len(chunk_ids)}/{len(ids)}")
                    db.expunge_all()
            
            logger.info(f"Finished {filename} with {current_batch_count} valid entries.")

    finally:
        db.close()

if __name__ == "__main__":
    consolidate()
