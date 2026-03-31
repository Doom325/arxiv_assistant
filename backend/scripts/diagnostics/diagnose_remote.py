import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from models import Paper, JobLog
from datetime import datetime, timedelta

DB_URL = "postgresql://user:password@192.168.1.49:5434/arxiv_db"

def diagnose():
    print(f"Connecting to {DB_URL}...")
    try:
        engine = create_engine(DB_URL, connect_args={'connect_timeout': 5})
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        print("--- Latest Papers ---")
        latest_papers = db.query(Paper).order_by(desc(Paper.published_date)).limit(5).all()
        if not latest_papers:
            print("No papers found in DB!")
        for p in latest_papers:
            print(f"ID: {p.arxiv_id}, Published: {p.published_date}, Downloaded: {p.is_downloaded}")
            
        print("\n--- Latest Job Logs (Last 15) ---")
        latest_jobs = db.query(JobLog).order_by(desc(JobLog.start_time)).limit(15).all()
        for j in latest_jobs:
            print(f"Job: {j.job_name}, Status: {j.status}, Start: {j.start_time}, Details: {j.job_details}")
            if j.error_message:
                 print(f"   Error: {j.error_message}")

        print("\n--- Paper Distribution by Date ---")
        from sqlalchemy import func
        stats = db.query(func.date(Paper.published_date), func.count(Paper.id)).group_by(func.date(Paper.published_date)).order_by(desc(func.date(Paper.published_date))).limit(10).all()
        for d, c in stats:
            print(f"Date: {d}, Count: {c}")

        db.close()
    except Exception as e:
        print(f"Diagnosis Failed: {e}")

if __name__ == "__main__":
    diagnose()
