import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from database import SessionLocal
from models import Paper

def check_count():
    db = SessionLocal()
    count = db.query(Paper).count()
    print(f"Total Papers in Database: {count}")
    
    # Also check how many have metadata? (All should)
    # Check how many have summaries
    summarized = db.query(Paper).filter(Paper.generated_summary.isnot(None)).count()
    print(f"Papers with Summaries: {summarized}")
    
    db.close()

if __name__ == "__main__":
    check_count()
