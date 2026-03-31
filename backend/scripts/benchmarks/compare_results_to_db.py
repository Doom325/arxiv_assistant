
import json
import glob
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DB_URL = "postgresql://user:password@192.168.1.49:5434/arxiv_db"
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def compare():
    db = SessionLocal()
    print("Fetching existing embedded IDs from remote DB...")
    res = db.execute(text("SELECT arxiv_id FROM papers WHERE embedding IS NOT NULL"))
    existing_ids = {row[0] for row in res}
    print(f"Total existing embeddings: {len(existing_ids)}")

    result_files = glob.glob("results_*.jsonl")
    result_files.sort()
    
    overall_new_records = 0
    for f in result_files:
        new_in_file = 0
        total_in_file = 0
        with open(f, "r") as json_file:
            for line in json_file:
                total_in_file += 1
                try:
                    data = json.loads(line)
                    aid = data["metadata"]["key"]
                    if aid not in existing_ids:
                        new_in_file += 1
                except:
                    pass
        print(f"File: {f:50} | Total: {total_in_file:4} | New: {new_in_file:4}")
        overall_new_records += new_in_file
        
    print(f"\nOverall records in local files that are NOT in DB: {overall_new_records}")
    db.close()

if __name__ == "__main__":
    compare()
