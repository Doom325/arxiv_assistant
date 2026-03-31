from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, cast, Date, text
from database import get_db
from models import Paper, UserLibrary
from typing import Optional
from datetime import date, timedelta, datetime

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/papers-over-time")
@router.get("/papers-over-time/")
async def papers_over_time(
    granularity: str = Query("day", regex="^(day|week|month)$"),
    days: int = Query(14, ge=1, le=365),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Papers published per time bucket, for sparkline/area charts."""
    cutoff = datetime.utcnow() - timedelta(days=days)

    q = (
        db.query(
            func.date_trunc(granularity, Paper.published_date).label("bucket"),
            func.count(Paper.id).label("count"),
        )
        .filter(Paper.published_date >= cutoff)
    )
    if category:
        q = q.filter(Paper.category == category)

    rows = q.group_by("bucket").order_by("bucket").all()

    return [
        {"date": row.bucket.strftime("%Y-%m-%d") if row.bucket else None, "count": row.count}
        for row in rows
    ]


@router.get("/category-distribution")
@router.get("/category-distribution/")
async def category_distribution(
    days: int = Query(30, ge=1, le=365),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Paper counts by arXiv category."""
    cutoff = datetime.utcnow() - timedelta(days=days)

    q = (
        db.query(Paper.category, func.count(Paper.id).label("count"))
        .filter(Paper.published_date >= cutoff)
    )
    if category:
        q = q.filter(Paper.category == category)

    rows = q.group_by(Paper.category).order_by(desc("count")).all()

    return [{"category": row.category or "unknown", "count": row.count} for row in rows]


@router.get("/summary-stats")
@router.get("/summary-stats/")
async def summary_stats(
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """High-level numbers for dashboard stat tiles."""
    today = date.today()
    yesterday = today - timedelta(days=1)

    cat_filter = [Paper.category == category] if category else []

    total_papers = (
        db.query(func.count(Paper.id)).filter(*cat_filter).scalar() or 0
    )
    today_count = (
        db.query(func.count(Paper.id))
        .filter(cast(Paper.published_date, Date) == today, *cat_filter)
        .scalar() or 0
    )
    yesterday_count = (
        db.query(func.count(Paper.id))
        .filter(cast(Paper.published_date, Date) == yesterday, *cat_filter)
        .scalar() or 0
    )
    library_count = db.query(func.count(func.distinct(UserLibrary.paper_id))).scalar() or 0
    category_count = 1 if category else (
        db.query(func.count(func.distinct(Paper.category))).scalar() or 0
    )

    return {
        "total_papers": total_papers,
        "today_count": today_count,
        "yesterday_count": yesterday_count,
        "library_count": library_count,
        "category_count": category_count,
    }
