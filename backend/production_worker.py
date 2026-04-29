
import sys
import os
import time
import re
import logging
import datetime
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# Ensure logs can handle UTF-8 symbols
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        # Fallback for older python versions
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8')
from sqlalchemy import create_engine, or_, and_
from sqlalchemy.orm import sessionmaker, scoped_session
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

# Pool sized to comfortably accommodate WORKER_CONCURRENCY + scheduler/API
# usage. SQLAlchemy default is 5 — too small for parallel workers.
engine = create_engine(
    DB_URL,
    pool_size=max(10, settings.WORKER_CONCURRENCY + 5),
    max_overflow=20,
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Limits simultaneous LLM/embedding HTTP calls to LiteLLM/Ollama. The worker
# pool itself is wider so I/O (PDF download, DB) keeps moving while heavy
# inference is gated.
_llm_semaphore = threading.Semaphore(max(1, settings.WORKER_LLM_CONCURRENCY))


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
            error_message=error,
        )
        db.add(job)
        db.commit()
    except Exception as e:
        logger.error(f"Failed to write job log: {e}")


def _fetch_pending_paper_ids(db, batch_size: int) -> list[int]:
    """Fetch a batch of paper IDs that need processing.

    Returns IDs (not ORM objects) so each worker thread loads its own
    instance under its own session — avoids SQLAlchemy cross-session bugs.
    """
    query = db.query(Paper.id).outerjoin(PaperEmbedding).filter(
        or_(
            Paper.is_downloaded == False,
            Paper.extracted_abstract.is_(None),
            Paper.citations.is_(None),
            PaperEmbedding.id.is_(None),
        )
    ).filter(
        or_(
            Paper.extracted_abstract.is_(None),
            and_(
                Paper.extracted_abstract != "[FAILED]",
                Paper.extracted_abstract != "[DOWNLOAD FAILED]",
            ),
        )
    )

    if settings.WORKER_BACKLOG_DAYS and settings.WORKER_BACKLOG_DAYS > 0:
        cutoff = (
            datetime.datetime.now()
            - datetime.timedelta(days=settings.WORKER_BACKLOG_DAYS)
        ).date()
        query = query.filter(Paper.published_date >= cutoff)

    rows = query.order_by(Paper.published_date.desc()).limit(batch_size).all()
    return [row[0] for row in rows]


def _download_step(db, paper) -> str | None:
    """Returns local PDF path or None if download failed (paper marked as failed)."""
    pdf_path = get_local_pdf_path(paper.arxiv_id)
    if pdf_path and paper.is_downloaded:
        return pdf_path

    if not pdf_path:
        url = paper.pdf_url or f"https://arxiv.org/pdf/{paper.arxiv_id}.pdf"
        pdf_path = download_pdf(url, paper.arxiv_id)

    if pdf_path:
        paper.is_downloaded = True
        db.commit()
        log_job(db, "worker_download", "SUCCESS", {"arxiv_id": paper.arxiv_id})
        return pdf_path

    paper.is_downloaded = True
    paper.extracted_abstract = "[DOWNLOAD FAILED]"
    paper.extracted_introduction = "[DOWNLOAD FAILED]"
    db.commit()
    log_job(
        db, "worker_download", "FAILED",
        {"arxiv_id": paper.arxiv_id}, "Download failed / 404",
    )
    return None


def _extract_step(db, paper, processor, pdf_path: str) -> None:
    needs_extract = (
        not paper.extracted_abstract
        or paper.extracted_abstract == "[FAILED]"
        or paper.citations is None
    )
    if not needs_extract:
        return

    logger.info(f"Step 2: Starting PDF processing for {paper.arxiv_id}...")
    with _llm_semaphore:
        result = processor.process_pdf(pdf_path)

    if not result:
        logger.warning(f"Step 2: No result for {paper.arxiv_id}, rolling back...")
        db.rollback()
        paper = db.query(Paper).filter(Paper.id == paper.id).first()
        paper.extracted_abstract = "[FAILED]"
        paper.extracted_introduction = (
            "Extraction failed: corrupted PDF or incompatible format"
        )
        db.commit()
        log_job(
            db, "worker_embed", "FAILED",
            {"arxiv_id": paper.arxiv_id}, "Extraction failed",
        )
        return

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

    logger.info(f"Step 2.1: Resolving citations for {paper.arxiv_id}...")
    resolve_citations(paper, paper.citations, db)

    log_job(
        db, "worker_embed", "SUCCESS",
        {"arxiv_id": paper.arxiv_id, "citations_count": len(result['citations'])},
    )


def _search_embedding_step(db, paper) -> None:
    try:
        search_text = paper.summary or paper.extracted_abstract or paper.title
        if (
            not search_text
            or search_text == "[FAILED]"
            or search_text == "[DOWNLOAD FAILED]"
        ):
            logger.warning(f"No valid text to embed for {paper.arxiv_id}, skipping search sync.")
            return

        existing_emb = (
            db.query(PaperEmbedding)
            .filter(PaperEmbedding.paper_id == paper.id)
            .first()
        )
        if existing_emb:
            return

        logger.info(f"Generating search embedding (768d) for {paper.arxiv_id}...")
        with _llm_semaphore:
            search_emb = embedding_service.generate_embedding(
                embedding_service.sanitize_text(search_text)
            )
        if not search_emb:
            logger.warning(f"Failed to generate search embedding for {paper.arxiv_id}")
            return

        new_emb = PaperEmbedding(
            paper_id=paper.id,
            embedding=search_emb,
            embedding_config={"purpose": "search", "dimension": 768},
            embedding_metadata={"source_model": "gemini-embedding-001"},
        )
        db.add(new_emb)
        db.commit()
        logger.info(f"Created PaperEmbedding for {paper.arxiv_id}")
    except Exception as sync_err:
        logger.error(f"Failed to sync search embedding for {paper.arxiv_id}: {sync_err}")
        db.rollback()


def _classify_step(db, paper) -> None:
    try:
        existing = (
            db.query(PatternExperimentResult)
            .filter(
                PatternExperimentResult.arxiv_id == paper.arxiv_id,
                PatternExperimentResult.prompt_version == TAXONOMY_PROMPT_VERSION,
            )
            .first()
        )
        if existing:
            return

        abstract_text = paper.extracted_abstract or paper.summary or ""
        if (
            not abstract_text
            or abstract_text in ("[FAILED]", "[DOWNLOAD FAILED]")
            or len(abstract_text) <= 50
        ):
            logger.info(f"Step 3: Skipping classification for {paper.arxiv_id} (insufficient abstract text)")
            return

        logger.info(f"Step 3: Classifying patterns for {paper.arxiv_id}...")
        start = time.time()
        with _llm_semaphore:
            parsed = llm_service.classify_paper(paper.title, abstract_text)
        elapsed = time.time() - start

        model_name = getattr(
            llm_service, 'model_name',
            getattr(llm_service, 'chat_model', 'unknown'),
        )

        if parsed is None:
            result = PatternExperimentResult(
                arxiv_id=paper.arxiv_id,
                paper_title=(paper.title or "")[:200],
                prompt_version=TAXONOMY_PROMPT_VERSION,
                model_name=model_name,
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
                model_name=model_name,
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
        agentic_str = (
            str(result.is_agentic)[:5] if result.is_agentic is not None else "err"
        )
        logger.info(
            f"Step 3: Classified {paper.arxiv_id} -> {result.primary_category} "
            f"(agentic={agentic_str}) in {elapsed:.1f}s"
        )
        log_job(
            db, "worker_classify", "SUCCESS",
            {
                "arxiv_id": paper.arxiv_id,
                "is_agentic": result.is_agentic,
                "category": result.primary_category,
            },
        )
    except Exception as classify_err:
        logger.error(f"Step 3: Classification failed for {paper.arxiv_id}: {classify_err}")
        db.rollback()
        log_job(
            db, "worker_classify", "FAILED",
            {"arxiv_id": paper.arxiv_id}, str(classify_err),
        )


def _process_paper(paper_id: int, processor: PDFProcessorLite) -> str:
    """Run the full pipeline for one paper. Owns its own DB session.

    Exceptions are logged and swallowed so a single bad paper cannot crash
    its sibling tasks in the batch.
    """
    db = SessionLocal()
    arxiv_id = "?"
    try:
        paper = db.query(Paper).filter(Paper.id == paper_id).first()
        if not paper:
            return f"missing:{paper_id}"
        arxiv_id = paper.arxiv_id

        pdf_path = _download_step(db, paper)
        if not pdf_path:
            return f"download_failed:{arxiv_id}"

        _extract_step(db, paper, processor, pdf_path)
        _search_embedding_step(db, paper)
        _classify_step(db, paper)

        logger.info(f"Completed processing state for {arxiv_id}")
        return f"ok:{arxiv_id}"
    except Exception as paper_err:
        logger.error(f"Critical error processing {arxiv_id} (id={paper_id}): {paper_err}")
        try:
            db.rollback()
            log_job(
                db, "worker_process", "FAILED",
                {"arxiv_id": arxiv_id}, str(paper_err),
            )
        except Exception:
            pass
        return f"error:{arxiv_id}"
    finally:
        db.close()


def run_worker():
    logger.info("🚀 Starting Production Worker (Lite Mode, parallel).")
    logger.info(f"DB: {DB_URL}")
    logger.info(f"PDF_DIR: {PDF_DIR}")
    logger.info(
        f"Concurrency: workers={settings.WORKER_CONCURRENCY} "
        f"llm_cap={settings.WORKER_LLM_CONCURRENCY} "
        f"batch={settings.WORKER_BATCH_SIZE} "
        f"backlog_days={settings.WORKER_BACKLOG_DAYS or 'unlimited'}"
    )

    processor = PDFProcessorLite()
    executor = ThreadPoolExecutor(
        max_workers=settings.WORKER_CONCURRENCY,
        thread_name_prefix="paper-worker",
    )

    try:
        while True:
            db = SessionLocal()
            try:
                paper_ids = _fetch_pending_paper_ids(db, settings.WORKER_BATCH_SIZE)
            except Exception as fetch_err:
                logger.error(f"Failed to fetch pending papers: {fetch_err}")
                paper_ids = []
            finally:
                db.close()

            if not paper_ids:
                time.sleep(settings.WORKER_IDLE_SLEEP_SECONDS)
                continue

            logger.info(
                f"Dispatching batch of {len(paper_ids)} papers across "
                f"{settings.WORKER_CONCURRENCY} workers..."
            )
            batch_start = time.time()
            futures = {
                executor.submit(_process_paper, pid, processor): pid
                for pid in paper_ids
            }
            ok = failed = 0
            for fut in as_completed(futures):
                try:
                    outcome = fut.result()
                    if outcome.startswith("ok:"):
                        ok += 1
                    else:
                        failed += 1
                except Exception as e:
                    failed += 1
                    logger.error(f"Worker task crashed: {e}")

            elapsed = time.time() - batch_start
            logger.info(
                f"Batch complete: ok={ok} failed/skipped={failed} "
                f"in {elapsed:.1f}s ({elapsed/max(len(paper_ids),1):.1f}s/paper)"
            )
            time.sleep(settings.WORKER_BATCH_PAUSE_SECONDS)
    finally:
        executor.shutdown(wait=True)


if __name__ == "__main__":
    if "--backfill" in sys.argv:
        backfill_citation_links(SessionLocal)
    else:
        run_worker()
