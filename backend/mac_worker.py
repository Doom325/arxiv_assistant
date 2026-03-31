"""
Mac Worker — Local development processor.

This worker runs on Mac for development, using PyTorch/MLX for local inference.
Production uses production_worker.py on Khadas Edge 2 with Gemini API/Ollama.
"""

import os
import time
import logging
from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker
from models import Paper
from pdf_processor import PDFProcessor
from core.pdf_utils import get_local_pdf_path as _get_local_pdf_path, download_pdf as _download_pdf
from core.text_utils import sanitize_text
from config import settings

# Setup Logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MacWorker")
logging.getLogger("pypdf").setLevel(logging.ERROR)

# Configuration — use centralized settings
DB_URL = settings.DATABASE_URL
PDF_DIR = settings.PDF_SAVE_DIR

engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_local_pdf_path(arxiv_id: str) -> str:
    """Backward-compatible wrapper. Delegates to core.pdf_utils."""
    return _get_local_pdf_path(arxiv_id, PDF_DIR)

def download_pdf(url: str, arxiv_id: str) -> str:
    """Backward-compatible wrapper. Delegates to core.pdf_utils."""
    return _download_pdf(url, arxiv_id, PDF_DIR, timeout=30)

def run_worker():
    logger.info("🚀 Starting Mac Processor Worker (Local Mode + Auto-Download)...")
    logger.info(f"Connecting to DB at {DB_URL}...")
    
    processor = None
    
    while True:
        db = SessionLocal()
        try:
            # 1. Fetch papers that need processing (Embedding OR Summary)
            batch_size = 10  # Smaller batch size for stability with heavy MLX model
            
            # Complex filter: Needs embedding OR needs summary
            papers = db.query(Paper).filter(
                or_(
                    Paper.extracted_abstract.is_(None),
                    Paper.generated_summary.is_(None)
                )
            ).order_by(Paper.published_date.desc()).limit(batch_size).all()
            
            if not papers:
                logger.info("No papers pending processing. Sleeping 10s...")
                time.sleep(10)
                continue
            
            # Lazy load processor only if needed for embeddings
            if processor is None:
                 # Check if any paper needs embedding
                 needs_embedding = any(p.extracted_abstract is None for p in papers)
                 if needs_embedding:
                     processor = PDFProcessor() # Loads GemmaEmbed

            from services.summarization_service import summarization_service  # lazy import for MLX

            logger.info(f"Processing batch of {len(papers)} papers...")
            
            for paper in papers:
                # A. Get PDF Path
                pdf_path = get_local_pdf_path(paper.arxiv_id)
                
                # B. Fallback Download (only if missing)
                if not pdf_path:
                     logger.warning(f"PDF missing for {paper.arxiv_id}. Attempting download...")
                     url = paper.pdf_url or f"https://arxiv.org/pdf/{paper.arxiv_id}.pdf"
                     pdf_path = download_pdf(url, paper.arxiv_id)
                     
                if not pdf_path:
                     logger.error(f"Could not retrieve PDF for {paper.arxiv_id}. Skipping.")
                     continue
                
                try:
                    # C. Process Embeddings (if missing)
                    if not paper.extracted_abstract:
                        if processor:
                            result = processor.process_pdf(pdf_path)
                            
                            if result:
                                # Handle empty lists
                                abs_emb = result['embeddings']['abstract']
                                if not abs_emb or len(abs_emb) == 0: abs_emb = None
                                    
                                intro_emb = result['embeddings']['introduction']
                                if not intro_emb or len(intro_emb) == 0: intro_emb = None
                                    
                                paper.extracted_abstract = sanitize_text(result['sections']['abstract']) or None
                                paper.extracted_introduction = sanitize_text(result['sections']['introduction']) or None
                                paper.abstract_embedding = abs_emb
                                paper.introduction_embedding = intro_emb
                                
                                db.commit()
                                logger.info(f"✅ Extracted/Embedded {paper.arxiv_id}")
                            else:
                                logger.warning(f"Failed to process content for {paper.arxiv_id}")
                    
                    # D. Generate Summary (if missing)
                    if not paper.generated_summary:
                        logger.info(f"Generating summary for {paper.arxiv_id}...")
                        try:
                            # Use the service (loads MLX if needed)
                            summary = summarization_service.generate_summary(pdf_path)
                            paper.generated_summary = summary
                            db.commit()
                            logger.info(f"✅ Summarized {paper.arxiv_id}")
                            
                            # Sleep to let GPU cool?
                            time.sleep(2)
                        except Exception as e:
                            logger.error(f"Summarization failed for {paper.arxiv_id}: {e}")
                            # Don't rollback immediately, we might have saved embeddings above
                            # But if commit fails? The commit above already happened.
                        
                except Exception as e:
                    logger.error(f"Error processing {paper.arxiv_id}: {e}")
                    db.rollback()
                
            # End of batch sleep
            time.sleep(2)

        except Exception as e:
            logger.error(f"Worker Loop Error: {e}")
            logger.info("Reconnecting in 5s...")
            time.sleep(5)
        finally:
            db.close()

if __name__ == "__main__":
    run_worker()
