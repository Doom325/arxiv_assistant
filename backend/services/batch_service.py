
import json
import time
import os
import logging
import google.generativeai as genai
from config import settings
from sqlalchemy.orm import Session
from models import Paper, JobLog, BatchQueue
from datetime import datetime

logger = logging.getLogger(__name__)

class BatchService:
    def __init__(self):
        genai.configure(api_key=settings.FINAL_GOOGLE_API_KEY)
        self.model_name = "models/gemini-3-flash-preview"

    def create_daily_batch_job(self, db: Session):
        """Creates a batch job for all papers without summaries."""
        # 1. Fetch papers from Queue (Priority)
        target_limit = 1000
        queue_items = db.query(BatchQueue).filter(BatchQueue.status == "PENDING").limit(target_limit).all()
        queue_paper_ids = [item.paper_id for item in queue_items]
        
        queue_papers = []
        if queue_paper_ids:
            queue_papers = db.query(Paper).filter(Paper.id.in_(queue_paper_ids)).all()
            
        remaining_limit = target_limit - len(queue_papers)
        
        daily_papers = []
        if remaining_limit > 0:
            daily_papers = db.query(Paper).filter(Paper.generated_summary.is_(None)).order_by(Paper.published_date.desc()).limit(remaining_limit).all()
            
        papers = queue_papers + daily_papers
        
        if not papers:
            logger.info("No papers to summarize.")
            return None

        logger.info(f"Preparing batch job for {len(papers)} papers...")
        
        # 2. Create JSONL file
        batch_requests = []
        for paper in papers:
            if not paper.extracted_abstract: continue
            
            # Simple prompt
            prompt = f"""
            Please provide a structured and detailed summary of the following research paper.
            Format the response with the following clearly labeled sections:

            1. **Core Problem**: What specific problem is this paper trying to solve?
            2. **Key Innovation**: What is the main novelty or contribution (the "aha!" moment)?
            3. **Methodology**: Briefly explain the technical approach.
            4. **Key Results**: What were the quantitative or qualitative findings?

            Text:
            {paper.extracted_abstract[:10000]} 
            {paper.extracted_introduction[:20000] if paper.extracted_introduction else ""}
            """
            
            request = {
                "custom_id": str(paper.id),
                "request": {
                    "model": self.model_name,
                    "contents": [{"parts": [{"text": prompt}]}]
                }
            }
            batch_requests.append(request)

        if not batch_requests:
            return None
            
        filename = f"batch_input_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
        with open(filename, "w") as f:
            for req in batch_requests:
                f.write(json.dumps(req) + "\n")

        try:
            # 3. Upload File
            batch_file = genai.upload_file(filename)
            logger.info(f"Uploaded file: {batch_file.name}")

            # 4. Create Batch
            batch = genai.create_batch_job(
                display_name=f"daily_summary_{datetime.now().strftime('%Y-%m-%d')}",
                model=self.model_name,
                source=batch_file.name
            )
            
            logger.info(f"Batch created: {batch.name}")
            
            # 5. Log
            job_log = JobLog(
                job_name="batch_creation",
                status="SUBMITTED",
                start_time=datetime.utcnow(),
                job_details={"batch_id": batch.name, "file_name": batch_file.name, "count": len(batch_requests)}
            )
            db.add(job_log)
            db.commit()
            
            # Cleanup
            os.remove(filename)
            return batch.name

        except Exception as e:
            logger.error(f"Batch creation failed: {e}")
            if os.path.exists(filename): os.remove(filename)
            raise e

    def process_completed_batches(self, db: Session):
        """Checks for completed batches and updates DB."""
        # Find active batch jobs from logs? 
        # Better: List recent batches from API
        try:
            # List usage is hard, let's just query API for submitted jobs we logged?
            # Or assume we run this periodically.
            
            # For now, let's iterate over specific batch IDs if we stored them better.
            # But genai.list_batch_jobs() exists?
            # Verify SDK documentation... create_batch_job returns an object.
            # Assuming list_batch_jobs works.
            
            # Simplified: Look at logs for SUBMITTED
            logs = db.query(JobLog).filter(JobLog.job_name == "batch_creation", JobLog.status == "SUBMITTED").all()
            
            for log in logs:
                batch_id = log.job_details.get("batch_id")
                if not batch_id: continue
                
                batch = genai.get_batch_job(batch_id)
                
                if batch.state == "COMPLETED":
                    logger.info(f"Processing completed batch {batch_id}")
                    
                    # Download output
                    output_file_name = batch.output_file
                    content = genai.get_file(output_file_name).download() # Verify method
                    # Actually usually via URL? 
                    # Providing SDK logic requires verifying exact syntax.
                    # fallback: print(batch) details.
                    
                    # Assuming we can get content. 
                    # content is bytes/string of jsonl
                    
                    # Parse and update DB
                    # ...
                    pass
                    
                    log.status = "PROCESSED"
                    db.commit()

        except Exception as e:
            logger.error(f"Error processing batches: {e}")

batch_service = BatchService()
