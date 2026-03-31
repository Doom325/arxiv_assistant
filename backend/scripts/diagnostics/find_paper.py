import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from database import SessionLocal
from models import Paper

db = SessionLocal()
paper = db.query(Paper).filter(Paper.arxiv_id == "2511.21686v1").first()
if paper:
    print(f"ID: {paper.id}")
else:
    print("Paper not found")
