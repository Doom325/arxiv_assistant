import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from database import SessionLocal
from models import Paper
import json

def repair_authors():
    db = SessionLocal()
    
    # Fetch papers where authors is a string (not a list)
    # Since SQLAlchemy handles the JSON type, we check if the Python value is a string
    papers = db.query(Paper).all()
    repaired_count = 0
    
    print(f"Checking {len(papers)} papers...")
    
    for p in papers:
        if isinstance(p.authors, str):
            # Convert comma-separated string to list
            # "Author 1, Author 2" -> ["Author 1", "Author 2"]
            old_val = p.authors
            new_val = [a.strip() for a in old_val.split(",") if a.strip()]
            p.authors = new_val
            repaired_count += 1
            
            if repaired_count % 1000 == 0:
                print(f"Repaired {repaired_count} papers...")
                db.commit() # Periodic commit
                
    db.commit()
    db.close()
    print(f"Repair Complete. Fixed {repaired_count} papers.")

if __name__ == "__main__":
    repair_authors()
