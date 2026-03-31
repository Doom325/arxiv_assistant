
from google import genai
from config import settings
from datetime import datetime
import json

def list_jobs():
    client = genai.Client(api_key=settings.FINAL_GOOGLE_API_KEY)
    print("Fetching all batch jobs...")
    jobs = list(client.batches.list())
    print(f"Total jobs found: {len(jobs)}")
    jobs.sort(key=lambda x: x.create_time, reverse=True)
    
    print("Most recent 50 batch jobs:")
    for batch in jobs[:50]:
        display_name = "N/A"
        if hasattr(batch, 'display_name'):
            display_name = batch.display_name
        elif hasattr(batch, 'config') and hasattr(batch.config, 'display_name'):
            display_name = batch.config.display_name
        
        print(f"Name: {batch.name}, State: {batch.state}, DisplayName: {display_name}, Created: {batch.create_time}")

if __name__ == "__main__":
    list_jobs()
