
import json
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DB_URL = "postgresql://user:password@arxiv_assistant_db:5432/arxiv_db"
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def check():
    db = SessionLocal()
    # Check total available papers
    total = db.execute(text("SELECT count(*) FROM papers")).fetchone()[0]
    with_emb = db.execute(text("SELECT count(*) FROM papers WHERE embedding IS NOT NULL")).fetchone()[0]
    print(f"Total papers: {total}, With embedding: {with_emb}, Missing: {total - with_emb}")

    # Check a different batch
    filename = "results_bu9c5l653wr7hd2nw77k5px36ik1y45son2z.jsonl"
    if os.path.exists(filename):
        print(f"\nChecking data from {filename}...")
        with open(filename, "r") as f:
            line = f.readline()
            data = json.loads(line)
            arxiv_id = data["metadata"]["key"]
            res = db.execute(text("SELECT arxiv_id, embedding IS NOT NULL FROM papers WHERE arxiv_id = :aid"), {"aid": arxiv_id}).fetchone()
            if res:
                print(f"Paper {arxiv_id} exists. Has embedding: {res[1]}")
            else:
                print(f"Paper {arxiv_id} DOES NOT EXIST in DB.")
                
    db.close()

if __name__ == "__main__":
    check()
