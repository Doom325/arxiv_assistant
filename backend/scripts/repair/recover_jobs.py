import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import os
import json
import logging
from google import genai
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def recover():
    client = genai.Client(api_key=settings.FINAL_GOOGLE_API_KEY)
    
    logger.info("Listing recent batch jobs from Gemini...")
    jobs = {}
    
    # List all batches
    batches = client.batches.list()
    
    for batch in batches:
        # Filter for our backfill batches
        # Display name is like "Arxiv-Backfill-batch_input_1.jsonl"
        display_name = getattr(batch, 'display_name', '')
        if display_name and "Arxiv-Backfill-" in display_name:
            filename = display_name.replace("Arxiv-Backfill-", "")
            status = "ACTIVE"
            # If the batch has a state/status, we can use it.
            # Batch object has 'state' (ACTIVE, SUCCEEDED, FAILED, etc.)
            state = str(batch.state)
            if "SUCCEEDED" in state:
                status = "COMPLETED"
            elif "FAILED" in state or "EXPIRED" in state:
                status = "FAILED"
            
            jobs[batch.name] = {
                "filename": filename,
                "file_name": batch.src.file_name if hasattr(batch.src, 'file_name') else "unknown",
                "status": status,
                "created_at": str(batch.create_time)
            }
            logger.info(f"Recovered job: {display_name} | Status: {status} | ID: {batch.name}")

    if jobs:
        with open("batch_embedding_jobs.json", "w") as f:
            json.dump(jobs, f, indent=4)
        logger.info(f"Successfully recovered {len(jobs)} jobs to batch_embedding_jobs.json")
    else:
        logger.warning("No Arxiv-Backfill batches found in Gemini account.")

if __name__ == "__main__":
    recover()
