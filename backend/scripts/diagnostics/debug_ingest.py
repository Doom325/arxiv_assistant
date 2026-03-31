import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import json
import os
from database import SessionLocal
from models import Paper
from sqlalchemy import text
import logging
import time

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_ingest():
    local_output = "results_mrs6aty9pck9wxxtthmok0q8wy38le60hy86.jsonl"
    if not os.path.exists(local_output):
        print(f"File {local_output} not found")
        return

    print("Connecting to DB...")
    db = SessionLocal()
    print("Connected.")

    processed_count = 0
    with open(local_output, "r") as f:
        for i, line in enumerate(f):
            if i >= 10: # Only try 10 items
                break
            
            try:
                print(f"Processing line {i}...")
                data = json.loads(line)
                arxiv_id = data["metadata"]["key"]
                print(f"  Arxiv ID: {arxiv_id}")
                
                # Check directly with SQL first to see if ID exists
                # result = db.execute(text("SELECT id FROM papers WHERE arxiv_id = :aid"), {"aid": arxiv_id}).fetchone()
                # print(f"  Exists in DB (raw SQL): {result}")

                print("  Querying ORM...")
                print("  Executing direct UPDATE...")
                stmt = text("UPDATE papers SET embedding = :emb WHERE arxiv_id = :aid")
                
                response = data["response"]
                embedding = None
                if isinstance(response, list) and len(response) > 0:
                    embedding = response[0].get("embedding")
                elif isinstance(response, dict):
                    embedding = response.get("embedding")
                
                if isinstance(embedding, dict) and "values" in embedding:
                    embedding = embedding["values"]

                if embedding:
                    start = time.time()
                    # We need to serialise embedding appropriately if using raw text sql, 
                    # but typically psycopg2 handles list -> array. 
                    # With pgvector, we might need to cast to vector?
                    # Let's try passing list first.
                    result = db.execute(stmt, {"emb": embedding, "aid": arxiv_id})
                    print(f"  Update took {time.time() - start:.4f}s")
                    print(f"  Rows updated: {result.rowcount}")
                    processed_count += 1
                else:
                    print("  No embedding found in data.")
            
            except Exception as e:
                print(f"  Error: {e}")
                import traceback
                traceback.print_exc()

    print("Committing...")
    db.commit()
    print("Done.")
    db.close()

if __name__ == "__main__":
    debug_ingest()
