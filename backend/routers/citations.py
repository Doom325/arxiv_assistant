from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from database import get_db
from models import Paper, CitationLink
from typing import List, Optional
from datetime import date

router = APIRouter(prefix="/citations", tags=["citations"])

@router.get("/top")
@router.get("/top/")
async def get_top_citations(
    limit: int = Query(50, ge=1, le=200),
    category: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """
    Returns the most frequently cited papers based on our local analysis.
    Joins with the Paper table to get full metadata for resolved citations.
    """
    
    # Query for top citations across all links (arXiv and non-arXiv)
    query = db.query(
        CitationLink.target_arxiv_id,
        CitationLink.target_title,
        CitationLink.target_url,
        CitationLink.resolved_paper_id,
        func.count(CitationLink.id).label("citation_count")
    )
    
    if category or start_date or end_date:
        # Join with Paper table to filter by TARGET metadata
        # (Only works for resolved arXiv papers currently)
        query = query.outerjoin(Paper, CitationLink.resolved_paper_id == Paper.id)
        
        if category:
            query = query.filter(Paper.category == category)
            
        if start_date:
            query = query.filter(func.date(Paper.published_date) >= start_date)
            
        if end_date:
            query = query.filter(func.date(Paper.published_date) <= end_date)
    
    # Group by all target identifiers and order by count
    top_citations = query.group_by(
                            CitationLink.target_arxiv_id, 
                            CitationLink.target_title,
                            CitationLink.target_url,
                            CitationLink.resolved_paper_id
                         )\
                         .order_by(desc("citation_count"))\
                         .limit(limit)\
                         .all()
    
    results = []
    for arxiv_id, title, url, resolved_id, count in top_citations:
        # If we have a resolved_id, get the metadata from our DB
        paper_metadata = None
        if resolved_id:
            paper = db.query(Paper).filter(Paper.id == resolved_id).first()
            if paper:
                paper_metadata = {
                    "id": paper.id,
                    "arxiv_id": paper.arxiv_id,
                    "title": paper.title,
                    "authors": paper.authors,
                    "category": paper.category,
                    "published_date": paper.published_date
                }
        elif not arxiv_id and title:
            # For non-arXiv papers, create a placeholder metadata object
            paper_metadata = {
                "id": None,
                "arxiv_id": None,
                "title": title,
                "authors": [], # We don't track aggregate authors for non-arxiv yet
                "category": "External",
                "published_date": None,
                "url": url
            }
        
        results.append({
            "arxiv_id": arxiv_id,
            "title": title, # Keep raw title for reference
            "count": count,
            "resolved_id": resolved_id,
            "paper": paper_metadata
        })
        
    return results
