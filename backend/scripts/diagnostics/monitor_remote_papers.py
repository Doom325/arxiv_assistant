import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Paper
from datetime import datetime, timedelta
import os

DB_URL = "postgresql://user:password@192.168.1.49:5434/arxiv_db"

def monitor_papers():
    engine = create_engine(DB_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    recent = datetime.now().date() - timedelta(days=7)
    
    total_recent = db.query(Paper).filter(Paper.published_date >= recent).count()
    downloaded = db.query(Paper).filter(Paper.published_date >= recent, Paper.is_downloaded == True).count()
    processed = db.query(Paper).filter(Paper.published_date >= recent, Paper.extracted_abstract.isnot(None), Paper.extracted_abstract != "[FAILED]").count()
    
    print(f"Papers since {recent}: {total_recent}")
    print(f"Downloaded: {downloaded}")
    print(f"Processed (Abstract Extracted): {processed}")

if __name__ == "__main__":
    monitor_papers()
