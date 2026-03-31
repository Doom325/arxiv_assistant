"""
Pattern Library API Router
Surfaces pattern classification data from the pattern_experiment_results table.
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, text as sa_text, and_, or_
from typing import Optional
from collections import defaultdict

from database import get_db, SessionLocal
from models import PatternExperimentResult, Paper
from schemas import (
    PatternOverviewResponse, CategoryOverview, PatternCount,
    PaperPatternResponse, PatternDetail,
)
from taxonomy import (
    VALID_CATEGORIES, VALID_PATTERNS, CATEGORY_LABELS, PATTERN_LABELS,
    AGENTIC_CATEGORIES,
)

router = APIRouter(prefix="/patterns", tags=["patterns"])


@router.get("/overview", response_model=PatternOverviewResponse)
def get_pattern_overview(
    is_agentic: Optional[bool] = Query(None, description="Filter to agentic/non-agentic papers only"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """
    Returns the full taxonomy overview with paper counts per category and per pattern.
    Excludes results with taxonomy violations or errors (quality gate).
    """
    # Base query: clean results only
    base_filters = [
        PatternExperimentResult.error.is_(None),
        or_(
            PatternExperimentResult.num_violations == 0,
            PatternExperimentResult.num_violations.is_(None),
        ),
        PatternExperimentResult.primary_category.isnot(None),
    ]

    if is_agentic is not None:
        base_filters.append(PatternExperimentResult.is_agentic == is_agentic)

    # Date filtering requires joining with papers table
    if start_date or end_date:
        query = db.query(PatternExperimentResult).join(
            Paper, Paper.arxiv_id == PatternExperimentResult.arxiv_id
        )
        if start_date:
            query = query.filter(Paper.published_date >= start_date)
        if end_date:
            query = query.filter(Paper.published_date <= end_date)
    else:
        query = db.query(PatternExperimentResult)

    results = query.filter(*base_filters).all()

    # Aggregate counts
    total_classified = len(results)
    total_agentic = sum(1 for r in results if r.is_agentic)

    # Count by category and by pattern (using the patterns JSON column)
    category_counts = defaultdict(int)
    pattern_counts = defaultdict(lambda: defaultdict(int))

    for r in results:
        if r.primary_category:
            category_counts[r.primary_category] += 1
        if r.patterns:
            for p in r.patterns:
                cat = p.get("category", "")
                name = p.get("name", "")
                if cat in VALID_CATEGORIES and name in VALID_PATTERNS.get(cat, set()):
                    pattern_counts[cat][name] += 1

    # Build response
    categories = []
    for cat in sorted(VALID_CATEGORIES):
        cat_patterns = []
        for pat_name in sorted(VALID_PATTERNS.get(cat, set())):
            count = pattern_counts.get(cat, {}).get(pat_name, 0)
            cat_patterns.append(PatternCount(
                name=pat_name,
                label=PATTERN_LABELS.get(pat_name, pat_name),
                paper_count=count,
            ))

        categories.append(CategoryOverview(
            category=cat,
            label=CATEGORY_LABELS.get(cat, cat),
            paper_count=category_counts.get(cat, 0),
            is_agentic_category=cat in AGENTIC_CATEGORIES,
            patterns=cat_patterns,
        ))

    # Sort: agentic categories first, then by paper count desc
    categories.sort(key=lambda c: (not c.is_agentic_category, -c.paper_count))

    return PatternOverviewResponse(
        total_classified=total_classified,
        total_agentic=total_agentic,
        categories=categories,
    )


@router.get("/papers", response_model=list[PaperPatternResponse])
def get_pattern_papers(
    category: Optional[str] = Query(None, description="Filter by primary category (e.g., agent_planning)"),
    pattern: Optional[str] = Query(None, description="Filter by specific pattern name (e.g., tree_search)"),
    is_agentic: Optional[bool] = Query(None, description="Filter to agentic/non-agentic papers only"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """
    Returns paginated papers matching category/pattern filters.
    Excludes results with violations or errors.
    """
    # Base query with quality gate
    query = db.query(PatternExperimentResult).join(
        Paper, Paper.arxiv_id == PatternExperimentResult.arxiv_id
    ).filter(
        PatternExperimentResult.error.is_(None),
        or_(
            PatternExperimentResult.num_violations == 0,
            PatternExperimentResult.num_violations.is_(None),
        ),
    )

    # Apply filters
    if category:
        query = query.filter(PatternExperimentResult.primary_category == category)

    if is_agentic is not None:
        query = query.filter(PatternExperimentResult.is_agentic == is_agentic)

    if start_date:
        query = query.filter(Paper.published_date >= start_date)
    if end_date:
        query = query.filter(Paper.published_date <= end_date)

    # Pattern-level filtering using JSON contains (PostgreSQL jsonb)
    if pattern:
        # Use raw SQL for jsonb containment: patterns::jsonb @> '[{"name": "tree_search"}]'
        query = query.filter(
            sa_text("pattern_experiment_results.patterns::jsonb @> :pattern_json")
        ).params(pattern_json=f'[{{"name": "{pattern}"}}]')

    # Order by published date (newest first), paginate
    query = query.order_by(Paper.published_date.desc())

    # Fetch both PatternExperimentResult and Paper in one query to avoid N+1
    combined_query = query.add_entity(Paper).offset(skip).limit(limit).all()

    # Build response
    papers = []
    for row in combined_query:
        r = row[0]  # PatternExperimentResult
        paper = row[1]  # Paper

        patterns = []
        if r.patterns:
            for p in r.patterns:
                patterns.append(PatternDetail(
                    category=p.get("category", ""),
                    name=p.get("name", ""),
                    confidence=p.get("confidence", 0.0),
                    evidence=p.get("evidence"),
                ))

        papers.append(PaperPatternResponse(
            arxiv_id=r.arxiv_id,
            title=r.paper_title or (paper.title if paper else "Unknown"),
            published_date=paper.published_date if paper else None,
            category=paper.category if paper else None,
            is_agentic=r.is_agentic,
            primary_pattern_category=r.primary_category,
            patterns=patterns,
            reasoning=r.reasoning,
        ))

    return papers


@router.get("/paper/{arxiv_id}", response_model=PaperPatternResponse)
def get_paper_patterns(
    arxiv_id: str,
    db: Session = Depends(get_db),
):
    """
    Returns pattern classification for a specific paper.
    Returns the most recent clean classification result.
    """
    result = db.query(PatternExperimentResult).filter(
        PatternExperimentResult.arxiv_id == arxiv_id,
        PatternExperimentResult.error.is_(None),
    ).order_by(PatternExperimentResult.created_at.desc()).first()

    if not result:
        raise HTTPException(status_code=404, detail="No pattern classification found for this paper")

    paper = db.query(Paper).filter(Paper.arxiv_id == arxiv_id).first()

    patterns = []
    if result.patterns:
        for p in result.patterns:
            patterns.append(PatternDetail(
                category=p.get("category", ""),
                name=p.get("name", ""),
                confidence=p.get("confidence", 0.0),
                evidence=p.get("evidence"),
            ))

    return PaperPatternResponse(
        arxiv_id=result.arxiv_id,
        title=result.paper_title or (paper.title if paper else "Unknown"),
        published_date=paper.published_date if paper else None,
        category=paper.category if paper else None,
        is_agentic=result.is_agentic,
        primary_pattern_category=result.primary_category,
        patterns=patterns,
        reasoning=result.reasoning,
    )
