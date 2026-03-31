import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Paper
from datetime import date

# Ensure we use the correct port (5434 based on recent fixes)
DB_URL = "postgresql://user:password@localhost:5434/arxiv_db"

def check_status():
    try:
        engine = create_engine(DB_URL)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        target_dates = [date(2025, 12, 12), date(2025, 12, 11)]
        
        papers = db.query(Paper).filter(Paper.published_date.in_(target_dates)).all()
        
        total = len(papers)
        with_summary = len([p for p in papers if p.generated_summary])
        
        print(f"Total Papers (Dec 11-12): {total}")
        print(f"With Summary: {with_summary}")
        print(f"Missing Summary: {total - with_summary}")
        
    except Exception as e:
        print(f"Error connecting to DB: {e}")

if __name__ == "__main__":
    check_status()
