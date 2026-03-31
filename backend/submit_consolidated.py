
from batch_embed_manager import BatchEmbedManager
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Submitter")

def submit():
    manager = BatchEmbedManager()
    files = ["consolidated_batch_1.jsonl", "consolidated_batch_2.jsonl"]
    
    for f in files:
        logger.info(f"Waiting for {f} to be ready...")
        # Wait for file to exist and size to stabilize
        while not os.path.exists(f):
            time.sleep(30)
        
        last_size = -1
        while True:
            current_size = os.path.getsize(f)
            if current_size == last_size and current_size > 0:
                break
            last_size = current_size
            logger.info(f"File {f} is growing ({current_size} bytes)...")
            time.sleep(60)

        logger.info(f"Submitting {f}...")
        job_name = manager.submit_batch(f)
        if job_name:
            logger.info(f"Successfully submitted {f} as job: {job_name}")
        else:
            logger.error(f"Failed to submit {f}")
        
        # Wait between submissions to avoid quota issues
        time.sleep(60)

if __name__ == "__main__":
    submit()
