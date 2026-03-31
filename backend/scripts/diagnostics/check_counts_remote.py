import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Paper, PaperEmbedding
import os

DB_URL = "postgresql://user:password@192.168.1.49:5434/arxiv_db"

def check_counts():
    engine = create_engine(DB_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    p_count = db.query(Paper).count()
    e_count = db.query(PaperEmbedding).count()
    
    print(f"Total Papers: {p_count}")
    print(f"Total Embeddings: {e_count}")

if __name__ == "__main__":
    check_counts()
