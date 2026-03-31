import os
import time
import logging
from batch_embed_manager import BatchEmbedManager

# Configure logging to show up in stdout
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def process_chunks():
    manager = BatchEmbedManager()
    
    # Source file logic
    source_file = "/app/batch_input_23.jsonl.bak"
    if not os.path.exists(source_file):
        logger.error(f"Source file {source_file} not found!")
        return

    logger.info(f"Reading source file: {source_file}")
    with open(source_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    total_lines = len(lines)
    logger.info(f"Total requests in source: {total_lines}")
    
    # We already processed the first 1000 requests successfully as Batch 25 (lines 0-999).
    # So we start from index 1000.
    start_index = 1000 
    chunk_size = 1000
    
    # Start numbering from 28 to avoid conflicts with previous test batches (23, 24, 25, 26, 27)
    current_batch_num = 28
    
    for i in range(start_index, total_lines, chunk_size):
        chunk = lines[i : i + chunk_size]
        batch_filename = f"batch_input_{current_batch_num}.jsonl"
        
        logger.info(f"Preparing {batch_filename} with {len(chunk)} requests (Offset: {i})...")
        
        with open(batch_filename, "w", encoding="utf-8") as f_out:
            f_out.writelines(chunk)
            
        logger.info(f"Submitting {batch_filename}...")
        
        # Submit the batch
        job_id = manager.submit_batch(batch_filename)
        
        if job_id:
            logger.info(f"SUCCESS: {batch_filename} -> Job ID: {job_id}")
            logger.info("Waiting 30 seconds to respect API rate limits...")
            time.sleep(30)
        else:
            logger.error(f"FAILED: Submission for {batch_filename} failed.")
            logger.error("Stopping submission loop to prevent cascading failures.")
            break
            
        current_batch_num += 1

if __name__ == "__main__":
    process_chunks()
