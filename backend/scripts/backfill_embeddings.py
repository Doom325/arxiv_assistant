import sys
import os
import time
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Paper, PaperEmbedding
from services.llm_service import llm_service, embedding_service
from config import settings

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("BackfillEmbeddings")

# Database setup
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def backfill_embeddings():
    db = SessionLocal()
    try:
        # Get all paper IDs that don't have an embedding
        # Use outer join to find missing
        # Batching for memory safety
        BATCH_SIZE = 100
        
        while True:
            # Query papers without embedding
            # Note: We query Paper IDs first to keep query simple
            # Or assume we just loop through all papers and check existence? 
            # Subquery is better.
            
            # Find papers with NO entry in paper_embeddings
            missing_papers = db.query(Paper).outerjoin(PaperEmbedding).filter(
                PaperEmbedding.id.is_(None)
            ).limit(BATCH_SIZE).all()
            
            if not missing_papers:
                logger.info("No more papers to backfill. Done!")
                break
            
            logger.info(f"Processing batch of {len(missing_papers)} papers...")
            
            success_count = 0
            for paper in missing_papers:
                try:
                    search_text = paper.summary or paper.extracted_abstract or paper.title
                    if not search_text:
                        logger.warning(f"Skipping {paper.arxiv_id}: No text available.")
                        continue
                        
                    # Generate embedding (768d via gemini-embedding-001)
                    # We don't pass output_dimensionality as it defaults/is fixed for 001
                    embedding = embedding_service.generate_embedding(search_text)
                    
                    if embedding:
                        new_emb = PaperEmbedding(
                            paper_id=paper.id,
                            embedding=embedding,
                            embedding_config={"purpose": "search", "dimension": 768},
                            embedding_metadata={"source_model": "gemini-embedding-001", "created_at": str(time.time())}
                        )
                        db.add(new_emb)
                        success_count += 1
                        
                        # Commit every few papers or at end of batch?
                        # Committing per paper is safer for long running processes
                        # But slightly slower. Let's commit every batch or sub-batch.
                    else:
                        logger.error(f"Failed to generate embedding for {paper.arxiv_id}")
                        
                except Exception as e:
                    logger.error(f"Error processing {paper.arxiv_id}: {e}")
                    continue
            
            db.commit()
            logger.info(f"Batch complete. Added {success_count} embeddings.")
            time.sleep(1) # Rate limiting buffer
            
    finally:
        db.close()

if __name__ == "__main__":
    backfill_embeddings()
