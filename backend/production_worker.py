
import sys
import os
import time
import re
import logging
import datetime

# Ensure logs can handle UTF-8 symbols
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        # Fallback for older python versions
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8')
from sqlalchemy import create_engine, or_, and_
from sqlalchemy.orm import sessionmaker
from models import Paper, JobLog, PaperEmbedding, PatternExperimentResult
from taxonomy import PROMPT_VERSION as TAXONOMY_PROMPT_VERSION, validate_classification_output
from core.pdf_utils import (
    get_local_pdf_path as _get_local_pdf_path,
    download_pdf as _download_pdf,
)
from core.text_utils import sanitize_text
from services.citation_service import resolve_citations, backfill_citation_links
from services.pdf_service import (
    extract_text_from_pdf,
    extract_sections,
    extract_citations,
    process_pdf as _process_pdf,
)
from services.llm_service import llm_service, embedding_service
from config import settings

import json

# Setup Logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ProdWorker")
logging.getLogger("pypdf").setLevel(logging.ERROR)

# Configuration
DB_URL = settings.DATABASE_URL
PDF_DIR = settings.PDF_SAVE_DIR

engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class PDFProcessorLite:
    """Backward-compatible shim. Delegates to services/pdf_service.py.

    Kept because 6 test files import PDFProcessorLite from production_worker.
    """

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        return extract_text_from_pdf(pdf_path)

    def extract_sections(self, full_text: str) -> dict:
        return extract_sections(full_text)

    def extract_citations(self, pdf_path: str) -> list:
        return extract_citations(pdf_path)

    def process_pdf(self, pdf_path: str):
        return _process_pdf(pdf_path)

def get_local_pdf_path(arxiv_id: str) -> str:
    """Backward-compatible wrapper. Delegates to core.pdf_utils."""
    return _get_local_pdf_path(arxiv_id, PDF_DIR)

def download_pdf(url: str, arxiv_id: str) -> str:
    """Backward-compatible wrapper. Delegates to core.pdf_utils."""
    return _download_pdf(url, arxiv_id, PDF_DIR)

def log_job(db, job_name, status, details=None, error=None):
    try:
        job = JobLog(
            job_name=job_name,
            status=status,
            start_time=datetime.datetime.utcnow(), 
            end_time=datetime.datetime.utcnow(),
            job_details=details,
            error_message=error
        )
        db.add(job)
        db.commit()
    except Exception as e:
        logger.error(f"Failed to write job log: {e}")

def run_worker():
    logger.info(f"🚀 Starting Production Worker (Lite Mode).")
    logger.info(f"DB: {DB_URL}")
    logger.info(f"PDF_DIR: {PDF_DIR}")
    
    processor = None
    
    while True:
        db = SessionLocal()
        try:
            batch_size = 5
            twenty_days_ago = datetime.datetime.now() - datetime.timedelta(days=20)
            # Find papers that either:
            # 1. Are not downloaded
            # 2. Have missing abstract/intro extraction
            # 3. Have missing 3072d search embedding in the new table
            # EXCLUDE papers that have already failed processing
            
            papers = db.query(Paper).outerjoin(PaperEmbedding).filter(
                or_(
                    Paper.is_downloaded == False,
                    Paper.extracted_abstract.is_(None),
                    Paper.citations.is_(None),
                    PaperEmbedding.id.is_(None)
                ),
                Paper.published_date >= twenty_days_ago.date()
            ).filter(
                or_(
                    Paper.extracted_abstract.is_(None),
                    and_(
                        Paper.extracted_abstract != "[FAILED]",
                        Paper.extracted_abstract != "[DOWNLOAD FAILED]"
                    )
                )
            ).order_by(Paper.published_date.desc()).limit(batch_size).all()
            
            if not papers:
                time.sleep(30) # Wait longer if nothing to do
                continue
            
            if processor is None:
                processor = PDFProcessorLite()

            logger.info(f"Processing batch of {len(papers)} papers...")
            
            for paper in papers:
                try:
                    # --- STEP 1: DOWNLOAD ---
                    pdf_path = get_local_pdf_path(paper.arxiv_id)
                    if not pdf_path or not paper.is_downloaded:
                        if not pdf_path:
                             url = paper.pdf_url or f"https://arxiv.org/pdf/{paper.arxiv_id}.pdf"
                             pdf_path = download_pdf(url, paper.arxiv_id)
                        
                        if pdf_path:
                            paper.is_downloaded = True
                            db.commit()
                            log_job(db, "worker_download", "SUCCESS", {"arxiv_id": paper.arxiv_id})
                        else:
                            # MARK AS FAILED so we don't loop on it
                            paper.is_downloaded = True 
                            paper.extracted_abstract = "[DOWNLOAD FAILED]"
                            paper.extracted_introduction = "[DOWNLOAD FAILED]"
                            db.commit()
                            log_job(db, "worker_download", "FAILED", {"arxiv_id": paper.arxiv_id}, "Download failed / 404")
                            continue

                    # --- STEP 2: EMBED & EXTRACT ---
                    if not paper.extracted_abstract or paper.extracted_abstract == "[FAILED]" or paper.citations is None:
                        logger.info(f"Step 2: Starting PDF processing for {paper.arxiv_id}...")
                        result = processor.process_pdf(pdf_path)
                        if result:
                            logger.info(f"Step 2: Sanitizing data for {paper.arxiv_id}...")
                            paper.extracted_abstract = sanitize_text(result['sections']['abstract']) or None
                            paper.extracted_introduction = sanitize_text(result['sections']['introduction']) or None
                            paper.citations = result['citations']
                            paper.entities = result['entities']
                            
                            if result['embeddings']['abstract']: 
                                paper.abstract_embedding = result['embeddings']['abstract']
                            if result['embeddings']['introduction']: 
                                paper.introduction_embedding = result['embeddings']['introduction']
                                
                            logger.info(f"Step 2: Committing data for {paper.arxiv_id}...")
                            db.commit()
                            
                            # --- STEP 2.1: RESOLVE CITATIONS ---
                            logger.info(f"Step 2.1: Resolving citations for {paper.arxiv_id}...")
                            resolve_citations(paper, paper.citations, db)
                            
                            log_job(db, "worker_embed", "SUCCESS", {"arxiv_id": paper.arxiv_id, "citations_count": len(result['citations'])})
                        else:
                            # Re-fetch paper in case session was tainted by failed flush elsewhere
                            logger.warning(f"Step 2: No result for {paper.arxiv_id}, rolling back...")
                            db.rollback()
                            paper = db.query(Paper).filter(Paper.id == paper.id).first()
                            paper.extracted_abstract = "[FAILED]"
                            paper.extracted_introduction = "Extraction failed: corrupted PDF or incompatible format"
                            db.commit()
                            log_job(db, "worker_embed", "FAILED", {"arxiv_id": paper.arxiv_id}, "Extraction failed")

                    # --- STEP 2.5: SYNC SEARCH EMBEDDING (3072d) ---
                    # ensure it exists in PaperEmbedding table for semantic search
                    try:
                        search_text = paper.summary or paper.extracted_abstract or paper.title
                        if not search_text or search_text == "[FAILED]" or search_text == "[DOWNLOAD FAILED]":
                            logger.warning(f"No valid text to embed for {paper.arxiv_id}, skipping search sync.")
                        else:
                            # Check if entry already exists
                            existing_emb = db.query(PaperEmbedding).filter(PaperEmbedding.paper_id == paper.id).first()
                            if not existing_emb:
                                logger.info(f"Generating search embedding (768d) for {paper.arxiv_id}...")
                                search_emb = embedding_service.generate_embedding(embedding_service.sanitize_text(search_text))
                                if search_emb:
                                    new_emb = PaperEmbedding(
                                        paper_id=paper.id,
                                        embedding=search_emb,
                                        embedding_config={"purpose": "search", "dimension": 768},
                                        embedding_metadata={"source_model": "gemini-embedding-001"}
                                    )
                                    db.add(new_emb)
                                    db.commit()
                                    logger.info(f"Created PaperEmbedding for {paper.arxiv_id}")
                                else:
                                    logger.warning(f"Failed to generate search embedding for {paper.arxiv_id}")
                    except Exception as sync_err:
                        logger.error(f"Failed to sync search embedding for {paper.arxiv_id}: {sync_err}")
                        db.rollback()

                    # --- STEP 3: PATTERN CLASSIFICATION ---
                    try:
                        existing_pattern = db.query(PatternExperimentResult).filter(
                            PatternExperimentResult.arxiv_id == paper.arxiv_id,
                            PatternExperimentResult.prompt_version == TAXONOMY_PROMPT_VERSION,
                        ).first()

                        if not existing_pattern:
                            abstract_text = paper.extracted_abstract or paper.summary or ""
                            if abstract_text and abstract_text not in ("[FAILED]", "[DOWNLOAD FAILED]") and len(abstract_text) > 50:
                                logger.info(f"Step 3: Classifying patterns for {paper.arxiv_id}...")
                                start_time = time.time()
                                parsed = llm_service.classify_paper(paper.title, abstract_text)
                                elapsed = time.time() - start_time

                                if parsed is None:
                                    result = PatternExperimentResult(
                                        arxiv_id=paper.arxiv_id,
                                        paper_title=(paper.title or "")[:200],
                                        prompt_version=TAXONOMY_PROMPT_VERSION,
                                        model_name=getattr(llm_service, 'model_name', getattr(llm_service, 'chat_model', 'unknown')),
                                        is_agentic=None,
                                        primary_category=None,
                                        reasoning=None,
                                        patterns=None,
                                        raw_json=None,
                                        num_patterns=0,
                                        taxonomy_violations=["PARSE_FAILED"],
                                        num_violations=1,
                                        elapsed_seconds=elapsed,
                                        error="LLM returned None",
                                    )
                                else:
                                    issues = validate_classification_output(parsed)
                                    result = PatternExperimentResult(
                                        arxiv_id=paper.arxiv_id,
                                        paper_title=(paper.title or "")[:200],
                                        prompt_version=TAXONOMY_PROMPT_VERSION,
                                        model_name=getattr(llm_service, 'model_name', getattr(llm_service, 'chat_model', 'unknown')),
                                        is_agentic=parsed.get("is_agentic"),
                                        primary_category=parsed.get("primary_category"),
                                        reasoning=parsed.get("reasoning", ""),
                                        patterns=parsed.get("patterns", []),
                                        raw_json=parsed,
                                        num_patterns=len(parsed.get("patterns", [])),
                                        taxonomy_violations=issues if issues else None,
                                        num_violations=len(issues),
                                        elapsed_seconds=elapsed,
                                        error=None,
                                    )

                                db.add(result)
                                db.commit()
                                agentic_str = str(result.is_agentic)[:5] if result.is_agentic is not None else "err"
                                logger.info(f"Step 3: Classified {paper.arxiv_id} -> {result.primary_category} (agentic={agentic_str}) in {elapsed:.1f}s")
                                log_job(db, "worker_classify", "SUCCESS", {"arxiv_id": paper.arxiv_id, "is_agentic": result.is_agentic, "category": result.primary_category})
                            else:
                                logger.info(f"Step 3: Skipping classification for {paper.arxiv_id} (insufficient abstract text)")
                    except Exception as classify_err:
                        logger.error(f"Step 3: Classification failed for {paper.arxiv_id}: {classify_err}")
                        db.rollback()
                        log_job(db, "worker_classify", "FAILED", {"arxiv_id": paper.arxiv_id}, str(classify_err))

                    logger.info(f"Completed processing state for {paper.arxiv_id}")
                    time.sleep(1) # Breathe between papers
                            
                except Exception as paper_err:
                     logger.error(f"Critical error processing {paper.arxiv_id}: {paper_err}")
                     db.rollback()
                     log_job(db, "worker_process", "FAILED", {"arxiv_id": paper.arxiv_id}, str(paper_err))
            
            time.sleep(15) # Pulse every 15s instead of 2s

        except Exception as e:
            logger.error(f"Worker Loop Error: {e}")
            try:
                db.rollback()
            except:
                pass
            time.sleep(30)
        finally:
            db.close()

if __name__ == "__main__":
    if "--backfill" in sys.argv:
        backfill_citation_links(SessionLocal)
    else:
        run_worker()
