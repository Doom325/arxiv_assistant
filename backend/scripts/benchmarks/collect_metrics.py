import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import os
import time
import json
import psutil
import logging
import threading
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Paper, SummarizationMetric
from services.summarization_service import summarization_service

# Configure Logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MetricsCollector")

DB_URL = "postgresql://user:password@localhost:5434/arxiv_db" # Mac Local
from config import settings
PDF_DIR = settings.PDF_SAVE_DIR or "/app/data"

engine = create_engine(DB_URL)
SessionLocal = sessionmaker(bind=engine)

# Try to get MLX Memory
try:
    import mlx.core as mx
    HAS_MLX = True
except ImportError:
    HAS_MLX = False

class MemoryMonitor(threading.Thread):
    def __init__(self, interval=0.1):
        super().__init__()
        self.interval = interval
        self.keep_running = True
        self.peak_system_ram = 0
        self.peak_metal_ram = 0
        self.process = psutil.Process(os.getpid())

    def run(self):
        while self.keep_running:
            # 1. System RAM (RSS)
            mem = self.process.memory_info().rss
            if mem > self.peak_system_ram:
                self.peak_system_ram = mem
            
            # 2. Metal Usage (Unified Memory for MLX)
            if HAS_MLX:
                try:
                    # Active memory in Metal
                    metal_mem = mx.metal.get_active_memory()
                    if metal_mem > self.peak_metal_ram:
                        self.peak_metal_ram = metal_mem
                except Exception:
                    pass
            
            time.sleep(self.interval)

    def stop(self):
        self.keep_running = False

    def get_peak_mb(self):
        # We report the MAX of System RAM or Metal RAM, or sum?
        # In Unified Memory, MLX allocations count towards process footprint usually?
        # But User says "numbers inaccurate".
        # Let's verify: 
        # MLX `mx.metal.get_peak_memory()` returns peak since start? Or we poll `get_active_memory`.
        # Taking the sum might double count if RSS includes it. 
        # But if RSS was ~500MB and Model is 2GB, RSS is definitely NOT counting it.
        # So Metal is allocated outside Python heap.
        # Let's assume we sum them or report both?
        # Database schema has `peak_memory_mb` (Float).
        # Let's save the SUM for now as "Total Footprint".
        
        sys_mb = self.peak_system_ram / (1024 * 1024)
        metal_mb = self.peak_metal_ram / (1024 * 1024)
        total_mb = sys_mb + metal_mb
        return total_mb, sys_mb, metal_mb

def get_pdf_path(arxiv_id):
    path = os.path.join(PDF_DIR, f"{arxiv_id}.pdf")
    if os.path.exists(path): return path
    base = arxiv_id.split("v")[0]
    path = os.path.join(PDF_DIR, f"{base}.pdf")
    if os.path.exists(path): return path
    return None

def collect_metrics():
    logger.info("Starting Metrics Collection (Decile Strategy)...")
    
    # Load Queue
    queue_path = "benchmark_queue.json"
    if not os.path.exists(queue_path):
        logger.error(f"Queue not found: {queue_path}. Run prepare_benchmark.py first.")
        return

    with open(queue_path, 'r') as f:
        chunks = json.load(f)

    # Flatten queue: List of (decile, paper_id)
    queue_items = []
    for chunk in chunks:
        for pid in chunk['samples']:
            queue_items.append((chunk['decile'], pid))

    logger.info(f"Loaded {len(queue_items)} papers from queue.")
    
    db = SessionLocal()
    
    for decile, arxiv_id in queue_items:
        try:
            # Check if already done
            exists = db.query(SummarizationMetric).filter(SummarizationMetric.paper_id == arxiv_id).first()
            if exists:
                logger.info(f"Skipping {arxiv_id} (Already Done)")
                continue

            pdf_path = get_pdf_path(arxiv_id)
            if not pdf_path:
                logger.warning(f"PDF missing for {arxiv_id}, skipping.")
                continue

            logger.info(f"Processing Decile {decile} | {arxiv_id}...")
            
            # Get File Size (proxy for complexity/length?)
            file_size = os.path.getsize(pdf_path)
            file_size_mb = file_size / (1024 * 1024)

            # Start Monitor
            monitor = MemoryMonitor(interval=0.05)
            monitor.start()
            
            result = None
            error_msg = None
            try:
                result = summarization_service.generate_summary_with_metrics(pdf_path)
            except Exception as e:
                logger.error(f"Generation failed for {arxiv_id}: {e}")
                error_msg = str(e)
            finally:
                monitor.stop()
                monitor.join()

            total_mb, sys_mb, metal_mb = monitor.get_peak_mb()
            
            if result:
                logger.info(f"Generated. PDF: {file_size_mb:.2f}MB. Peak: {total_mb:.2f} MB")
                status = "SUCCESS"
                n_chars = result['num_chars']
                n_in = result['num_input_tokens']
                n_out = result['num_output_tokens']
            else:
                logger.warning(f"Failed. PDF: {file_size_mb:.2f}MB. Peak: {total_mb:.2f} MB. Error: {error_msg}")
                status = "FAILED"
                n_chars = 0
                n_in = 0
                n_out = 0

            metric = SummarizationMetric(
                paper_id=arxiv_id,
                file_size_bytes=file_size,
                num_chars=n_chars,
                num_input_tokens=n_in,
                num_output_tokens=n_out,
                peak_memory_mb=total_mb, 
                model_name="gemma-3-4b-it-4bit",
                status=status,
                error_message=error_msg
            )
            db.add(metric)
            db.commit()
            
            # Cooldown
            time.sleep(1)

        except Exception as e:
            logger.error(f"Loop error: {e}")
            db.rollback()
        
    logger.info("Benchmark Queue Complete.")
    db.close()

if __name__ == "__main__":
    collect_metrics()
