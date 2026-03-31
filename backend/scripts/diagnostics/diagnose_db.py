import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from models import Paper, JobLog
from datetime import datetime, timedelta

DB_URL = "postgresql://user:password@localhost:5434/arxiv_db"

def diagnose():
    engine = create_engine(DB_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    print("--- Latest Papers ---")
    latest_papers = db.query(Paper).order_by(desc(Paper.published_date)).limit(5).all()
    if not latest_papers:
        print("No papers found in DB!")
    for p in latest_papers:
        print(f"ID: {p.arxiv_id}, Title: {p.title[:50]}, Published: {p.published_date}")
        
    print("\n--- Latest Job Logs ---")
    latest_jobs = db.query(JobLog).order_by(desc(JobLog.start_time)).limit(10).all()
    for j in latest_jobs:
        print(f"Job: {j.job_name}, Status: {j.status}, Start: {j.start_time}, Details: {j.job_details}, Error: {j.error_message}")

    print("\n--- Summary Count ---")
    total = db.query(Paper).count()
    print(f"Total papers: {total}")
    
    db.close()

if __name__ == "__main__":
    diagnose()
