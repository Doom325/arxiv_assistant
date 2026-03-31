
from sqlalchemy import create_engine, text
from config import settings
from datetime import datetime, timedelta

def count_backfill():
    engine = create_engine(settings.DATABASE_URL)
    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    print(f"Targeting papers from {seven_days_ago} onwards in cs.AI")
    
    with engine.connect() as conn:
        query = text("""
            SELECT count(*) 
            FROM papers 
            WHERE published_date >= :date
              AND category = 'cs.AI'
        """)
        count = conn.execute(query, {"date": seven_days_ago}).scalar()
        print(f"Papers found: {count}")
        
        # Check how many of these are already classified
        query_done = text("""
            SELECT count(*) 
            FROM pattern_experiment_results r
            JOIN papers p ON r.arxiv_id = p.arxiv_id
            WHERE p.published_date >= :date
              AND p.category = 'cs.AI'
        """)
        done = conn.execute(query_done, {"date": seven_days_ago}).scalar()
        print(f"Already classified: {done}")
        print(f"Remaining: {count - done}")

if __name__ == "__main__":
    count_backfill()
