import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Paper
from datetime import datetime, timedelta
import pytz

# Config
DB_URL = "postgresql://user:password@localhost:5434/arxiv_db"

def check_processed():
    engine = create_engine(DB_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    # Check papers with yesterday's date
    ist = pytz.timezone('Asia/Kolkata')
    today_ist = datetime.now(ist).date()
    yesterday = today_ist - timedelta(days=1)
    
    print(f"Checking for processed papers from: {yesterday}")
    
    papers = db.query(Paper).filter(Paper.published_date == yesterday).all()
    
    print(f"Total papers found for {yesterday}: {len(papers)}")
    
    processed_count = 0
    summarized_count = 0
    
    for p in papers:
        if p.extracted_abstract:
            processed_count += 1
        if p.generated_summary:
            summarized_count += 1
            
    print(f"Propcessed (Content Extracted): {processed_count}")
    print(f"Summarized (AI Insight): {summarized_count}")

    if summarized_count > 0:
        print("✅ Daily Summary appears to have run!")
    else:
        print("❌ No summaries found for yesterday's papers.")

if __name__ == "__main__":
    check_processed()
