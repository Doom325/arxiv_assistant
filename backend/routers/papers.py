import logging
import os
import re
import tempfile
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
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
from schemas import PaperResponse, PaperFullTextResponse
from services.arxiv_service import arxiv_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/papers", tags=["papers"])

# Disk-full is the one download failure with a dedicated HTTP status; every
# other failure is an upstream/gateway problem (502).
_PDF_DOWNLOAD_HTTP_STATUS = {"pdf_disk_full": 507}


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
def get_paper(paper_id_or_arxiv_id: str, db: Session = Depends(get_db)):
    paper = _resolve_paper(db, paper_id_or_arxiv_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
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
    # 1. Look up paper (same pattern as get_paper)
    try:
        paper_id = int(paper_id_or_arxiv_id)
        paper = db.query(Paper).filter(Paper.id == paper_id).first()
    except ValueError:
        paper = db.query(Paper).filter(Paper.arxiv_id == paper_id_or_arxiv_id).first()

    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

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
    paper = _resolve_paper(db, paper_id_or_arxiv_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

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


@router.get("/{paper_id_or_arxiv_id}/similar", response_model=List[PaperResponse])
def get_similar_papers(paper_id_or_arxiv_id: str, limit: int = 6, db: Session = Depends(get_db)):
    # 1. Fetch reference paper
    try:
        paper_id = int(paper_id_or_arxiv_id)
        ref_paper = db.query(Paper).filter(Paper.id == paper_id).first()
    except ValueError:
        ref_paper = db.query(Paper).filter(Paper.arxiv_id == paper_id_or_arxiv_id).first()
        
    if not ref_paper:
        raise HTTPException(status_code=404, detail="Reference paper not found")
        
    if ref_paper.embedding is None:
        # Check if it has an embedding in the new table
        item = db.query(PaperEmbedding).filter(PaperEmbedding.paper_id == ref_paper.id).first()
        if not item:
            return []
        ref_embedding = item.embedding
    else:
        ref_embedding = ref_paper.embedding

    # 2. Vector search for similar papers using cosine similarity
    # We join with Paper to return Paper objects
    similar_results = db.query(Paper).join(PaperEmbedding).filter(
        Paper.id != ref_paper.id
    ).order_by(
        PaperEmbedding.embedding.cosine_distance(ref_embedding)
    ).limit(limit).all()
    
    return similar_results

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
