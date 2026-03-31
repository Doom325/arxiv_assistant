import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from models import JobLog, Paper
import os

# Connect to Khadas IP
DB_URL = "postgresql://user:password@192.168.1.49:5434/arxiv_db"

def check_remote_status():
    print(f"Connecting to {DB_URL}...")
    try:
        engine = create_engine(DB_URL, connect_args={'connect_timeout': 5})
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        print("--- Connection Successful ---")
        
        # 1. Check Latest Paper
        latest_paper = db.query(Paper).order_by(Paper.published_date.desc()).first()
        if latest_paper:
            print(f"Latest Paper Date: {latest_paper.published_date} (ID: {latest_paper.arxiv_id})")
        else:
            print("No papers found.")
            
        # 2. Check Recent Job Logs
        print("\n--- Recent Job Logs (Last 10) ---")
        jobs = db.query(JobLog).order_by(desc(JobLog.start_time)).limit(10).all()
        for job in jobs:
            status_icon = "✅" if job.status == "SUCCESS" else "❌" if job.status == "FAILED" else "⚠️"
            print(f"{status_icon} [{job.start_time}] {job.job_name}: {job.status}")
            if job.error_message:
                print(f"   Error: {job.error_message}")
                
        # 3. Check for specific failure patterns in papers
        fail_count = db.query(Paper).filter(Paper.extracted_abstract == "[FAILED]").count()
        print(f"\nTotal Failed Extractions: {fail_count}")

    except Exception as e:
        print(f"Connection Failed: {e}")

if __name__ == "__main__":
    check_remote_status()
