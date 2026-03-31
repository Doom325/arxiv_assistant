import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Paper
from datetime import datetime, timedelta

DB_URL = "postgresql://user:password@192.168.1.49:5434/arxiv_db"

def check_failures():
    engine = create_engine(DB_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    recent = datetime.now().date() - timedelta(days=7)
    
    down_failed = db.query(Paper).filter(Paper.published_date >= recent, Paper.extracted_abstract == "[DOWNLOAD FAILED]").count()
    extract_failed = db.query(Paper).filter(Paper.published_date >= recent, Paper.extracted_abstract == "[FAILED]").count()
    none_abstract = db.query(Paper).filter(Paper.published_date >= recent, Paper.extracted_abstract.is_(None)).count()
    not_downloaded = db.query(Paper).filter(Paper.published_date >= recent, Paper.is_downloaded == False).count()

    print(f"Since {recent}:")
    print(f" - [DOWNLOAD FAILED]: {down_failed}")
    print(f" - [FAILED]: {extract_failed}")
    print(f" - extracted_abstract IS NULL: {none_abstract}")
    print(f" - is_downloaded IS FALSE: {not_downloaded}")

if __name__ == "__main__":
    check_failures()
