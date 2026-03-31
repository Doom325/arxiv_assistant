import sys
import os
from sqlalchemy import text
from database import SessionLocal

def migrate():
    db = SessionLocal()
    try:
        print("Checking for search_vector column...")
        # Check if column exists
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='papers' AND column_name='search_vector';
        """)).fetchone()
        
        if not result:
            print("Adding search_vector column and index...")
            # We use a trick for generated columns with tsvector in Postgres
            db.execute(text("""
                ALTER TABLE papers 
                ADD COLUMN search_vector tsvector 
                GENERATED ALWAYS AS (
                    to_tsvector('english', coalesce(title, '') || ' ' || coalesce(summary, ''))
                ) STORED;
            """))
            db.execute(text("CREATE INDEX idx_papers_search ON papers USING GIN(search_vector);"))
            print("Successfully added search_vector and index.")
        else:
            print("search_vector column already exists.")
            
        db.commit()
    except Exception as e:
        print(f"Migration failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    migrate()
