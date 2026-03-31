
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DB_URL = "postgresql://user:password@192.168.1.49:5434/arxiv_db"

def diagnose():
    engine = create_engine(DB_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    print("--- Existing Tables ---")
    try:
        result = db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
        tables = [row[0] for row in result]
        print(f"Tables: {tables}")
    except Exception as e:
        print(f"Failed to get tables: {e}")

    # Check pgvector extension
    print("\n--- Extensions ---")
    try:
        result = db.execute(text("SELECT extname FROM pg_extension"))
        exts = [row[0] for row in result]
        print(f"Extensions: {exts}")
    except Exception as e:
        print(f"Failed to get extensions: {e}")

    db.close()

if __name__ == "__main__":
    diagnose()
