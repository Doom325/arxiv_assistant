import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import JobLog
from datetime import datetime
import os

# Connect to Khadas IP
DB_URL = "postgresql://user:password@192.168.1.49:5434/arxiv_db"

def fix_stuck_jobs():
    print(f"Connecting to {DB_URL}...")
    try:
        engine = create_engine(DB_URL, connect_args={'connect_timeout': 5})
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        print("Checking for stuck RUNNING jobs...")
        
        # Find jobs stuck in RUNNING for more than 1 hour (simple heuristic)
        stuck_jobs = db.query(JobLog).filter(JobLog.status == "RUNNING").all()
        
        count = 0
        for job in stuck_jobs:
            # Check if start_time is old (e.g. not today)
            # Assuming if I'm running this, I want to clear them all because I know it's stuck.
            print(f"Fixing stuck job: {job.job_name} (Started: {job.start_time})")
            job.status = "FAILED"
            job.error_message = "Job detected as stuck and manually reset."
            job.end_time = datetime.utcnow()
            count += 1
            
        if count > 0:
            db.commit()
            print(f"Successfully reset {count} stuck jobs.")
        else:
            print("No stuck jobs found.")
            
    except Exception as e:
        print(f"Operation Failed: {e}")

if __name__ == "__main__":
    fix_stuck_jobs()
