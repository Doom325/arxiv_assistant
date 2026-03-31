import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import json
import os
from batch_embed_manager import BatchEmbedManager
from database import SessionLocal
from models import Paper

def test_submission():
    manager = BatchEmbedManager()
    db = SessionLocal()
    
    # Take 10 papers that are not corrupted and have extracted text
    papers = db.query(Paper).filter(Paper.extracted_abstract.isnot(None)).limit(10).all()
    
    if not papers:
        print("No papers found with extracted text for testing.")
        return

    current_batch = []
    for paper in papers:
        content = f"{paper.title} {paper.extracted_abstract}"
        request = {
            "task_type": "RETRIEVAL_DOCUMENT",
            "content": {"parts": [{"text": content}]},
            "title": paper.title,
            "output_dimensionality": 768
        }
        current_batch.append({
            "request": request,
            "metadata": {"key": paper.arxiv_id}
        })
    
    filename = "test_batch.jsonl"
    with open(filename, "w") as f:
        for entry in current_batch:
            f.write(json.dumps(entry) + "\n")
    
    print(f"Generated {filename}. Submitting...")
    job_name = manager.submit_batch(filename)
    if job_name:
        print(f"Test batch submitted successfully: {job_name}")
    else:
        print("Test batch submission failed.")
    
    db.close()

if __name__ == "__main__":
    test_submission()
