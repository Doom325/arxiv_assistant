import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker
from models import Paper, PaperEmbedding
import datetime
import time

DB_URL = "postgresql://user:password@192.168.1.49:5434/arxiv_db"

def test_query():
    engine = create_engine(DB_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    seven_days_ago = datetime.datetime.now() - datetime.timedelta(days=7)
    
    start = time.time()
    print("Running query...")
    papers = db.query(Paper).outerjoin(PaperEmbedding).filter(
        or_(
            Paper.is_downloaded == False,
            Paper.extracted_abstract.is_(None),
            PaperEmbedding.id.is_(None)
        ),
        Paper.published_date >= seven_days_ago.date(),
        Paper.extracted_abstract != "[FAILED]",
        Paper.extracted_abstract != "[DOWNLOAD FAILED]"
    ).order_by(Paper.published_date.desc()).limit(5).all()
    
    end = time.time()
    print(f"Query took {end - start:.2f} seconds")
    print(f"Found {len(papers)} papers")
    for p in papers:
        print(f" - {p.arxiv_id}: {p.title}")

if __name__ == "__main__":
    test_query()
