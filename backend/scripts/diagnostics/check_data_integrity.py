import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from database import SessionLocal
from models import Paper
from sqlalchemy import or_, and_

def check_data_integrity():
    db = SessionLocal()
    
    # 1. Check for null critical fields
    null_titles = db.query(Paper).filter(Paper.title.is_(None)).count()
    null_authors = db.query(Paper).filter(Paper.authors.is_(None)).count()
    null_dates = db.query(Paper).filter(Paper.published_date.is_(None)).count()
    null_categories = db.query(Paper).filter(Paper.category.is_(None)).count()
    
    print(f"Null Titles: {null_titles}")
    print(f"Null Authors: {null_authors}")
    print(f"Null Dates: {null_dates}")
    print(f"Null Categories: {null_categories}")
    
    # 2. Sample some authors to see their types
    papers = db.query(Paper).limit(10).all()
    for p in papers:
        print(f"ID: {p.id}, Authors Type: {type(p.authors)}, Content: {p.authors}")
        print(f"ID: {p.id}, Category Type: {type(p.category)}, Content: {p.category}")
    
    db.close()

if __name__ == "__main__":
    check_data_integrity()
