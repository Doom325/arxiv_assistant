import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import datetime
from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker
from models import Paper

DB_URL = "postgresql://user:password@192.168.1.49:5434/arxiv_db"

def test_null_bug():
    engine = create_engine(DB_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    recent = datetime.date.today() - datetime.timedelta(days=7)
    
    print("Testing NULL handling...")
    
    # Query without the != 'FAILED' filters
    q1 = db.query(Paper).filter(
        Paper.published_date >= recent,
        Paper.extracted_abstract.is_(None)
    ).limit(5).all()
    print(f"Query 1 (Plain NULL check) found: {len(q1)}")
    
    # Query with the != 'FAILED' filters
    q2 = db.query(Paper).filter(
        Paper.published_date >= recent,
        Paper.extracted_abstract.is_(None),
        Paper.extracted_abstract != "[FAILED]"
    ).limit(5).all()
    print(f"Query 2 (NULL check + != 'FAILED') found: {len(q2)}")

if __name__ == "__main__":
    test_null_bug()
