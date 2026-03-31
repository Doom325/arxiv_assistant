import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from production_worker import PDFProcessorLite
from models import Paper
from config import settings

def test_citations(arxiv_id):
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    paper = db.query(Paper).filter(Paper.arxiv_id == arxiv_id).first()
    if not paper:
        print(f"Paper {arxiv_id} not found")
        return

    pdf_path = os.path.join(settings.PDF_SAVE_DIR, f"{arxiv_id}.pdf")
    if not os.path.exists(pdf_path):
        # Try without vX
        pdf_path = os.path.join(settings.PDF_SAVE_DIR, f"{arxiv_id.split('v')[0]}.pdf")
        if not os.path.exists(pdf_path):
            print(f"PDF not found for {arxiv_id}")
            return

    print(f"Processing {pdf_path}...")
    processor = PDFProcessorLite()
    text = processor.extract_text_from_pdf(pdf_path)
    if not text:
        print("Failed to extract text from PDF")
        return
    
    print(f"Text length: {len(text)}")
    # Print some of the end of the text to see if headers are there
    print("--- LAST 2000 CHARS ---")
    print(text[-2000:])
    
    citations = processor.extract_citations(text)
    print(f"Extracted {len(citations)} citations")
    for c in citations[:5]:
        print(f" - {c.get('title')}")

if __name__ == "__main__":
    test_citations(sys.argv[1])
