
from sqlalchemy import create_engine, text
from config import settings

def check_recent():
    engine = create_engine(settings.DATABASE_URL)
    with engine.connect() as conn:
        print("Recent 5 papers:")
        query = text("SELECT arxiv_id, published_date, category FROM papers ORDER BY published_date DESC LIMIT 5")
        results = conn.execute(query).fetchall()
        for r in results:
            print(r)
            
        print("\nDistinct categories (top 10):")
        query_cats = text("SELECT category, count(*) FROM papers GROUP BY category ORDER BY count(*) DESC LIMIT 10")
        results_cats = conn.execute(query_cats).fetchall()
        for r in results_cats:
            print(r)

if __name__ == "__main__":
    check_recent()
