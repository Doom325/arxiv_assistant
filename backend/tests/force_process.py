import sys
import os
import logging

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database import SessionLocal
from models import Paper
from production_worker import PDFProcessorLite, get_local_pdf_path, download_pdf

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ForceWorker")

def force_process_citations(paper_id):
    db = SessionLocal()
    try:
        paper = db.query(Paper).filter(Paper.id == paper_id).first()
        if not paper:
            print(f"Paper {paper_id} not found")
            return

        print(f"Processing paper: {paper.title} ({paper.arxiv_id})")
        
        pdf_path = get_local_pdf_path(paper.arxiv_id)
        if not pdf_path:
            url = paper.pdf_url or f"https://arxiv.org/pdf/{paper.arxiv_id}.pdf"
            print(f"Downloading from {url}...")
            pdf_path = download_pdf(url, paper.arxiv_id)
        
        if not pdf_path:
            print("Download failed")
            return

        processor = PDFProcessorLite()
        result = processor.process_pdf(pdf_path)
        if result:
            paper.citations = result['citations']
            db.commit()
            print(f"Successfully extracted {len(result['citations'])} citations!")
            for idx, c in enumerate(result['citations']):
                print(f"{idx+1}. {c['title']} ({c.get('url')})")
        else:
            print("Processing failed")

    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        force_process_citations(int(sys.argv[1]))
    else:
        print("Usage: python backend/tests/force_process.py <paper_id>")
