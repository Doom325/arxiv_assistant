"""Submit batch files one at a time, waiting for each to complete before submitting the next."""
import time
import sys
import glob
import os

os.environ["DATABASE_URL"] = "postgresql://user:password@192.168.1.49:5434/arxiv_db"

from batch_embed_manager import BatchEmbedManager

m = BatchEmbedManager()

# Find all unsubmitted part files
jobs = m._load_jobs()
tracked = {info["filename"] for info in jobs.values()}

pattern = sys.argv[1] if len(sys.argv) > 1 else "batch_*_part_*.jsonl"
files = sorted(glob.glob(pattern))
unsubmitted = [f for f in files if f not in tracked]
print(f"Found {len(unsubmitted)} unsubmitted files")

for i, f in enumerate(unsubmitted):
    print(f"\n[{i+1}/{len(unsubmitted)}] Submitting: {f}")
    
    # Wait for any active jobs to complete first
    while True:
        jobs = m._load_jobs()
        active = {n: info for n, info in jobs.items() if info["status"] == "ACTIVE"}
        if not active:
            break
        for name, info in active.items():
            try:
                job = m.client.batches.get(name=name)
                state = str(job.state)
                if "SUCCEEDED" in state or "COMPLETED" in state:
                    print(f"  ✓ {info['filename']} completed")
                    info["status"] = "COMPLETED"
                    m._save_jobs(jobs)
                elif "FAILED" in state:
                    print(f"  ✗ {info['filename']} FAILED")
                    info["status"] = "FAILED"
                    m._save_jobs(jobs)
                else:
                    print(f"  ⏳ Waiting for {info['filename']}...")
            except Exception as e:
                print(f"  Error: {e}")
        jobs = m._load_jobs()
        if any(info["status"] == "ACTIVE" for info in jobs.values()):
            time.sleep(30)
    
    result = m.submit_batch(f)
    if not result:
        print(f"Failed to submit {f}, stopping.")
        sys.exit(1)

# Wait for last job
print("\nWaiting for last job to complete...")
while True:
    jobs = m._load_jobs()
    active = {n: info for n, info in jobs.items() if info["status"] == "ACTIVE"}
    if not active:
        break
    for name, info in active.items():
        try:
            job = m.client.batches.get(name=name)
            state = str(job.state)
            if "SUCCEEDED" in state or "COMPLETED" in state:
                print(f"  ✓ {info['filename']} completed")
                info["status"] = "COMPLETED"
                m._save_jobs(jobs)
            elif "FAILED" in state:
                print(f"  ✗ {info['filename']} FAILED")
                info["status"] = "FAILED"
                m._save_jobs(jobs)
            else:
                print(f"  ⏳ Waiting for {info['filename']}...")
        except Exception as e:
            print(f"  Error: {e}")
    jobs = m._load_jobs()
    if any(info["status"] == "ACTIVE" for info in jobs.values()):
        time.sleep(30)

# Re-download and ingest results for this run's files
print("\n\nAll jobs complete! Downloading and ingesting results...")
jobs = m._load_jobs()
submitted_files = sorted(glob.glob(pattern))
for f in submitted_files:
    for name, info in jobs.items():
        if info["filename"] == f and info["status"] == "COMPLETED":
            try:
                job = m.client.batches.get(name=name)
                if job.dest and job.dest.file_name:
                    local_file = f"results_{name.split('/')[-1]}.jsonl"
                    print(f"Downloading {f} -> {local_file}...")
                    content = m.client.files.download(file=job.dest.file_name)
                    with open(local_file, "wb") as out:
                        out.write(content)
                    m.ingest_category_results(local_file)
            except Exception as e:
                print(f"Error ingesting {f}: {e}")
            break

print("\nDone!")
