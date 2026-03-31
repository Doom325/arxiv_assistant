import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from database import SessionLocal
from models import Paper

def test_db():
    db = SessionLocal()
    try:
        # Check for papers with local PDF paths
        papers = db.query(Paper).filter(Paper.pdf_url.like("/%")).limit(5).all()
        if papers:
            print(f"Found {len(papers)} papers with local paths:")
            for p in papers:
                print(f"- {p.pdf_url}")
        else:
            print("No papers with local paths found. All seem to be external.")
            
        # Check total count
        count = db.query(Paper).count()
        print(f"Total papers: {count}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_db()
