import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from google import genai
from config import settings
import json
import os

def reconstruct():
    client = genai.Client(api_key=settings.FINAL_GOOGLE_API_KEY)
    print("Reconstructing batch_embedding_jobs.json...")
    
    jobs = {}
    for batch in client.batches.list():
        display_name = "N/A"
        if hasattr(batch, 'display_name'):
            display_name = batch.display_name
        elif hasattr(batch, 'config') and hasattr(batch.config, 'display_name'):
            display_name = batch.config.display_name
        
        # Strip the prefix if present
        filename = display_name
        if filename.startswith("Arxiv-Backfill-"):
            filename = filename.replace("Arxiv-Backfill-", "")
        
        # Metadata
        status = "ACTIVE"
        state_str = str(batch.state)
        if any(s in state_str for s in ["SUCCEEDED", "COMPLETED"]):
            status = "COMPLETED"
        elif any(s in state_str for s in ["FAILED"]):
            status = "FAILED"
            
        jobs[batch.name] = {
            "filename": filename,
            "status": status,
            "created_at": str(batch.create_time)
        }
        print(f"Adding Job: {batch.name} -> {filename} ({status})")

    with open("batch_embedding_jobs.json", "w") as f:
        json.dump(jobs, f, indent=4)
    print("Done!")

if __name__ == "__main__":
    reconstruct()
