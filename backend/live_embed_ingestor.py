import os
import json
import asyncio
import time
import queue
import threading
import logging
import signal
import argparse
from typing import List, Dict, Any, Optional
from datetime import datetime

import google.generativeai as genai
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker
from google.protobuf.json_format import MessageToDict

# Project local imports
from models import Base, Paper, PaperEmbedding, PromptTemplate
from services.prompts import PROMPT_REGISTRY
from protos import embeddings_pb2

# Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(threadName)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_QPS = 50
BATCH_SIZE = 100
MAX_QUEUE_SIZE = 1000
MODEL_NAME = "models/gemini-embedding-001" # This is the internal name for gemini-embedding-001 often
# Wait, based on my previous research, gemini-embedding-001 is the name.
# Let's double check the model list if needed, but I'll make it configurable.

class LiveEmbedIngestor:
    def __init__(self, jsonl_path: str, db_url: str, api_key: str, qps: int = 160, model: str = MODEL_NAME):
        self.jsonl_path = jsonl_path
        self.db_url = db_url
        self.api_key = api_key
        self.qps = qps
        self.model_name = model
        
        # Rate limiting
        self.semaphore = asyncio.Semaphore(qps)
        self.last_request_time = 0
        self.rate_limit_interval = 1.0 / qps
        
        # Threading & Queues
        self.result_queue = queue.Queue(maxsize=MAX_QUEUE_SIZE)
        self.stop_event = threading.Event()
        
        # Database
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
        
        # Prompt Setup
        self.template_name = "gemini_retrieval_v1"
        self.template_info = PROMPT_REGISTRY[self.template_name]
        self.prompt_template_id = self._sync_prompt_template()
        
        # Stats
        self.total_processed = 0
        self.total_success = 0
        self.total_failed = 0
        self.start_time = time.time()
        
        # GenAI
        genai.configure(api_key=api_key)

    def _sync_prompt_template(self) -> int:
        """Ensures the current prompt template is in the DB."""
        session = self.Session()
        try:
            template = session.query(PromptTemplate).filter_by(
                name=self.template_name,
                version_tag=self.template_info["version"]
            ).first()
            
            if not template:
                template = PromptTemplate(
                    name=self.template_name,
                    template_text=self.template_info["template"],
                    version_tag=self.template_info["version"]
                )
                session.add(template)
                session.commit()
                logger.info(f"Registered new prompt template: {self.template_name} v{template.version_tag}")
            return template.id
        finally:
            session.close()

    def _get_processed_ids(self) -> set:
        """Gets paper IDs that already have embeddings for this prompt."""
        session = self.Session()
        try:
            results = session.query(PaperEmbedding.paper_id).filter_by(
                prompt_template_id=self.prompt_template_id
            ).all()
            return {r[0] for r in results}
        finally:
            session.close()

    async def producer(self, limit: Optional[int] = None):
        """Async loop to send API requests."""
        processed_ids = self._get_processed_ids()
        logger.info(f"Resuming: Found {len(processed_ids)} already processed papers.")
        
        if not os.path.exists(self.jsonl_path):
            logger.error(f"Input file {self.jsonl_path} not found.")
            self.stop_event.set()
            return

        active_tasks = set()
        with open(self.jsonl_path, 'r') as f:
            count = 0
            for line in f:
                if self.stop_event.is_set():
                    break
                
                if limit and count >= limit:
                    break
                    
                data = json.loads(line)
                arxiv_id = data['metadata']['key']
                
                paper_id = self._lookup_paper_id(arxiv_id)
                if not paper_id or paper_id in processed_ids:
                    continue
                
                # Sliding window logic: Wait for at least one slot to open up
                # We use a window size of 2x the QPS to ensure the semaphore is always saturated
                # even if some requests finish extremely fast.
                while len(active_tasks) >= (self.qps * 2):
                    done, active_tasks = await asyncio.wait(
                        active_tasks, return_when=asyncio.FIRST_COMPLETED
                    )
                
                new_task = asyncio.create_task(
                    self.embed_item(paper_id, arxiv_id, data['request']['content']['parts'][0]['text'])
                )
                active_tasks.add(new_task)
                count += 1
                
            if active_tasks:
                await asyncio.gather(*active_tasks)
        
        logger.info("Producer completed reading input file.")
        # Send poison pill
        self.result_queue.put(None)

    def _lookup_paper_id(self, arxiv_id: str) -> Optional[int]:
        """Looks up internal paper ID from arxiv_id."""
        if not hasattr(self, '_id_cache'):
            session = self.Session()
            try:
                # Pre-cache ALL IDs to avoid 60k queries
                logger.info("Building ID cache...")
                results = session.query(Paper.id, Paper.arxiv_id).all()
                self._id_cache = {r.arxiv_id: r.id for r in results}
                logger.info(f"Cache built with {len(self._id_cache)} entries.")
            finally:
                session.close()
        return self._id_cache.get(arxiv_id)

    async def embed_item(self, paper_id: int, arxiv_id: str, text: str):
        """Performs a single embedding request with rate limiting."""
        async with self.semaphore:
            # Precise rate limiting interval
            now = time.time()
            elapsed = now - self.last_request_time
            if elapsed < self.rate_limit_interval:
                await asyncio.sleep(self.rate_limit_interval - elapsed)
            
            self.last_request_time = time.time()
            
            retries = 3
            for attempt in range(retries):
                try:
                    # In google-generativeai, embed_content is the call
                    # We use the sync version in a thread if the library doesn't have a true async client,
                    # but current genai has embed_content_async.
                    response = await genai.embed_content_async(
                        model=self.model_name,
                        content=text,
                        task_type="retrieval_document",
                        output_dimensionality=3072
                    )
                    
                    embedding = response['embedding']
                    
                    # Prepare data for consumer
                    self.result_queue.put({
                        'paper_id': paper_id,
                        'embedding': embedding,
                        'input_tokens': len(text) // 4 # Rough estimate if not returned
                    })
                    self.total_success += 1
                    break
                except Exception as e:
                    if "429" in str(e) or "ResourceExhausted" in str(e):
                        wait = (attempt + 1) * 2
                        logger.warning(f"Rate limit hit for {arxiv_id}, retrying in {wait}s...")
                        await asyncio.sleep(wait)
                    else:
                        logger.error(f"Error embedding {arxiv_id}: {e}")
                        self.total_failed += 1
                        break
            
            self.total_processed += 1
            if self.total_processed % 100 == 0:
                elapsed_total = time.time() - self.start_time
                avg_qps = self.total_processed / elapsed_total
                logger.info(f"Progress: {self.total_processed} processed. Success: {self.total_success}, Fail: {self.total_failed}. Avg QPS: {avg_qps:.2f}")

    def consumer(self):
        """Background thread to handle DB writes."""
        logger.info("Consumer thread started.")
        buffer = []
        
        while True:
            try:
                item = self.result_queue.get(timeout=1.0)
                if item is None: # Poison pill
                    if buffer:
                        self._flush_buffer(buffer)
                    break
                
                buffer.append(item)
                if len(buffer) >= BATCH_SIZE:
                    self._flush_buffer(buffer)
                    buffer = []
                    
            except queue.Empty:
                if self.stop_event.is_set():
                    if buffer:
                        self._flush_buffer(buffer)
                    break
                continue
            except Exception as e:
                logger.error(f"Consumer error: {e}")
                self.stop_event.set()
                break
                
        logger.info("Consumer thread exiting.")

    def _flush_buffer(self, buffer: List[Dict]):
        """Writes a batch of embeddings to the DB."""
        session = self.Session()
        try:
            for item in buffer:
                # Create Protobuf objects for correct serialization
                config = embeddings_pb2.EmbeddingConfig()
                config.purpose = embeddings_pb2.EmbeddingConfig.RETRIEVAL
                config.dimensions = 3072
                config.is_normalized = True
                config.model_name = self.model_name
                
                meta = embeddings_pb2.EmbeddingMetadata()
                meta.source_model = self.model_name
                meta.provider = "google"
                meta.total_tokens = item['input_tokens']
                meta.prompt_template_version = self.template_info["version"]
                meta.schema_version = "1.0.0"
                
                emb = PaperEmbedding(
                    paper_id=item['paper_id'],
                    prompt_template_id=self.prompt_template_id,
                    embedding=item['embedding'],
                    embedding_config=MessageToDict(config),
                    embedding_metadata=MessageToDict(meta)
                )
                session.add(emb)
            
            session.commit()
            logger.debug(f"Committed {len(buffer)} embeddings.")
        except Exception as e:
            session.rollback()
            logger.error(f"Database flush error: {e}")
            raise e
        finally:
            session.close()

    def run(self, limit: Optional[int] = None):
        """Starts the process."""
        # Start consumer thread
        t = threading.Thread(target=self.consumer, name="DBWriter")
        t.start()
        
        # Start producer loop
        try:
            asyncio.run(self.producer(limit=limit))
        except KeyboardInterrupt:
            logger.info("Received interrupt, shutting down gracefully...")
            self.stop_event.set()
        finally:
            # Ensure consumer thread finishes
            t.join()
            logger.info("Ingestion process complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Live Gemini Embedding Ingestor")
    parser.add_argument("--jsonl", default="master_batch_embeddings.jsonl", help="Path to input JSONL")
    parser.add_argument("--db", help="Database URL (default from env)")
    parser.add_argument("--key", help="Gemini API Key (default from env)")
    parser.add_argument("--qps", type=int, default=160, help="Max requests per second")
    parser.add_argument("--model", default=MODEL_NAME, help="Model name")
    parser.add_argument("--limit", type=int, help="Limit number of papers to embed")
    
    args = parser.parse_args()
    
    db_url = args.db or os.environ.get("DATABASE_URL")
    api_key = args.key or os.environ.get("GEMINI_API_KEY")
    
    if not db_url or not api_key:
        print("Error: DATABASE_URL and GEMINI_API_KEY must be provided via args or environment.")
        exit(1)
        
    ingestor = LiveEmbedIngestor(
        jsonl_path=args.jsonl,
        db_url=db_url,
        api_key=api_key,
        qps=args.qps,
        model=args.model
    )
    ingestor.run(limit=args.limit)
