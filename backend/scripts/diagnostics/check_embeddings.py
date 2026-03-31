import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from database import SessionLocal
from models import Paper

def check_embeddings():
    db = SessionLocal()
    total = db.query(Paper).count()
    with_embedding = db.query(Paper).filter(Paper.embedding.isnot(None)).count()
    
    print(f"Total Papers: {total}")
    print(f"Papers with Embeddings: {with_embedding}")
    print(f"Papers MISSING Embeddings: {total - with_embedding}")
    
    db.close()

if __name__ == "__main__":
    check_embeddings()
