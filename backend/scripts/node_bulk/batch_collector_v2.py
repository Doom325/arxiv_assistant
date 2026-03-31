from google import genai
import os
import sys
import argparse
from dotenv import load_dotenv
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
import json
import re
import requests

# App root path
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(ROOT_DIR, 'backend'))

try:
    from models import Paper, CitationLink
except ImportError:
    print("⚠️ Could not import Paper/CitationLink models directly, using table reflection.")

load_dotenv(os.path.join(ROOT_DIR, '.env'))

API_KEY = (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").replace('"', '').strip()
# Use environment's DATABASE_URL as is
DATABASE_URL = os.getenv("DATABASE_URL")

def extract_arxiv_id(text):
    if not text: return None
    # Match 2401.12345 or cond-mat/0101123
    match = re.search(r'(\d{4}\.\d{4,5}(v\d+)?)|([a-z\-]+\/\d{7}(v\d+)?)|(abs\/\d{4}\.\d{4,5})', text, re.IGNORECASE)
    if match:
        res = match.group(0)
        if 'abs/' in res.lower():
            return res.lower().split('abs/')[-1]
        return res
    return None

def process_completed_job(job_id):
    print(f"🚀 Processing completed job: {job_id}")
    client = genai.Client(api_key=API_KEY, http_options={'api_version': 'v1beta'})
    
    engine = sa.create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        job = client.batches.get(name=job_id)
        print(f"Job State: {job.state}")
        
        if job.state not in ['SUCCEEDED', 'JOB_STATE_SUCCEEDED', 'BATCH_STATE_SUCCEEDED']:
            print(f"Job is not SUCCEEDED yet. Current state: {job.state}")
            return

        # Get output file names
        output_file_id = None
        
        # Try metadata or response fields
        if hasattr(job, 'response') and job.response and hasattr(job.response, 'responses_file'):
            output_file_id = job.response.responses_file
        elif hasattr(job, 'metadata') and 'output' in job.metadata and 'responsesFile' in job.metadata['output']:
            output_file_id = job.metadata['output']['responsesFile']
        
        # Fallback to direct REST check if SDK field access is tricky
        if not output_file_id:
            url = f"https://generativelanguage.googleapis.com/v1beta/{job_id}?key={API_KEY}"
            resp = requests.get(url)
            data = resp.json()
            output_file_id = data.get('response', {}).get('responsesFile') or \
                             data.get('metadata', {}).get('output', {}).get('responsesFile')
        
        if not output_file_id:
            print(f"❌ Could not find output file ID. Job data: {job}")
            return

        # Construct download URL
        # output_file_id is like 'files/batch-xxx'
        output_uri = f"https://generativelanguage.googleapis.com/v1beta/{output_file_id}?alt=media&key={API_KEY}"
        
        print(f"Downloading results from {output_uri.split('?')[0]}...")
        results_resp = requests.get(output_uri)
        results_resp.raise_for_status()
        
        lines = results_resp.text.strip().split('\n')
        print(f"Processing {len(lines)} results...")

        success_count = 0
        for line in lines:
            if not line.strip(): continue
            try:
                result = json.loads(line)
                custom_id = result.get('custom_id')
                paper_id = int(custom_id.replace('paper_', ''))
                
                if 'response' in result and 'candidates' in result['response']:
                    content = result['response']['candidates'][0]['content']['parts'][0]['text']
                    # Clean markdown
                    clean_json = re.sub(r'```json\n?|\n?```', '', content).strip()
                    citations = json.loads(clean_json)

                    # Update papers table using SQL directly to avoid ORM overhead for bulk
                    db.execute(
                        sa.text("UPDATE papers SET citations = :cit WHERE id = :pid"),
                        {"cit": json.dumps(citations), "pid": paper_id}
                    )

                    # Resolve citations
                    for cit in citations:
                        resolved_id = extract_arxiv_id(cit.get('raw', ''))
                        if resolved_id:
                            # Check if exists locally
                            linked = db.execute(
                                sa.text("SELECT id FROM papers WHERE arxiv_id = :aid"),
                                {"aid": resolved_id}
                            ).fetchone()
                            
                            if linked:
                                db.execute(
                                    sa.text("""
                                        INSERT INTO citation_links (source_paper_id, resolved_paper_id, arxiv_id, title)
                                        VALUES (:src, :res, :aid, :title)
                                        ON CONFLICT DO NOTHING
                                    """),
                                    {"src": paper_id, "res": linked[0], "aid": resolved_id, "title": cit.get('title')}
                                )

                    # Mark tracker as completed
                    db.execute(
                        sa.text("UPDATE bulk_process_tracker SET status = 'completed' WHERE paper_id = :pid"),
                        {"pid": paper_id}
                    )
                    success_count += 1
            except Exception as e:
                print(f"Error processing line for paper: {e}")

        db.commit()
        print(f"✅ Successfully synced {success_count} papers from job {job_id}.")

    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", help="Specific Job ID (e.g. models/gemini-2.0.../batches/xxx)")
    args = parser.parse_args()
    
    if args.job:
        process_completed_job(args.job)
    else:
        # Fetch all queued jobs from tracker and check them
        engine = sa.create_engine(DATABASE_URL)
        conn = engine.connect()
        jobs = conn.execute(sa.text("SELECT DISTINCT batch_job_id FROM bulk_process_tracker WHERE status = 'queued_batch'")).fetchall()
        conn.close()
        
        for job_row in jobs:
            process_completed_job(job_row[0])
