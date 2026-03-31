"""Reading queue router — discovery + prioritized reading list."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from services import reading_queue_service as rqs

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/queue", tags=["queue"])


# ── Response Schemas ──────────────────────────────────────


class QueueItemResponse(BaseModel):
    paper_id: int
    arxiv_id: str
    title: str
    authors: object = None
    summary: object = None
    published_date: Optional[str] = None
    category: str = ""
    pdf_url: str = ""
    generated_summary: Optional[str] = None
    priority_score: float = 0.0
    interest_similarity: float = 0.0
    citation_impact: float = 0.0
    freshness_score: float = 0.0
    category_score: float = 0.0
    entity_overlap: float = 0.0
    peer_reads_score: float = 0.0
    read_status: str = "unread"
    source: str = "bookmark"
    best_match_paper_id: Optional[int] = None
    best_match_score: Optional[float] = None
    best_match_title: Optional[str] = None
    manual_priority: Optional[int] = None
    added_at: Optional[str] = None
    scored_at: Optional[str] = None
    read_at: Optional[str] = None


class QueueStatsResponse(BaseModel):
    total_unread: int = 0
    total_reading: int = 0
    total_read: int = 0
    total_skipped: int = 0
    discovery_unread: int = 0
    bookmark_unread: int = 0
    avg_priority: float = 0.0
    high_priority_count: int = 0
    estimated_reading_hours: float = 0.0


class ManualPriorityRequest(BaseModel):
    priority: Optional[int] = None


# ── Endpoints ─────────────────────────────────────────────


@router.get("", response_model=list[QueueItemResponse])
def get_queue(
    status: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """Get the prioritized reading queue."""
    return rqs.get_queue(
        db, status=status, source=source, limit=limit, offset=offset
    )


@router.get("/stats", response_model=QueueStatsResponse)
def get_queue_stats(db: Session = Depends(get_db)):
    """Get queue statistics."""
    return rqs.get_queue_stats(db)


@router.post("/discover")
def run_discovery(
    since_days: int = 7,
    db: Session = Depends(get_db),
):
    """Run discovery pipeline: find relevant recent papers."""
    added = rqs.run_discovery(db, since_days=since_days)
    return {"message": "Discovery complete", "added": added}


@router.post("/rescore")
def rescore_queue(db: Session = Depends(get_db)):
    """Manually trigger library sync + full rescore."""
    added, removed = rqs.sync_queue_from_library(db)
    rescored = rqs.rescore_queue(db)
    return {
        "message": "Rescore complete",
        "added": added,
        "removed": removed,
        "rescored": rescored,
    }


@router.post("/{paper_id}/read")
def mark_read(paper_id: int, db: Session = Depends(get_db)):
    entry = rqs.mark_read(db, paper_id)
    if not entry:
        raise HTTPException(404, "Paper not in queue")
    return {"message": "Marked as read"}


@router.post("/{paper_id}/reading")
def mark_reading(paper_id: int, db: Session = Depends(get_db)):
    entry = rqs.mark_reading(db, paper_id)
    if not entry:
        raise HTTPException(404, "Paper not in queue")
    return {"message": "Marked as reading"}


@router.post("/{paper_id}/skip")
def mark_skipped(paper_id: int, db: Session = Depends(get_db)):
    entry = rqs.mark_skipped(db, paper_id)
    if not entry:
        raise HTTPException(404, "Paper not in queue")
    return {"message": "Marked as skipped"}


@router.patch("/{paper_id}/priority")
def set_manual_priority(
    paper_id: int,
    body: ManualPriorityRequest,
    db: Session = Depends(get_db),
):
    if body.priority is not None and body.priority not in (1, 2, 3):
        raise HTTPException(400, "Priority must be 1, 2, 3, or null")
    entry = rqs.update_manual_priority(db, paper_id, body.priority)
    if not entry:
        raise HTTPException(404, "Paper not in queue")
    return {"message": "Priority updated"}


@router.delete("/{paper_id}")
def remove_from_queue(paper_id: int, db: Session = Depends(get_db)):
    deleted = rqs.remove_from_queue(db, paper_id)
    if not deleted:
        raise HTTPException(404, "Paper not in queue")
    return {"message": "Removed from queue"}
