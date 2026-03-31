from google import genai
import os
import sys
import argparse
from dotenv import load_dotenv

# App root path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(ROOT_DIR, '.env'))

API_KEY = (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").replace('"', '').strip()

def submit_batch(file_path, model_name):
    client = genai.Client(api_key=API_KEY, http_options={'api_version': 'v1beta'})
    
    print(f"Uploading {file_path} to Gemini...")
    # Get absolute path
    abs_path = os.path.abspath(file_path)
    
    with open(abs_path, "rb") as f:
        # Note: display_name instead of name
        gemini_file = client.files.upload(
            file=f, 
            config={
                'display_name': 'bulk_backfill_jsonl',
                'mime_type': 'application/json'
            }
        )
    
    print(f"✅ Upload successful. File ID: {gemini_file.name}")
    
    print(f"Submitting Batch Job for model {model_name}...")
    # Use the file ID (e.g. files/xxx)
    batch_job = client.batches.create(
        model=model_name,
        src=gemini_file.name
    )
    
    return batch_job.name

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True)
    parser.add_argument("--model", default="models/gemini-2.0-flash-lite-preview-02-05")
    args = parser.parse_args()
    
    if not API_KEY:
        print("❌ Error: GEMINI_API_KEY not found in environment.")
        sys.exit(1)

    try:
        job_id = submit_batch(args.file, args.model)
        print(f"🚀 Batch Job Submitted! Job ID: {job_id}")
        # Print just the job ID at the end for the Node wrapper to capture if needed
        print(f"JOB_ID:{job_id}")
    except Exception as e:
        print(f"❌ Batch Submission Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
