import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from models import JobLog
import os

DB_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5434/arxiv_db")
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

print("--- Recent Job Logs ---")
jobs = db.query(JobLog).order_by(desc(JobLog.start_time)).limit(20).all()
for job in jobs:
    print(f"[{job.start_time}] {job.job_name}: {job.status} - {job.error_message or ''}")
print("-----------------------")
