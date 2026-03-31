import logging
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Paper
from services.nlp_service import nlp_service
from config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("EntityBackfill")

DB_URL = settings.DATABASE_URL
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def backfill_entities(batch_size=50, limit=None):
    db = SessionLocal()
    try:
        query = db.query(Paper).filter(Paper.entities.is_(None))
        total = query.count()
        if limit:
            total = min(total, limit)
            
        logger.info(f"Starting backfill for {total} papers...")
        
        processed = 0
        while True:
            papers = query.limit(batch_size).all()
            if not papers or (limit and processed >= limit):
                break
                
            for paper in papers:
                try:
                    # Extract from title and summary
                    text = f"{paper.title}\n{paper.summary}"
                    entities = nlp_service.extract_entities(text[:1500]) # Limit context for speed
                    paper.entities = entities
                    processed += 1
                except Exception as e:
                    logger.error(f"Error processing paper {paper.arxiv_id}: {e}")
            
            db.commit()
            logger.info(f"Processed {processed}/{total} papers...")
            
    finally:
        db.close()

if __name__ == "__main__":
    import sys
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    backfill_entities(limit=limit)
