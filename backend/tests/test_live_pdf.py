import sys
import os
import logging
import json

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import production_worker
# Force local path for test
production_worker.PDF_DIR = os.path.join(os.path.dirname(__file__), '../data/pdfs')
os.makedirs(production_worker.PDF_DIR, exist_ok=True)

from production_worker import PDFProcessorLite, download_pdf

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LiveTest")

def test_live_pdf():
    arxiv_id = "1706.03762" # Attention Is All You Need
    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    
    # 1. Download
    logger.info(f"Downloading {arxiv_id}...")
    pdf_path = download_pdf(pdf_url, arxiv_id)
    if not pdf_path:
        logger.error("Download failed")
        return

    # 2. Process
    logger.info(f"Processing {pdf_path}...")
    processor = PDFProcessorLite()
    
    # Use granular MLX if on Mac
    try:
        results = processor.process_pdf(pdf_path)
        if results:
            print("\n=== EXTRACTION RESULTS ===")
            print(f"File: {results['file']}")
            print(f"Citations Found: {len(results['citations'])}")
            print(json.dumps(results['citations'], indent=2))
        else:
            print("Extraction failed (returned None)")
    except Exception as e:
        logger.error(f"Live test error: {e}")

if __name__ == "__main__":
    test_live_pdf()
