
import glob
import os
import json
import logging
import re
import time
from typing import List, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import concurrent.futures
import signal
import requests
from pypdf import PdfReader
from google import genai
from config import settings
from models import Paper, Base, PromptTemplate, PaperEmbedding
from services.prompts import PROMPT_REGISTRY, get_retrieval_prompt, get_clustering_prompt
from protos import embeddings_pb2
from google.protobuf.json_format import MessageToDict
import hashlib
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database Setup
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class BatchEmbedManager:
    def __init__(self):
        logger.info(f"Using DATABASE_URL: {settings.DATABASE_URL}")
        logger.info(f"Using PDF_SAVE_DIR: {settings.PDF_SAVE_DIR}")
        self.client = genai.Client(api_key=settings.FINAL_GOOGLE_API_KEY)
        self.pdf_dir = settings.PDF_SAVE_DIR
        self.batch_size = 200000 
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
        })
        self.embedding_model = "models/gemini-embedding-2-preview" 
        self.prompt_name = "gemini_retrieval_v1"

    def find_next_batch_index(self):
        """Finds the next batch number by checking both host and container contexts."""
        files = glob.glob("batch_input_*.jsonl")
        if not files:
            return 1
        indices = [int(re.search(r'(\d+)', f).group(1)) for f in files if re.search(r'(\d+)', f)]
        return max(indices) + 1 if indices else 1

    def extract_content(self, paper: Paper) -> Optional[str]:
        """Hierarchical extraction with 30s timeout."""
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self._do_extract_content, paper)
            try:
                return future.result(timeout=30)
            except concurrent.futures.TimeoutError:
                logger.warning(f"Timeout extracting content from {paper.arxiv_id}. Skipping.")
                return None
            except Exception as e:
                logger.error(f"Error in extraction thread for {paper.arxiv_id}: {e}")
                return None

    def _do_extract_content(self, paper: Paper) -> Optional[str]:
        """Logic moved here for timeout wrapping."""
        # Robust filename check
        arxiv_id = paper.arxiv_id
        pdf_path = os.path.join(self.pdf_dir, f"{arxiv_id}.pdf")
        
        if not os.path.exists(pdf_path):
            # Try version stripped
            base_id = arxiv_id.split('v')[0]
            pdf_path = os.path.join(self.pdf_dir, f"{base_id}.pdf")
            
        if not os.path.exists(pdf_path):
            logger.warning(f"PDF missing for {paper.arxiv_id}. Skipping content enrichment.")
            return None

        # Helper to clean text
        def clean(t):
            if not t: return ""
            # Remove null bytes and other common issues
            t = t.replace("\x00", "")
            # Force encode to utf-8 and ignore errors (like surrogates)
            return t.encode('utf-8', 'ignore').decode('utf-8').strip()

        # Check for reCAPTCHA/HTML (usually < 5KB and contains <html> tag)
        try:
            if os.path.getsize(pdf_path) < 10000:
                with open(pdf_path, 'r', errors='ignore') as f:
                    preview = f.read(1000)
                    if "<html" in preview.lower() or "recaptcha" in preview.lower():
                        logger.warning(f"Corrupted/reCAPTCHA PDF for {paper.arxiv_id}. Marking for deletion.")
                        return "CORRUPTED"
        except:
            pass

        try:
            reader = PdfReader(pdf_path)
            full_text = ""
            # Process up to 10 pages for search
            for page in reader.pages[:10]:
                try:
                    full_text += page.extract_text() + "\n"
                except:
                    continue
            
            full_text = clean(full_text)
            if not full_text.strip():
                return "CORRUPTED"

            # 1. Abstract Search
            abstract_match = re.search(r'(?i)abstract\s*[:\-\.]?\s*(.*?)(\n\s*[A-Z]|\n\s*1\s+Introduction|\n\s*Introduction)', full_text, re.DOTALL)
            if abstract_match:
                extracted = clean(abstract_match.group(1))
                if len(extracted) > 100:
                    paper.extracted_abstract = extracted
                    return f"{paper.title} {extracted}"

            # Fallback to arxiv summary if PDF search fails
            if paper.summary:
                paper.extracted_abstract = paper.summary
            
            # 2. Introduction Search
            intro_match = re.search(r'(?i)(?:1\s+)?introduction\s*[:\-\.]?\s*(.*?)(\n\s*[A-Z]|\n\s*2\s+)', full_text, re.DOTALL)
            if intro_match:
                extracted = clean(intro_match.group(1))
                if len(extracted) > 100:
                    paper.extracted_introduction = extracted
                    return f"{paper.title} {extracted}"

            # 3. First 150 words fallback
            words = full_text.split()[:150]
            fallback_text = " ".join(words)
            paper.extracted_introduction = fallback_text
            return f"{paper.title} {fallback_text}"

        except Exception as e:
            if "invalid pdf header" in str(e).lower():
                return "CORRUPTED"
            logger.error(f"Error parsing PDF {paper.arxiv_id}: {e}")
            return "CORRUPTED"

    def _get_or_create_prompt(self, db):
        prompt_info = PROMPT_REGISTRY[self.prompt_name]
        template_text = prompt_info["template"]
        version_tag = prompt_info["version"]
        
        prompt = db.query(PromptTemplate).filter_by(name=self.prompt_name, version_tag=version_tag).first()
        if not prompt:
            prompt = PromptTemplate(
                name=self.prompt_name,
                template_text=template_text,
                version_tag=version_tag
            )
            db.add(prompt)
            db.commit()
            db.refresh(prompt)
            logger.info(f"Registered new prompt template: {self.prompt_name} v{version_tag}")
        return prompt

    def download_pdf(self, arxiv_id: str) -> bool:
        """Downloads PDF from Arxiv if not present."""
        pdf_path = os.path.join(self.pdf_dir, f"{arxiv_id}.pdf")
        if os.path.exists(pdf_path):
            return True
            
        url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        logger.info(f"Downloading PDF from {url}...")
        try:
            # Small random delay to be polite
            time.sleep(random.uniform(1.0, 3.0))
            
            response = self.session.get(url, timeout=30)
            if response.status_code == 200:
                with open(pdf_path, "wb") as f:
                    f.write(response.content)
                logger.info(f"Downloaded {arxiv_id}.pdf")
                return True
            else:
                logger.error(f"Failed to download {arxiv_id}.pdf: {response.status_code}")
                # If we get 403, sleep longer
                if response.status_code == 403:
                    logger.warning("Rate limited (403). Sleeping for 30s...")
                    time.sleep(30)
                return False
        except Exception as e:
            logger.error(f"Error downloading {arxiv_id}: {e}")
            return False

    def prepare_master_batch(self):
        """Generates a single master_batch_embeddings.jsonl for ALL papers (~65k)."""
        db = SessionLocal()
        try:
            # Get ALL papers
            all_ids = [row[0] for row in db.execute(text("SELECT id FROM papers")).fetchall()]
            total = len(all_ids)
            logger.info(f"Preparing master batch for {total} papers.")

            prompt = self._get_or_create_prompt(db)
            prompt_id = prompt.id

            filename = "master_batch_embeddings.jsonl"
            
            # Check for existing progress to resume
            processed_ids = set()
            if os.path.exists(filename):
                try:
                    with open(filename, "r") as f:
                        for line in f:
                            try:
                                data = json.loads(line)
                                aid = data["metadata"]["key"]
                                processed_ids.add(aid)
                            except: continue
                    logger.info(f"Resuming master batch. Already processed {len(processed_ids)} papers.")
                except Exception as e:
                    logger.warning(f"Error reading existing {filename}: {e}")

            f_out = open(filename, "a", encoding="utf-8")
            
            processed_count = 0
            
            # Use chunks of 100 for better feedback and memory management
            batch_size = 100
            for i in range(0, total, batch_size):
                chunk_ids = all_ids[i:i+batch_size]
                
                # Retry logic for the chunk processing
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        # Refresh session if this is a retry
                        if attempt > 0:
                            db.close()
                            db = SessionLocal()
                            logger.info(f"Refreshed DB session for retry {attempt+1}")
                            
                        papers = db.query(Paper).filter(Paper.id.in_(chunk_ids)).all()
                        for paper in papers:
                            if paper.arxiv_id in processed_ids:
                                processed_count += 1
                                continue

                            # Logic to get content
                            content = paper.extracted_abstract or paper.extracted_introduction
                            
                            if not content:
                                # Try to download and extract
                                if self.download_pdf(paper.arxiv_id):
                                    content = self.extract_content(paper)
                                    # Update paper in DB so we don't do this again
                                    db.flush()
                            
                            # Last fallback
                            if not content:
                                content = paper.summary
                                
                            if content and content != "CORRUPTED":
                                formatted_content = get_retrieval_prompt(paper.title, content)
                                entry = {
                                    "request": {
                                        "task_type": "RETRIEVAL_DOCUMENT",
                                        "content": {"parts": [{"text": formatted_content}]},
                                        "title": paper.title,
                                        "output_dimensionality": 768
                                    },
                                    "metadata": {
                                        "key": paper.arxiv_id,
                                        "prompt_template_id": prompt_id
                                    }
                                }
                                f_out.write(json.dumps(entry) + "\n")
                            
                            processed_count += 1
                        
                        db.commit()
                        f_out.flush()
                        break # Success for this chunk
                        
                    except Exception as e:
                        db.rollback()
                        logger.error(f"Error in chunk {i}-{i+batch_size} (Attempt {attempt+1}/{max_retries}): {e}")
                        if attempt < max_retries - 1:
                            time.sleep(5)
                        else:
                            raise e
                
                if (i // batch_size + 1) % 10 == 0:
                    logger.info(f"Progress: {processed_count}/{total} papers processed.")
            
            f_out.close()
            logger.info(f"Master batch generation complete: {filename}")
        finally:
            if 'f_out' in locals() and not f_out.closed:
                f_out.close()
            db.commit()
            db.close()

    def prepare_batches(self):
        db = SessionLocal()
        try:
            # Get all papers as requested
            all_ids = [row[0] for row in db.execute(text("SELECT id FROM papers")).fetchall()]
            total = len(all_ids)
            logger.info(f"Found {total} papers to process for embeddings.")

            prompt = self._get_or_create_prompt(db)
            prompt_id = prompt.id

            batch_count = self.find_next_batch_index()
            # If batch_count is 1 and no files exist, valid. If files exist, we might be appending or creating new.
            # But here we are creating fresh batches for the missing ones.
            
            current_batch_size_bytes = 0
            max_batch_size_bytes = 2 * 1024 * 1024 * 1024 # 2GB
            max_requests_per_batch = self.batch_size
            
            current_request_count = 0
            
            # Open the first file
            filename = f"batch_input_{batch_count}.jsonl"
            f_out = open(filename, "w", encoding="utf-8")
            logger.info(f"Started writing to {filename}...")

            # Process in chunks of 500 to keep memory low
            chunk_size = 500
            for start_idx in range(0, total, chunk_size):
                chunk_ids = all_ids[start_idx : start_idx + chunk_size]
                papers = db.query(Paper).filter(Paper.id.in_(chunk_ids)).order_by(Paper.id).all()
                
                for i, paper in enumerate(papers):
                    overall_idx = start_idx + i
                    # Optimization: check if already extracted
                    content = None
                    if paper.extracted_abstract:
                        abstract_or_intro = paper.extracted_abstract
                    elif paper.extracted_introduction:
                        abstract_or_intro = paper.extracted_introduction
                    else:
                        # Performs extraction
                        content_raw = self.extract_content(paper)
                        db.flush() 
                        abstract_or_intro = paper.extracted_abstract or paper.extracted_introduction or paper.summary

                    if abstract_or_intro == "CORRUPTED":
                        paper.is_downloaded = False
                        pdf_path = os.path.join(self.pdf_dir, f"{paper.arxiv_id}.pdf")
                        if os.path.exists(pdf_path):
                            try: os.remove(pdf_path)
                            except: pass
                        logger.info(f"Skipping and cleaned up corrupted paper {paper.arxiv_id}")
                    elif abstract_or_intro:
                        # Format content using services.prompts
                        formatted_content = get_retrieval_prompt(paper.title, abstract_or_intro)
                        
                        # Formulate request for JSONL
                        request = {
                            "task_type": "RETRIEVAL_DOCUMENT",
                            "content": {"parts": [{"text": formatted_content}]},
                            "title": paper.title,
                            "output_dimensionality": 768
                        }
                        entry = {
                            "request": request,
                            "metadata": {
                                "key": paper.arxiv_id,
                                "prompt_template_id": prompt_id
                            }
                        }
                        entry_json = json.dumps(entry) + "\n"
                        
                        # Write immediately
                        f_out.write(entry_json)
                        current_request_count += 1
                        current_batch_size_bytes += len(entry_json.encode('utf-8'))

                        # Check limits and rotate file if needed
                        if current_request_count >= max_requests_per_batch or current_batch_size_bytes >= max_batch_size_bytes:
                            logger.info(f"Finished {filename} with {current_request_count} requests.")
                            f_out.close()
                            
                            batch_count += 1
                            filename = f"batch_input_{batch_count}.jsonl"
                            f_out = open(filename, "w", encoding="utf-8")
                            logger.info(f"Started writing to {filename}...")
                            
                            current_request_count = 0
                            current_batch_size_bytes = 0

                    if (overall_idx + 1) % 100 == 0:
                        logger.info(f"Processed {overall_idx + 1}/{total} papers... Current batch: {current_request_count} items")
                        db.commit() # Periodic commit
                        f_out.flush() # Periodic flush

                # Clear session to free memory after each chunk
                db.expunge_all()

            # Final cleanup
            if not f_out.closed:
                logger.info(f"Finished {filename} with {current_request_count} requests.")
                f_out.close()
            
        finally:
            if 'f_out' in locals() and not f_out.closed:
                f_out.close()
            db.commit()
            db.close()

    def prepare_category_batch(self, category: str):
        """Generates 3 JSONL files for a category: search, abstract clustering, intro clustering."""
        db = SessionLocal()
        try:
            FAILED_VALUES = ("[FAILED]", "[DOWNLOAD FAILED]")

            # --- File 1: Search embeddings (all papers in category) ---
            search_papers = db.query(Paper).filter(Paper.category == category).all()
            search_file = f"batch_search_{category.replace('.', '_')}.jsonl"
            search_count = 0
            with open(search_file, "w", encoding="utf-8") as f:
                for paper in search_papers:
                    content = None
                    for candidate in (paper.extracted_abstract, paper.extracted_introduction, paper.summary):
                        if candidate and candidate not in FAILED_VALUES:
                            content = candidate
                            break
                    if not content:
                        continue
                    formatted = get_retrieval_prompt(paper.title or "", content)
                    entry = {
                        "key": f"search_{paper.arxiv_id}",
                        "request": {
                            "task_type": "RETRIEVAL_DOCUMENT",
                            "title": paper.title,
                            "output_dimensionality": 768,
                            "content": {"parts": [{"text": formatted}]}
                        }
                    }
                    f.write(json.dumps(entry) + "\n")
                    search_count += 1
            logger.info(f"[{category}] Search JSONL: {search_count} entries -> {search_file}")

            # --- File 2: Abstract clustering embeddings ---
            abstract_papers = (
                db.query(Paper)
                .filter(
                    Paper.category == category,
                    Paper.extracted_abstract.isnot(None),
                    Paper.extracted_abstract.notin_(FAILED_VALUES),
                )
                .all()
            )
            abstract_file = f"batch_abstract_{category.replace('.', '_')}.jsonl"
            abstract_count = 0
            with open(abstract_file, "w", encoding="utf-8") as f:
                for paper in abstract_papers:
                    formatted = get_clustering_prompt(paper.extracted_abstract)
                    entry = {
                        "key": f"abstract_{paper.arxiv_id}",
                        "request": {
                            "task_type": "CLUSTERING",
                            "output_dimensionality": 768,
                            "content": {"parts": [{"text": formatted}]}
                        }
                    }
                    f.write(json.dumps(entry) + "\n")
                    abstract_count += 1
            logger.info(f"[{category}] Abstract clustering JSONL: {abstract_count} entries -> {abstract_file}")

            # --- File 3: Introduction clustering embeddings ---
            intro_papers = (
                db.query(Paper)
                .filter(
                    Paper.category == category,
                    Paper.extracted_introduction.isnot(None),
                    Paper.extracted_introduction.notin_(FAILED_VALUES),
                )
                .all()
            )
            intro_file = f"batch_intro_{category.replace('.', '_')}.jsonl"
            intro_count = 0
            with open(intro_file, "w", encoding="utf-8") as f:
                for paper in intro_papers:
                    formatted = get_clustering_prompt(paper.extracted_introduction)
                    entry = {
                        "key": f"intro_{paper.arxiv_id}",
                        "request": {
                            "task_type": "CLUSTERING",
                            "output_dimensionality": 768,
                            "content": {"parts": [{"text": formatted}]}
                        }
                    }
                    f.write(json.dumps(entry) + "\n")
                    intro_count += 1
            logger.info(f"[{category}] Intro clustering JSONL: {intro_count} entries -> {intro_file}")

            total = search_count + abstract_count + intro_count
            logger.info(f"[{category}] Total: {total} embedding requests across 3 files.")
        finally:
            db.close()

    def submit_category_batches(self, category: str):
        """Submits all 3 JSONL files for a category."""
        cat_slug = category.replace(".", "_")
        for prefix in ("batch_search_", "batch_abstract_", "batch_intro_"):
            filename = f"{prefix}{cat_slug}.jsonl"
            if os.path.exists(filename):
                logger.info(f"Submitting {filename}...")
                self.submit_batch(filename)
                time.sleep(10)  # Brief pause between submissions
            else:
                logger.warning(f"File {filename} not found, skipping.")

    def ingest_category_results(self, filename: str):
        """Ingests results from a category batch, routing by key prefix."""
        if not os.path.exists(filename):
            logger.error(f"File {filename} not found.")
            return

        db = SessionLocal()
        search_count = 0
        abstract_count = 0
        intro_count = 0
        error_count = 0

        try:
            with open(filename, "r") as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        if "response" not in data:
                            continue

                        key = data.get("key", "")
                        response = data["response"]

                        # Extract embedding from response
                        embedding = None
                        if isinstance(response, list) and len(response) > 0:
                            embedding = response[0].get("embedding")
                        elif isinstance(response, dict):
                            embedding = response.get("embedding")

                        if isinstance(embedding, dict) and "values" in embedding:
                            embedding = embedding["values"]

                        if not embedding or not isinstance(embedding, list):
                            logger.warning(f"No valid embedding for key={key}")
                            error_count += 1
                            continue

                        # Parse arxiv_id from key
                        # key format: "search_{arxiv_id}", "abstract_{arxiv_id}", "intro_{arxiv_id}"
                        parts = key.split("_", 1)
                        if len(parts) != 2:
                            logger.warning(f"Invalid key format: {key}")
                            error_count += 1
                            continue

                        prefix, arxiv_id = parts[0], parts[1]

                        if prefix == "search":
                            # Delete existing, insert new into paper_embeddings
                            paper_id = db.execute(
                                text("SELECT id FROM papers WHERE arxiv_id = :aid"),
                                {"aid": arxiv_id}
                            ).scalar()
                            if paper_id:
                                db.execute(
                                    text("DELETE FROM paper_embeddings WHERE paper_id = :pid"),
                                    {"pid": paper_id}
                                )
                                new_emb = PaperEmbedding(
                                    paper_id=paper_id,
                                    embedding=embedding,
                                    embedding_config={"purpose": "search", "dimensions": 768},
                                    embedding_metadata={
                                        "source_model": self.embedding_model,
                                        "provider": "google",
                                        "format": "title_document",
                                        "batch_generated": True,
                                    }
                                )
                                db.add(new_emb)
                                search_count += 1

                        elif prefix == "abstract":
                            db.execute(
                                text("UPDATE papers SET abstract_embedding = :emb WHERE arxiv_id = :aid"),
                                {"emb": str(embedding), "aid": arxiv_id}
                            )
                            abstract_count += 1

                        elif prefix == "intro":
                            db.execute(
                                text("UPDATE papers SET introduction_embedding = :emb WHERE arxiv_id = :aid"),
                                {"emb": str(embedding), "aid": arxiv_id}
                            )
                            intro_count += 1

                        total = search_count + abstract_count + intro_count
                        if total % 100 == 0 and total > 0:
                            db.commit()
                            logger.info(f"Ingested {total} embeddings (search={search_count}, abstract={abstract_count}, intro={intro_count})...")

                    except Exception as e:
                        logger.error(f"Error processing line: {e}")
                        db.rollback()
                        error_count += 1

            db.commit()
            total = search_count + abstract_count + intro_count
            logger.info(
                f"Ingestion complete: {total} embeddings "
                f"(search={search_count}, abstract={abstract_count}, intro={intro_count}, errors={error_count})"
            )
        finally:
            db.close()

    def submit_batch(self, filename: str):
        """Uploads JSONL and submits a batch embedding job."""
        if not os.path.exists(filename):
            logger.error(f"File {filename} not found.")
            return

        try:
            logger.info(f"Uploading {filename}...")
            # Upload with retry logic
            max_retries = 3
            uploaded_file = None
            for attempt in range(max_retries):
                try:
                    uploaded_file = self.client.files.upload(
                        file=filename,
                        config={'mime_type': 'application/x-jsonlines'}
                    )
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 60
                        logger.warning(f"Upload failed: {e}. Retrying in {wait_time}s... (Attempt {attempt+1}/{max_retries})")
                        time.sleep(wait_time)
                    else:
                        raise e

            if not uploaded_file:
                raise Exception("Failed to upload file after retries.")
            
            logger.info(f"Uploaded file name: {uploaded_file.name}")

            logger.info(f"Creating batch job for {filename}...")
            
            # Submission with retry logic for 429s/Resource Exhaustion
            max_retries = 3
            batch_job = None
            for attempt in range(max_retries):
                try:
                    batch_job = self.client.batches.create_embeddings(
                        model=self.embedding_model,
                        src={'file_name': uploaded_file.name},
                        config={'display_name': f"Arxiv-Backfill-{filename}"},
                    )
                    break 
                except Exception as e:
                    if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                        if attempt < max_retries - 1:
                            wait_time = (attempt + 1) * 300 # 5 min, 10 min...
                            logger.warning(f"Quota exceeded (429). Retrying in {wait_time}s... (Attempt {attempt+1}/{max_retries})")
                            time.sleep(wait_time)
                        else:
                            raise e
                    else:
                        raise e

            if not batch_job:
                raise Exception("Failed to create batch job after retries.")

            logger.info(f"Created batch job: {batch_job.name}")

            # Track job
            jobs = self._load_jobs()
            jobs[batch_job.name] = {
                "filename": filename,
                "file_name": uploaded_file.name,
                "status": "ACTIVE",
                "created_at": str(batch_job.create_time)
            }
            self._save_jobs(jobs)
            return batch_job.name

        except Exception as e:
            logger.error(f"Error submitting batch {filename}: {e}")
            return None

    def _load_jobs(self):
        if os.path.exists("batch_embedding_jobs.json"):
            with open("batch_embedding_jobs.json", "r") as f:
                return json.load(f)
        return {}

    def _save_jobs(self, jobs):
        with open("batch_embedding_jobs.json", "w") as f:
            json.dump(jobs, f, indent=4)

    def monitor_and_ingest(self, force_reingest: bool = False):
        """Checks status of jobs and ingests results if completed."""
        jobs = self._load_jobs()
        db = SessionLocal()
        try:
            for job_name, info in list(jobs.items()):
                if info["status"] != "ACTIVE" and not force_reingest:
                    continue

                try:
                    job = self.client.batches.get(name=job_name)
                    state = str(job.state) # Handle Enum or String
                    logger.info(f"Job {job_name} state: {state}")

                    if any(s in state for s in ["SUCCEEDED", "COMPLETED"]):
                        if info["status"] == "COMPLETED" and not force_reingest:
                            continue
                            
                        logger.info(f"Job {job_name} SUCCEEDED. Ingesting results...")
                        self._ingest_results(job, db)
                        info["status"] = "COMPLETED"
                        info["completed_at"] = str(job.update_time)
                    elif any(s in state for s in ["FAILED"]):
                        logger.error(f"Job {job_name} FAILED: {job.error}")
                        info["status"] = "FAILED"
                        info["error"] = str(job.error)
                except Exception as e:
                    logger.error(f"Error checking job {job_name}: {e}")

            self._save_jobs(jobs)
        finally:
            db.close()

    def cancel_all_active_jobs(self):
        """Cancels all jobs currently marked as ACTIVE in the tracker."""
        jobs = self._load_jobs()
        cancelled_count = 0
        for job_name, info in list(jobs.items()):
            if info["status"] == "ACTIVE":
                try:
                    logger.info(f"Cancelling job: {job_name} ({info.get('filename')})...")
                    # Note: Using .delete() as it often acts as cancel in early Batch SDKs 
                    # or specifically as the method available in this iteration.
                    try:
                        self.client.batches.delete(name=job_name)
                    except AttributeError:
                        self.client.batches.cancel(name=job_name)
                    info["status"] = "CANCELLED"
                    cancelled_count += 1
                except Exception as e:
                    logger.error(f"Failed to cancel job {job_name}: {e}")
        
        self._save_jobs(jobs)
        logger.info(f"Successfully cancelled {cancelled_count} active jobs.")

    def _ingest_results(self, job, db):
        """Downloads the output file and updates the database."""
        # Use job.dest.file_name for the new SDK
        if not job.dest or not job.dest.file_name:
            logger.error(f"No result file found in job {job.name}")
            return

        output_file_name = job.dest.file_name
        logger.info(f"Downloading results from {output_file_name}...")
        
        local_output = f"results_{job.name.split('/')[-1]}.jsonl"
        try:
            # download() returns bytes, we must write them to disk
            logger.info(f"Downloading {output_file_name} to {local_output}...")
            content_bytes = self.client.files.download(file=output_file_name)
            with open(local_output, "wb") as f:
                f.write(content_bytes)
        except Exception as e:
            logger.error(f"Error downloading {output_file_name}: {e}")
            return

        processed_count = 0
        with open(local_output, "r") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    # response content contains embedding
                    # metadata key is the arxiv_id
                    if "metadata" not in data or "response" not in data:
                        logger.warning(f"Unexpected data format in JSONL: {data.keys()}")
                        continue
                        
                    arxiv_id = data["metadata"]["key"]
                    prompt_template_id = data["metadata"].get("prompt_template_id")
                    response = data["response"]
                    
                    # Embedding logic
                    embedding = None
                    if isinstance(response, list) and len(response) > 0:
                        embedding = response[0].get("embedding")
                    elif isinstance(response, dict):
                        embedding = response.get("embedding")
                    
                    if isinstance(embedding, dict) and "values" in embedding:
                        embedding = embedding["values"]
                    
                    if not embedding or not isinstance(embedding, list):
                        logger.warning(f"No valid embedding list found for {arxiv_id}")
                        continue
                    
                    # Construct structured config and metadata using Protobuf
                    config = embeddings_pb2.EmbeddingConfig(
                        purpose=embeddings_pb2.EmbeddingConfig.RETRIEVAL,
                        dimensions=768,
                        is_normalized=True
                    )
                    
                    meta = embeddings_pb2.EmbeddingMetadata(
                        source_model=self.embedding_model,
                        provider="google",
                        prompt_template_version=PROMPT_REGISTRY[self.prompt_name]["version"],
                        input_tokens_count=0, # Default or extract if available
                        schema_version="1.0.0"
                    )
                    
                    # Store in paper_embeddings table
                    paper_id = db.execute(text("SELECT id FROM papers WHERE arxiv_id = :aid"), {"aid": arxiv_id}).scalar()
                    if paper_id:
                        new_emb = PaperEmbedding(
                            paper_id=paper_id,
                            prompt_template_id=prompt_template_id,
                            embedding=embedding,
                            embedding_config=MessageToDict(config),
                            embedding_metadata=MessageToDict(meta)
                        )
                        db.add(new_emb)
                        processed_count += 1
                    
                    if processed_count % 100 == 0 and processed_count > 0:
                        db.commit()
                        logger.info(f"Ingested {processed_count} embeddings...")
                except Exception as e:
                    logger.error(f"Error processing line in {local_output}: {e}")
                    db.rollback()
            
        db.commit()
        logger.info(f"Successfully ingested {processed_count} embeddings for job {job.name}")

    def ingest_local_file(self, filename):
        """Ingests a local results file directly without API calls."""
        if not os.path.exists(filename):
            logger.error(f"File {filename} not found.")
            return

        logger.info(f"Ingesting results from local file {filename}...")
        db = SessionLocal()
        processed_count = 0
        try:
            with open(filename, "r") as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        if "metadata" not in data or "response" not in data:
                            logger.warning(f"Skipping invalid line: keys missing")
                            continue
                            
                        arxiv_id = data["metadata"]["key"]
                        response = data["response"]
                        
                        embedding = None
                        if isinstance(response, list) and len(response) > 0:
                            embedding = response[0].get("embedding")
                        elif isinstance(response, dict):
                            embedding = response.get("embedding")
                        
                        if isinstance(embedding, dict) and "values" in embedding:
                            embedding = embedding["values"]
                        
                        if not embedding or not isinstance(embedding, list):
                            logger.warning(f"No valid embedding list found for {arxiv_id}")
                            continue

                        stmt = text("UPDATE papers SET embedding = :emb WHERE arxiv_id = :aid")
                        try:
                            # We need to explicitly cast or just pass as list (psycopg2 handles it)
                            db.execute(stmt, {"emb": embedding, "aid": arxiv_id})
                            processed_count += 1
                        except Exception as e:
                             logger.error(f"Error updating {arxiv_id}: {e}")
                             db.rollback()

                        if processed_count % 100 == 0 and processed_count > 0:
                            db.commit()
                            logger.info(f"Ingested {processed_count} embeddings...")
                    except Exception as e:
                        logger.error(f"Error processing line: {e}")
            
            db.commit()
            logger.info(f"Successfully ingested {processed_count} embeddings from {filename}")
        finally:
            db.close()

    def ingest_all_local(self):
        """Finds all results_*.jsonl files and ingests them."""
        files = glob.glob("results_*.jsonl")
        files.sort()
        logger.info(f"Found {len(files)} result files for ingestion: {files}")
        for f in files:
            self.ingest_local_file(f)

    def submit_all_batches(self):
        """Finds all batch files (input, search, abstract, intro) and submits them if not already tracked."""
        files = (
            glob.glob("batch_input_*.jsonl")
            + glob.glob("batch_search_*.jsonl")
            + glob.glob("batch_abstract_*.jsonl")
            + glob.glob("batch_intro_*.jsonl")
        )
        files.sort()
        
        jobs = self._load_jobs()
        tracked_files = [info["filename"] for info in jobs.values()]
        
        logger.info(f"Found {len(files)} batch files. {len(tracked_files)} files already tracked.")
        
        for f in files:
            if f not in tracked_files:
                logger.info(f"Submitting new batch: {f}")
                success = self.submit_batch(f)
                if not success:
                    logger.warning(f"Failed to submit {f}, stopping submit_all loop.")
                    break
                # Sleep between submissions to avoid overwhelming the API
                time.sleep(30)
            else:
                logger.debug(f"Skipping already tracked file: {f}")

    def cleanup_completed_batches(self):
        """Deletes local jsonl files for completed jobs to save space."""
        jobs = self._load_jobs()
        for job_id, info in jobs.items():
            if info.get("status") == "COMPLETED":
                # Delete input file
                input_file = info.get("filename")
                if input_file and os.path.exists(input_file):
                    logger.info(f"Deleting completed input file: {input_file}")
                    try:
                        os.remove(input_file)
                    except:
                        pass
                
                # Delete results file
                results_file = f"results_{job_id.split('/')[-1]}.jsonl"
                if os.path.exists(results_file):
                    logger.info(f"Deleting results file: {results_file}")
                    try:
                        os.remove(results_file)
                    except:
                        pass


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Gemini Batch Embedding Manager")
    commands = [
        "prepare", "prepare_master", "prepare_category",
        "submit", "submit_all", "submit_category",
        "monitor", "ingest_local", "ingest_all_local", "ingest_category",
        "clean", "cancel_active",
    ]
    parser.add_argument("command", choices=commands, help="Command to run")
    parser.add_argument("--file", help="Filename for submit/ingest commands")
    parser.add_argument("--category", help="arXiv category (e.g., cs.AI) for category commands")
    parser.add_argument("--force", action="store_true", help="Force re-ingest of COMPLETED jobs")
    parser.add_argument("--db-url", help="Override DATABASE_URL")

    args = parser.parse_args()

    if args.db_url:
        import os
        os.environ["DATABASE_URL"] = args.db_url

    manager = BatchEmbedManager()

    if args.command == "prepare":
        manager.prepare_batches()
    elif args.command == "prepare_master":
        manager.prepare_master_batch()
    elif args.command == "prepare_category":
        if not args.category:
            print("Error: --category required (e.g., --category cs.AI)")
        else:
            manager.prepare_category_batch(args.category)
    elif args.command == "submit":
        if not args.file:
            print("Error: --file required for submit command")
        else:
            manager.submit_batch(args.file)
    elif args.command == "submit_all":
        manager.submit_all_batches()
    elif args.command == "submit_category":
        if not args.category:
            print("Error: --category required (e.g., --category cs.AI)")
        else:
            manager.submit_category_batches(args.category)
    elif args.command == "monitor":
        manager.monitor_and_ingest(force_reingest=args.force)
    elif args.command == "ingest_local":
        if not args.file:
            print("Error: --file required for ingest_local command")
        else:
            manager.ingest_local_file(args.file)
    elif args.command == "ingest_all_local":
        manager.ingest_all_local()
    elif args.command == "ingest_category":
        if not args.file:
            print("Error: --file required for ingest_category command")
        else:
            manager.ingest_category_results(args.file)
    elif args.command == "clean":
        manager.cleanup_completed_batches()
    elif args.command == "cancel_active":
        manager.cancel_all_active_jobs()
