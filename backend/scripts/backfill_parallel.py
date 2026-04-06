#!/usr/bin/env python3
"""
Multithreaded Pattern Backfill Script using Option B (NUM_PARALLEL=4)
Execution target: python3 scripts/backfill_parallel.py
"""

import argparse
import hashlib
import json
import time
import requests
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from queue import Queue

from config import settings
from sqlalchemy import create_engine, text as sa_text
from sqlalchemy.orm import sessionmaker
from models import PatternExperimentResult
from taxonomy import PROMPT_VERSION, V6_COT_PROMPT, validate_classification_output
from core.text_utils import sanitize_text

# Global DB Engine
engine_kwargs = {"pool_size": 20, "max_overflow": 30} if "postgresql" in settings.DATABASE_URL else {}
engine = create_engine(settings.DATABASE_URL, **engine_kwargs)
PatternExperimentResult.__table__.create(engine, checkfirst=True)
SessionLocal = sessionmaker(bind=engine)

# Queue-based thread-safe logging
log_queue = Queue()

def log_writer():
    """Background thread for thread-safe JSONL appending."""
    with open("backfill_metrics.jsonl", "a") as f:
        while True:
            msg = log_queue.get()
            if msg is None:  # Sentinel to stop
                break
            f.write(json.dumps(msg) + "\n")
            f.flush()
            log_queue.task_done()

def get_partition(arxiv_id: str, num_workers: int) -> int:
    """Deterministic, resume-safe partitioning across N workers using MD5 hash."""
    digest = hashlib.md5(arxiv_id.encode('utf-8')).hexdigest()
    return int(digest[:8], 16) % num_workers

def classify_paper_raw(title: str, abstract: str, session: requests.Session) -> dict | None:
    """Format prompt & raw POST to Ollama. Bypass singleton llm_service."""
    safe_title = sanitize_text(title or "")
    safe_abstract = sanitize_text(abstract or "")
    
    prompt = V6_COT_PROMPT.format(title=safe_title, abstract=safe_abstract)
    
    payload = {
        "model": "gemma3:12b",  # Hardcoded model
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {
            "num_ctx": 4096,
            "temperature": 0.1
        },
        "format": "json",
        "keep_alive": "30m"
    }
    
    try:
        # T2.3: POST through mitmproxy locally port 8434
        url = "http://localhost:8434/api/chat"
        res = session.post(url, json=payload, timeout=120)
        res.raise_for_status()
        data = res.json()
        content = data.get("message", {}).get("content", "{}")
        # Ensure json load works
        parsed_content = json.loads(content)
        
        # Include metadata for telemetry
        parsed_content["_meta"] = {
            "eval_count": data.get("eval_count"),
            "prompt_eval_count": data.get("prompt_eval_count"),
            "eval_duration": data.get("eval_duration", 0) / 1e9, # Nanoseconds -> seconds
        }
        return parsed_content
    except Exception as e:
        return {"_error": str(e)}

# Progress tracking globals
progress_lock = threading.Lock()
stats = {"total": 0, "processed": 0, "errors": 0, "total_eval_count": 0, "total_elapsed": 0.0}

def worker_process(worker_id: int, papers: list, is_dry_run: bool):
    """Worker thread that processes its specific partition."""
    # Setup independent connection pools for this thread
    http_session = requests.Session()
    
    if not papers:
        print(f"[Worker {worker_id}] No papers assigned. Exiting.")
        return

    for idx, (arxiv_id, title, abstract) in enumerate(papers):
        start_time = time.time()
        parsed = classify_paper_raw(title, abstract, http_session)
        elapsed = time.time() - start_time
        
        if is_dry_run:
            print(f"[Worker {worker_id}] DRY RUN: {arxiv_id} processed in {elapsed:.2f}s")
            continue
            
        error_msg = parsed.get("_error") if parsed else "Failed to parse json"
        meta = parsed.pop("_meta", {}) if parsed and not error_msg else {}
        
        icon = "✅"
        result = None
        
        if error_msg:
            result = PatternExperimentResult(
                arxiv_id=arxiv_id,
                paper_title=title[:200] if title else None,
                prompt_version=PROMPT_VERSION,
                model_name="gemma3:12b-parallel-backfill",  # T2.4: Safely tagged
                num_violations=1,
                taxonomy_violations=["PARSE_FAILED"],
                elapsed_seconds=elapsed,
                error=error_msg,
            )
            icon = "💥"
        else:
            issues = validate_classification_output(parsed)
            result = PatternExperimentResult(
                arxiv_id=arxiv_id,
                paper_title=title[:200] if title else None,
                prompt_version=PROMPT_VERSION,
                model_name="gemma3:12b-parallel-backfill",
                is_agentic=parsed.get("is_agentic"),
                primary_category=parsed.get("primary_category"),
                reasoning=parsed.get("reasoning"),
                patterns=parsed.get("patterns"),
                raw_json=parsed,
                num_patterns=len(parsed.get("patterns", [])),
                taxonomy_violations=issues if issues else None,
                num_violations=len(issues),
                elapsed_seconds=elapsed,
            )
            if issues: 
                icon = "⚠️"

        # Micro-commit directly
        db = SessionLocal()
        try:
            db.add(result)
            db.commit()
        except Exception as e:
            db.rollback()
            error_msg = str(e)
            icon = "💥"
        finally:
            db.close()
        
        eval_count = meta.get("eval_count", 0)
        tps = (eval_count / meta.get("eval_duration", 1)) if meta.get("eval_duration", 0) > 0 else 0
        
        log_msg = {
            "timestamp": datetime.now().isoformat(),
            "worker_id": worker_id,
            "arxiv_id": arxiv_id,
            "elapsed_seconds": elapsed,
            "status": "success" if icon != "💥" else "error",
            "eval_count": eval_count,
            "prompt_eval_count": meta.get("prompt_eval_count", 0),
            "tokens_per_sec": round(tps, 2),
            "error_message": error_msg if error_msg else None
        }
        log_queue.put(log_msg)
        
        # Update global stats
        with progress_lock:
            stats["processed"] += 1
            if log_msg["status"] == "error":
                stats["errors"] += 1
            stats["total_eval_count"] += eval_count
            stats["total_elapsed"] += elapsed
            
            avg_lat = stats["total_elapsed"] / stats["processed"]
            eta_mins = ((stats["total"] - stats["processed"]) * avg_lat) / 60 / 4 # approximated
            print(f"[Worker {worker_id}] {idx+1:>3}/{len(papers)} {icon} {elapsed:>4.1f}s | {arxiv_id} | ETA: {eta_mins:.1f}m")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--category", type=str, required=True)
    parser.add_argument("--start", type=str, required=True, help="YYYY-MM-DD")
    parser.add_argument("--end", type=str, required=True, help="YYYY-MM-DD")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--dry-run", action="store_true", help="Process but don't commit to DB")
    args = parser.parse_args()

    # Start writer thread
    writer_thread = threading.Thread(target=log_writer, daemon=True)
    writer_thread.start()

    db = SessionLocal()
    where_clause = """
        p.category = :cat
        AND p.published_date >= :start
        AND p.published_date <= :end
        AND r.id IS NULL
    """
    
    print("Querying unclassified papers...")
    rows = db.execute(sa_text(f"""
        SELECT p.arxiv_id, p.title, COALESCE(p.extracted_abstract, p.summary) as abstract
        FROM papers p
        LEFT JOIN pattern_experiment_results r ON p.arxiv_id = r.arxiv_id AND r.prompt_version = :pv
        WHERE {where_clause}
          AND COALESCE(p.extracted_abstract, p.summary) IS NOT NULL
        ORDER BY p.published_date DESC
    """), {"pv": PROMPT_VERSION, "cat": args.category, "start": args.start, "end": args.end}).fetchall()
    
    db.close()

    seen = set()
    deduped = []
    for r in rows:
        aid = r[0]
        if aid not in seen:
            deduped.append((aid, r[1], (r[2] or "")[:800]))
            seen.add(aid)
            
    stats["total"] = len(deduped)
    print(f"Assigning {len(deduped)} papers into {args.workers} partitions...")
    
    partitions = {i: [] for i in range(args.workers)}
    for p in deduped:
        w_id = get_partition(p[0], args.workers)  # T2.2: Deterministic Partition
        partitions[w_id].append(p)
    
    for i, p_list in partitions.items():
        print(f"Worker {i} assigned {len(p_list)} papers")
        
    print(f"\nStarting ThreadPoolExecutor workers={args.workers} (dry_run={args.dry_run})...")
    start_global = time.time()
    
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        for i in range(args.workers):
            executor.submit(worker_process, i, partitions[i], args.dry_run)
            
    # Cleanup
    log_queue.put(None)
    writer_thread.join()
    
    # Summary T2.6
    total_time = time.time() - start_global
    print("\n--- Backfill Complete ---")
    print(f"Processed: {stats['processed']} papers")
    print(f"Errors:    {stats['errors']}")
    print(f"Total Time:{total_time:.2f}s")
    if stats["total_elapsed"] > 0:
        print(f"Avg tokens/sec: {stats['total_eval_count'] / stats['total_elapsed']:.2f}")

if __name__ == "__main__":
    main()
