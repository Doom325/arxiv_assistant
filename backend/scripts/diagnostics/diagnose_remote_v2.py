
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DB_URL = "postgresql://user:password@192.168.1.49:5434/arxiv_db"

def diagnose():
    engine = create_engine(DB_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    print("--- Table Columns (papers) ---")
    try:
        result = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'papers'"))
        columns = [row[0] for row in result]
        print(f"Columns: {columns}")
    except Exception as e:
        print(f"Failed to get columns: {e}")

    print("\n--- Recent Job Logs ---")
    try:
        result = db.execute(text("SELECT job_name, status, start_time, error_message FROM job_logs ORDER BY start_time DESC LIMIT 10"))
        for row in result:
            print(f"Job: {row[0]}, Status: {row[1]}, Start: {row[2]}, Error: {row[3]}")
    except Exception as e:
        print(f"Failed to get logs: {e}")

    print("\n--- Paper Count ---")
    try:
        result = db.execute(text("SELECT COUNT(*) FROM papers"))
        print(f"Total Papers: {result.scalar()}")
    except Exception as e:
        print(f"Failed to get count: {e}")

    db.close()

if __name__ == "__main__":
    diagnose()
