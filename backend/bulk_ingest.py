import json
import os
import logging
import requests
import time
from datetime import datetime, timedelta
from database import SessionLocal
from models import UserConfig
from sqlalchemy import select

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

METADATA_FILE = "data/arxiv-metadata-oai-snapshot.json"
PDF_DIR = "data/pdfs"

def get_target_categories():
    """Fetch all unique categories tracked by users."""
    db = SessionLocal()
    try:
        configs = db.scalars(select(UserConfig)).all()
        categories = set()
        for config in configs:
            if config.categories:
                categories.update(config.categories)
        return categories
    finally:
        db.close()

def parse_date(date_str):
    """Parse arXiv date format (e.g., 'Mon, 2 Apr 2007 19:18:42 GMT' or '2007-04-02')."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return None

def get_paper_date(paper):
    """Extract date from paper JSON."""
    # 1. Try update_date
    update_date_str = paper.get("update_date")
    if update_date_str:
        return parse_date(update_date_str)
    
    # 2. Try versions
    versions = paper.get("versions", [])
    if versions:
        if isinstance(versions[0], str):
            return None
        # Format: "Mon, 2 Apr 2007 19:18:42 GMT"
        created_str = versions[0].get("created")
        try:
            parts = created_str.split(", ")[1].split(" ")
            day, month_str, year = parts[0], parts[1], parts[2]
            return datetime.strptime(f"{year}-{month_str}-{day}", "%Y-%b-%d").date()
        except Exception:
            pass
    return None

def download_pdf(url, filepath, fallback_url=None):
    """Download PDF from URL to filepath, with optional fallback."""
    try:
        response = requests.get(url, stream=True, timeout=30)
        if response.status_code == 200:
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        elif response.status_code == 404 and fallback_url:
            logger.warning(f"404 for {url}, trying fallback: {fallback_url}")
            response = requests.get(fallback_url, stream=True, timeout=30)
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                return True
            else:
                logger.error(f"Fallback failed for {fallback_url}: Status {response.status_code}")
                return False
        else:
            logger.error(f"Failed to download {url}: Status {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Error downloading {url}: {e}")
        return False

def bulk_ingest(years=3):
    """
    Download PDFs from local metadata based on user categories and date range.
    """
    if not os.path.exists(PDF_DIR):
        os.makedirs(PDF_DIR)
        
    if not os.path.exists(METADATA_FILE):
        logger.error(f"Metadata file not found: {METADATA_FILE}")
        return

    target_categories = get_target_categories()
    if not target_categories:
        logger.warning("No user categories found. Nothing to ingest.")
        return

    logger.info(f"Target categories: {target_categories}")
    
    cutoff_date = (datetime.now() - timedelta(days=years*365)).date()
    logger.info(f"Filtering papers updated after: {cutoff_date}")

    logger.info(f"Reading metadata from {METADATA_FILE}...")
    
    count = 0
    downloaded = 0
    
    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        for line in f:
            # Optimization: Quick check for recent years in ID (22, 23, 24, 25)
            # This skips parsing JSON for old papers (2007-2021)
            if not any(x in line for x in ['"id": "22', '"id": "23', '"id": "24', '"id": "25',
                                         '"id":"22', '"id":"23', '"id":"24', '"id":"25']):
                count += 1
                if count % 500000 == 0:
                    logger.info(f"Skipped {count} papers...")
                continue

            try:
                paper = json.loads(line)
                
                # 1. Check Category
                raw_cats = paper.get("categories", "")
                paper_categories = set()
                if isinstance(raw_cats, list):
                    for cat_str in raw_cats:
                        paper_categories.update(cat_str.split())
                elif isinstance(raw_cats, str):
                    paper_categories.update(raw_cats.split())
                
                if not paper_categories.intersection(target_categories):
                    continue

                # 2. Check Date
                p_date = get_paper_date(paper)
                if not p_date or p_date < cutoff_date:
                    continue

                # 3. Download PDF
                arxiv_id = paper.get("id")
                
                if "/" in arxiv_id:
                    continue
                
                pdf_path = os.path.join(PDF_DIR, f"{arxiv_id}.pdf")
                if os.path.exists(pdf_path):
                    # logger.info(f"Skipping existing PDF: {arxiv_id}")
                    continue

                yymm = arxiv_id.split(".")[0]
                versions = paper.get("versions", [])
                if versions:
                    latest_version = versions[-1]["version"]
                else:
                    latest_version = "v1"
                    
                # Use arXiv.org directly as requested
                pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
                
                logger.info(f"Downloading {arxiv_id} ({p_date})...")
                # We can remove fallback since this is the source of truth
                if download_pdf(pdf_url, pdf_path):
                    downloaded += 1
                    time.sleep(3) # Be nice to arXiv API
                    if downloaded % 10 == 0:
                        logger.info(f"Downloaded {downloaded} PDFs so far.")

            except json.JSONDecodeError:
                continue
            except Exception as e:
                logger.error(f"Error processing line: {e}")
                continue
            
            count += 1
            if count % 100000 == 0:
                logger.info(f"Scanned {count} papers...")

if __name__ == "__main__":
    bulk_ingest()
