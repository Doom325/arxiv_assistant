
import os
import time
import requests
import datetime
import logging
from sqlalchemy import create_engine, or_, text
from sqlalchemy.orm import sessionmaker
from models import Paper, JobLog
from config import settings

# Setup Logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("PDFCatchup")

# Configuration
DB_URL = os.getenv("DATABASE_URL", "postgresql://user:password@db:5432/arxiv_db")
PDF_DIR = os.getenv("PDF_SAVE_DIR", "/app/data")

engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def download_pdf(url: str, arxiv_id: str) -> str:
    try:
        if not os.path.exists(PDF_DIR): os.makedirs(PDF_DIR, exist_ok=True)
        target_path = os.path.join(PDF_DIR, f"{arxiv_id}.pdf")
        if os.path.exists(target_path):
            return target_path
            
        logger.info(f"Downloading {url} to {target_path}...")
        # Add headers to mimic a browser to avoid some reCAPTCHA blocks if possible
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
        }
        response = requests.get(url, timeout=60, headers=headers)
        response.raise_for_status()
        with open(target_path, 'wb') as f: f.write(response.content)
        return target_path
    except Exception as e:
        logger.error(f"Download failed for {arxiv_id}: {e}")
        return None

def run_catchup():
    logger.info("🚀 Starting PDF Catch-up Job (Bypassing 7-day filter)")
    db = SessionLocal()
    try:
        # Count missing
        total_missing = db.query(Paper).filter(Paper.is_downloaded == False).count()
        logger.info(f"Found {total_missing} papers missing PDFs.")
        
        batch_size = 50
        offset = 0
        
        while True:
            papers = db.query(Paper).filter(Paper.is_downloaded == False).order_by(Paper.published_date.desc()).offset(offset).limit(batch_size).all()
            if not papers:
                break
                
            logger.info(f"Processing batch of {len(papers)} papers (Offset: {offset})...")
            for paper in papers:
                url = paper.pdf_url or f"https://arxiv.org/pdf/{paper.arxiv_id}.pdf"
                path = download_pdf(url, paper.arxiv_id)
                if path:
                    paper.is_downloaded = True
                    db.commit()
                else:
                    # If we fail, we might want to skip it for this run to avoid infinite loops if it's a 404
                    pass
                
                # Tiny throttle to be polite to Arxiv
                time.sleep(1)
            
            offset += batch_size
            
    except Exception as e:
        logger.error(f"Catch-up Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run_catchup()
