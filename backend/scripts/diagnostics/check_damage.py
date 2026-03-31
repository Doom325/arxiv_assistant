import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models import Paper

# Matches mac_worker.py config
DB_URL = "postgresql://user:password@localhost:5434/arxiv_db"
PDF_DIR = "/Volumes/External/PDFs/Arxiv Assistant"

def check_damage():
    print(f"Checking for deleted PDFs in {PDF_DIR}...")
    
    if not os.path.isdir(PDF_DIR):
        print(f"CRITICAL: PDF Directory not found at {PDF_DIR}")
        return

    try:
        engine = create_engine(DB_URL)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        # Papers that have been processed (have extracted content)
        processed_papers = db.query(Paper).filter(Paper.extracted_abstract.isnot(None)).all()
        
        print(f"Total Processed Papers in DB: {len(processed_papers)}")
        
        missing_count = 0
        missing_ids = []
        
        for paper in processed_papers:
            # Check ID.pdf
            path1 = os.path.join(PDF_DIR, f"{paper.arxiv_id}.pdf")
            # Check versionless (1706.03762v1 -> 1706.03762.pdf)
            base_id = paper.arxiv_id.split('v')[0]
            path2 = os.path.join(PDF_DIR, f"{base_id}.pdf")
            
            if os.path.exists(path1) or os.path.exists(path2):
                continue
            else:
                missing_count += 1
                missing_ids.append(paper.arxiv_id)
                if missing_count <= 5:
                    print(f"MISSING: {paper.arxiv_id} (Processed but PDF gone)")
        
        print("-" * 30)
        print(f"TOTAL MISSING PDFs: {missing_count}")
        print("-" * 30)
        
    except Exception as e:
        print(f"Error connecting to DB: {e}")

if __name__ == "__main__":
    check_damage()
