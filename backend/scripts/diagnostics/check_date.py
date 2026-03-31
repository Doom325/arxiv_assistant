import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from database import SessionLocal
from models import Paper
from sqlalchemy import func
from datetime import datetime, timedelta

def check_dates():
    db = SessionLocal()
    try:
        # Check papers from Dec 1st to Dec 6th
        start_date = datetime(2025, 12, 1)
        
        print("\n--- Paper Counts by Date ---")
        results = db.query(
            func.date(Paper.published_date), 
            func.count(Paper.id)
        ).group_by(
            func.date(Paper.published_date)
        ).order_by(
            func.date(Paper.published_date).desc()
        ).limit(10).all()
        
        for date, count in results:
            print(f"{date}: {count} papers")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_dates()
