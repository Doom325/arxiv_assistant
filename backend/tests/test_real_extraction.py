
import sys
import os
import logging

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from production_worker import PDFProcessorLite

logging.basicConfig(level=logging.INFO)

def test_real_extraction():
    processor = PDFProcessorLite()
    pdf_path = "backend/Advanced Data Augmentation Strategies for NL-to-SQL in Complex Domains.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"PDF not found: {pdf_path}")
        return

    print(f"Processing {pdf_path}...")
    # We only care about citations for this test
    text = processor.extract_text_from_pdf(pdf_path)
    if not text:
        print("Failed to extract text from PDF")
        return
        
    print("Extracting citations...")
    citations = processor.extract_citations(text)
    
    print(f"Extracted {len(citations)} citations:")
    for i, c in enumerate(citations[:5]):
        print(f"{i+1}. {c.get('title')} by {c.get('authors')}")
        if c.get('url'):
            print(f"   URL: {c.get('url')}")

if __name__ == '__main__':
    test_real_extraction()
