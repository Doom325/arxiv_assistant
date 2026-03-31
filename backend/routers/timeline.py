"""Timeline API — citation graph visualization endpoints."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from services.timeline_service import (
    TimelineResponse,
    build_timeline_from_topic,
    build_timeline_from_paper,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/timeline", tags=["timeline"])


@router.get("/topic", response_model=TimelineResponse)
def get_timeline_by_topic(
    q: str = Query(..., min_length=1, description="Topic search query"),
    limit: int = Query(50, ge=10, le=100, description="Max papers to include"),
    library_only: bool = Query(False, description="Only include papers in user's library"),
    db: Session = Depends(get_db),
):
    """Build a timeline from a topic query via semantic search."""
    try:
        return build_timeline_from_topic(q, db, limit=limit, library_only=library_only)
    except Exception as e:
        logger.error("Timeline topic query failed: %s", e)
        raise HTTPException(status_code=500, detail="Timeline generation failed")


@router.get("/paper/{paper_id}", response_model=TimelineResponse)
def get_timeline_by_paper(
    paper_id: int,
    hops: int = Query(2, ge=1, le=3, description="Citation traversal depth"),
    db: Session = Depends(get_db),
):
    """Build a timeline radiating from a seed paper."""
    try:
        return build_timeline_from_paper(paper_id, db, hops=hops)
    except Exception as e:
        logger.error("Timeline paper query failed for %d: %s", paper_id, e)
        raise HTTPException(status_code=500, detail="Timeline generation failed")
