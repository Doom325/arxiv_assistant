import asyncio
import logging
import math
import os
import re
import tempfile
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from config import settings
from core.pdf_utils import (
    PdfDownloadError,
    download_pdf_strict,
    get_local_pdf_path,
)
from database import get_db
from ingestion import process_paper_entry
from models import Paper, PaperEmbedding
from schemas import PaperResponse
from services.arxiv_service import arxiv_service
import services.llm_service as llm_module

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/papers", tags=["papers"])

# Disk-full is the one download failure with a dedicated HTTP status; every
# other failure is an upstream/gateway problem (502).
_PDF_DOWNLOAD_HTTP_STATUS = {"pdf_disk_full": 507}
_EMBED_TIMEOUT_SECONDS = 15.0
_EXPECTED_EMBEDDING_DIM = 768
_INVALID_TEXT_MARKERS = frozenset({"[FAILED]", "[DOWNLOAD FAILED]", "[NO_ABSTRACT]"})
_SEARCH_STOPWORDS = frozenset({
    "the", "and", "for", "with", "from", "that", "this", "into", "over",
    "under", "via", "using", "based", "towards", "toward", "study", "new",
    "meet", "meets", "beyond", "through", "between", "across", "their", "are",
})


def _resolve_paper(db: Session, paper_id_or_arxiv_id: str) -> Optional[Paper]:
    """Look a paper up by numeric PK, falling back to its arXiv id."""
    try:
        return db.query(Paper).filter(Paper.id == int(paper_id_or_arxiv_id)).first()
    except ValueError:
        return (
            db.query(Paper)
            .filter(Paper.arxiv_id == paper_id_or_arxiv_id)
            .first()
        )


def _get_paper_or_404(paper_id_or_arxiv_id: str, db: Session) -> Paper:
    """Resolve a paper by integer primary key or arXiv ID, raising 404 if absent."""
    paper = _resolve_paper(db, paper_id_or_arxiv_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return paper

@router.get("/", response_model=List[PaperResponse])
@router.get("", response_model=List[PaperResponse], include_in_schema=False)
def get_papers(
    skip: int = 0, 
    limit: int = 10000, 
    category: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Paper)
    
    if category:
        query = query.filter(Paper.category == category)
    if start_date:
        query = query.filter(Paper.published_date >= start_date)
    if end_date:
        query = query.filter(Paper.published_date <= end_date)
        
    papers = query.order_by(Paper.published_date.desc(), Paper.arxiv_id.desc()).offset(skip).limit(limit).all()
    return papers

@router.get("/{paper_id_or_arxiv_id}", response_model=PaperResponse)
def get_paper(paper_id_or_arxiv_id: str, db: Session = Depends(get_db)) -> Paper:
    paper = _get_paper_or_404(paper_id_or_arxiv_id, db)
    # Single-paper detail stats the file so the UI can offer an on-demand
    # download; list endpoints deliberately skip this per-row filesystem hit.
    paper.pdf_available = (
        get_local_pdf_path(paper.arxiv_id, settings.PDF_SAVE_DIR) is not None
    )
    return paper

@router.get("/{paper_id_or_arxiv_id}/images/{filename}")
def get_paper_image(paper_id_or_arxiv_id: str, filename: str):
    """Serve an extracted image from a paper's PDF."""
    # Sanitize filename to prevent path traversal
    filename = os.path.basename(filename)

    image_dir = os.path.join(tempfile.gettempdir(), "arxiv_images", paper_id_or_arxiv_id)
    filepath = os.path.join(image_dir, filename)

    if not os.path.isfile(filepath):
        raise HTTPException(status_code=404, detail="Image not found")

    ext = filename.rsplit(".", 1)[-1].lower()
    content_type = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "jxr": "image/jxr",
        "jp2": "image/jp2",
    }.get(ext, "application/octet-stream")

    return FileResponse(filepath, media_type=content_type)


@router.get("/{paper_id_or_arxiv_id}/full-text")
def get_paper_full_text(paper_id_or_arxiv_id: str, db: Session = Depends(get_db)):
    paper = _get_paper_or_404(paper_id_or_arxiv_id, db)

    # 2. Return cached if available
    if paper.full_text_sections:
        sections = paper.full_text_sections
        images = paper.extracted_images or []
        word_count = sum(len(s["content"].split()) for s in sections)
        return {
            "arxiv_id": paper.arxiv_id,
            "title": paper.title,
            "sections": sections,
            "images": images,
            "word_count": word_count,
            "estimated_reading_minutes": max(1, word_count // 250),
        }

    # 3. On-demand extraction
    from core.pdf_utils import get_local_pdf_path, download_pdf, extract_text_from_pdf, extract_images_from_pdf
    from core.text_utils import extract_all_sections, sanitize_text
    from config import settings

    pdf_dir = settings.PDF_SAVE_DIR
    # Fallback to temp dir if configured dir is unavailable
    if not os.path.isdir(pdf_dir):
        pdf_dir = os.path.join(tempfile.gettempdir(), "arxiv_pdfs")
        os.makedirs(pdf_dir, exist_ok=True)

    pdf_path = get_local_pdf_path(paper.arxiv_id, pdf_dir)
    if not pdf_path:
        try:
            pdf_path = download_pdf(paper.pdf_url, paper.arxiv_id, pdf_dir)
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Could not download PDF: {str(e)}")

    # Smart (format-aware) extraction with regex fallback
    try:
        from core.smart_pdf_extractor import extract_paper_smart
        sections = extract_paper_smart(pdf_path)
    except Exception as smart_err:
        logger.warning(
            "Smart PDF extraction failed for %s, falling back to regex: %s",
            paper.arxiv_id, smart_err,
        )
        try:
            full_text = extract_text_from_pdf(pdf_path)
            full_text = sanitize_text(full_text)
            sections = extract_all_sections(full_text)
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Text extraction failed: {str(e)}")

    # Extract images from PDF
    image_dir = os.path.join(tempfile.gettempdir(), "arxiv_images", paper.arxiv_id)
    try:
        images = extract_images_from_pdf(pdf_path, image_dir)
    except Exception as e:
        logger.warning(f"Image extraction failed for {paper.arxiv_id}: {e}")
        images = []

    # 4. Cache in DB
    paper.full_text_sections = sections
    paper.extracted_images = images
    db.commit()

    word_count = sum(len(s["content"].split()) for s in sections)
    return {
        "arxiv_id": paper.arxiv_id,
        "title": paper.title,
        "sections": sections,
        "images": images,
        "word_count": word_count,
        "estimated_reading_minutes": max(1, word_count // 250),
    }

def _pdf_error_detail(exc: PdfDownloadError) -> dict:
    """Shape a PdfDownloadError like the summarization ``summary_error`` body."""
    detail: dict = {
        "code": exc.code,
        "message": exc.message,
        "retryable": exc.retryable,
    }
    if exc.http_status is not None:
        detail["http_status"] = exc.http_status
    return detail


@router.post("/{paper_id_or_arxiv_id}/pdf/download")
def download_paper_pdf(paper_id_or_arxiv_id: str, db: Session = Depends(get_db)):
    """Idempotently ensure one paper's PDF is on local disk.

    Returns quickly when a valid PDF already exists; otherwise downloads that
    single paper via the shared validated/atomic helper. The arXiv id comes
    from the DB row, never the raw path, so no caller input reaches the
    filesystem. Failures surface as structured errors (disk full vs upstream)
    matching the summarization error shape.
    """
    paper = _get_paper_or_404(paper_id_or_arxiv_id, db)

    pdf_dir = settings.PDF_SAVE_DIR
    if get_local_pdf_path(paper.arxiv_id, pdf_dir):
        return {
            "status": "available",
            "pdf_available": True,
            "message": "PDF already available",
        }

    pdf_url = paper.pdf_url or f"https://arxiv.org/pdf/{paper.arxiv_id}.pdf"
    try:
        download_pdf_strict(pdf_url, paper.arxiv_id, pdf_dir)
    except PdfDownloadError as exc:
        raise HTTPException(
            status_code=_PDF_DOWNLOAD_HTTP_STATUS.get(exc.code, 502),
            detail=_pdf_error_detail(exc),
        ) from exc

    return {
        "status": "downloaded",
        "pdf_available": True,
        "message": "PDF downloaded",
    }


def _get_existing_embedding(ref_paper: Paper, db: Session) -> Optional[List[float]]:
    """Return stored search embedding from PaperEmbedding or legacy Paper.embedding."""
    item = db.query(PaperEmbedding).filter(PaperEmbedding.paper_id == ref_paper.id).first()
    if item is not None and item.embedding is not None and len(item.embedding) > 0:
        return list(item.embedding)
    if ref_paper.embedding is not None and len(ref_paper.embedding) > 0:
        return list(ref_paper.embedding)
    return None


def _select_embedding_text(paper: Paper) -> Optional[str]:
    """Pick the richest valid text field to embed without requiring PDF download."""
    for candidate in (paper.summary, paper.extracted_abstract, paper.title):
        cleaned = (candidate or "").strip()
        if cleaned and cleaned not in _INVALID_TEXT_MARKERS:
            return cleaned
    return None


def _upsert_paper_embedding(
    paper_id: int,
    vector: List[float],
    source_model: str,
    db: Session,
) -> None:
    """Persist or refresh the PaperEmbedding row for a paper safely under concurrency."""
    existing = db.query(PaperEmbedding).filter(PaperEmbedding.paper_id == paper_id).first()
    if existing is not None:
        try:
            existing.embedding = vector
            db.commit()
        except Exception as exc:
            db.rollback()
            logger.error("event=similar_embed_update_failed paper_id=%s error=%s", paper_id, exc)
        return

    new_emb = PaperEmbedding(
        paper_id=paper_id,
        embedding=vector,
        embedding_config={"purpose": "search", "dimension": len(vector)},
        embedding_metadata={"source_model": source_model, "trigger": "on_demand"},
    )
    try:
        db.add(new_emb)
        db.commit()
    except IntegrityError:
        db.rollback()
    except Exception as exc:
        db.rollback()
        logger.error("event=similar_embed_insert_failed paper_id=%s error=%s", paper_id, exc)


async def _generate_and_store_embedding(
    ref_paper: Paper,
    db: Session,
) -> Optional[List[float]]:
    """Generate an embedding via the configured provider with a bounded timeout and cache it."""
    raw_text = _select_embedding_text(ref_paper)
    if not raw_text:
        return None

    svc = llm_module.embedding_service
    sanitized = svc.sanitize_text(raw_text)
    try:
        generated = await asyncio.wait_for(
            asyncio.to_thread(svc.generate_embedding, sanitized),
            timeout=_EMBED_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        logger.error("event=similar_embed_timeout arxiv_id=%s", ref_paper.arxiv_id)
        return None
    except Exception as exc:
        logger.error("event=similar_embed_failed arxiv_id=%s error=%s", ref_paper.arxiv_id, exc)
        return None

    if not generated:
        logger.warning("event=similar_embed_empty arxiv_id=%s", ref_paper.arxiv_id)
        return None

    vector = list(generated)
    if "sqlite" not in settings.DATABASE_URL and len(vector) != _EXPECTED_EMBEDDING_DIM:
        logger.error("event=similar_embed_dim_mismatch arxiv_id=%s dim=%d", ref_paper.arxiv_id, len(vector))
        return None

    model_name = getattr(svc, "embedding_model", "unknown")
    _upsert_paper_embedding(ref_paper.id, vector, str(model_name), db)
    return vector


def _dedupe_papers(papers: List[Paper], limit: int) -> List[Paper]:
    """Preserve rank order while removing duplicate Paper rows from 1:N joins."""
    seen_ids: set[int] = set()
    unique: List[Paper] = []
    for paper in papers:
        if paper.id in seen_ids:
            continue
        seen_ids.add(paper.id)
        unique.append(paper)
        if len(unique) >= limit:
            break
    return unique


def _cosine_distance(vec_a: List[float], vec_b: List[float]) -> float:
    """Compute cosine distance in [0, 2] for SQLite test environments lacking pgvector."""
    if len(vec_a) != len(vec_b) or not vec_a:
        return 1.0
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 1.0
    return 1.0 - (dot / (norm_a * norm_b))


def _query_sqlite_vector_similar(
    ref_paper_id: int,
    ref_embedding: List[float],
    limit: int,
    db: Session,
) -> List[Paper]:
    """Rank PaperEmbedding rows in Python when running against SQLite in tests."""
    rows = (
        db.query(Paper, PaperEmbedding)
        .join(PaperEmbedding, Paper.id == PaperEmbedding.paper_id)
        .filter(Paper.id != ref_paper_id)
        .all()
    )
    scored = sorted(
        rows,
        key=lambda pair: _cosine_distance(list(pair[1].embedding or []), ref_embedding),
    )
    return _dedupe_papers([paper for paper, _ in scored], limit)


def _query_vector_similar(
    ref_paper_id: int,
    ref_embedding: List[float],
    limit: int,
    db: Session,
) -> List[Paper]:
    """Query nearest neighbors by cosine distance in pgvector (or SQLite fallback)."""
    if "sqlite" in settings.DATABASE_URL:
        return _query_sqlite_vector_similar(ref_paper_id, ref_embedding, limit, db)
    try:
        candidates = (
            db.query(Paper)
            .join(PaperEmbedding, Paper.id == PaperEmbedding.paper_id)
            .filter(Paper.id != ref_paper_id)
            .order_by(PaperEmbedding.embedding.cosine_distance(ref_embedding))
            .limit(limit * 2)
            .all()
        )
        return _dedupe_papers(candidates, limit)
    except Exception as exc:
        db.rollback()
        logger.error("event=similar_vector_query_failed paper_id=%s error=%s", ref_paper_id, exc)
        return []


def _extract_search_tokens(text: str) -> List[str]:
    """Extract distinct content words from title/abstract for full-text fallback."""
    words = re.findall(r"[a-z0-9]{3,}", (text or "").lower())
    seen: set[str] = set()
    tokens: List[str] = []
    for word in words:
        if word in _SEARCH_STOPWORDS or word in seen:
            continue
        seen.add(word)
        tokens.append(word)
        if len(tokens) >= 12:
            break
    return tokens


def _query_keyword_similar(ref_paper: Paper, limit: int, db: Session) -> List[Paper]:
    """Fallback similarity search via PostgreSQL tsvector (or SQLite ILIKE) when embeddings fail."""
    tokens = _extract_search_tokens(ref_paper.title or ref_paper.summary or "")
    if not tokens:
        return []

    if "sqlite" not in settings.DATABASE_URL:
        or_query = " OR ".join(tokens)
        ts_query = func.websearch_to_tsquery("english", or_query)
        return (
            db.query(Paper)
            .filter(Paper.id != ref_paper.id, Paper.search_vector.op("@@")(ts_query))
            .order_by(func.ts_rank_cd(Paper.search_vector, ts_query).desc())
            .limit(limit)
            .all()
        )

    clauses = [Paper.title.ilike(f"%{tok}%") | Paper.summary.ilike(f"%{tok}%") for tok in tokens]
    candidates = db.query(Paper).filter(Paper.id != ref_paper.id, or_(*clauses)).limit(limit * 5).all()
    candidates.sort(
        key=lambda p: sum(
            tok in f"{p.title or ''} {p.summary or ''}".lower() for tok in tokens
        ),
        reverse=True,
    )
    return candidates[:limit]


@router.get("/{paper_id_or_arxiv_id}/similar", response_model=List[PaperResponse])
async def get_similar_papers(
    paper_id_or_arxiv_id: str,
    limit: int = Query(default=6, ge=1, le=50),
    db: Session = Depends(get_db),
) -> List[Paper]:
    ref_paper = _get_paper_or_404(paper_id_or_arxiv_id, db)
    ref_embedding = _get_existing_embedding(ref_paper, db)
    if ref_embedding is None:
        return []
    return _query_vector_similar(ref_paper.id, ref_embedding, limit, db)


@router.post("/{paper_id_or_arxiv_id}/similar", response_model=List[PaperResponse])
async def find_similar_papers(
    paper_id_or_arxiv_id: str,
    limit: int = Query(default=6, ge=1, le=50),
    force: bool = False,
    db: Session = Depends(get_db),
) -> List[Paper]:
    """Generate and cache a missing PaperEmbedding on demand, then return similar papers."""
    ref_paper = _get_paper_or_404(paper_id_or_arxiv_id, db)
    ref_embedding = None if force else _get_existing_embedding(ref_paper, db)

    if ref_embedding is None:
        ref_embedding = await _generate_and_store_embedding(ref_paper, db)
    if ref_embedding is None and force:
        ref_embedding = _get_existing_embedding(ref_paper, db)

    if ref_embedding is not None:
        vector_matches = _query_vector_similar(ref_paper.id, ref_embedding, limit, db)
        if vector_matches:
            return vector_matches

    return _query_keyword_similar(ref_paper, limit, db)

class AddPaperRequest(BaseModel):
    query: str

@router.post("/add", response_model=PaperResponse)
def add_paper(request: AddPaperRequest, db: Session = Depends(get_db)):
    """
    Manually add a paper by arXiv ID or URL.
    """
    query = request.query.strip()
    
    # 1. Extract ArXiv ID from URL if necessary
    arxiv_id = query
    
    # Handle URL formats:
    # https://arxiv.org/abs/2402.12345
    # https://arxiv.org/pdf/2402.12345.pdf
    if "arxiv.org" in query:
        # Match pattern after /abs/ or /pdf/
        match = re.search(r'(?:abs|pdf)/(\d{4}\.\d{4,5}(?:v\d+)?)', query)
        if match:
            arxiv_id = match.group(1)
        else:
            # Fallback for just stripping the end if it looks like an ID
            arxiv_id = query.split('/')[-1].replace('.pdf', '')
            
    # 2. Fetch Metadata from ArXiv
    logger.info(f"Manual add request for: {arxiv_id}")
    paper_metadata = arxiv_service.get_paper_by_id(arxiv_id)
    
    if not paper_metadata:
        raise HTTPException(status_code=404, detail=f"Could not find paper with ID {arxiv_id} on arXiv.")
        
    # 3. Ingest into DB
    paper = process_paper_entry(db, paper_metadata)
    
    if not paper:
        # Paper already exists or process_paper_entry returned None
        # Use the ID from metadata which is canonical (includes version if applicable)
        canonical_id = paper_metadata['arxiv_id']
        paper = db.query(Paper).filter(Paper.arxiv_id == canonical_id).first()
        if not paper:
             raise HTTPException(status_code=500, detail=f"Conflict adding paper {canonical_id} but existing entry not found.")
             
    return paper
