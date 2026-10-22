"""Search and chat endpoints, extracted from papers.py."""

import logging
import re
from datetime import date
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, Text, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from models import Paper, PaperEmbedding
from schemas import PaperResponse
from services.llm_service import llm_service
from services.query_embedding_cache import query_cache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/papers", tags=["search"])


def parse_query(query: str) -> Tuple[str, Dict[str, Optional[str]]]:
    """Parses search query for metadata operators like category:, after:, before:, author:."""
    filters: Dict[str, Optional[str]] = {
        'category': None,
        'after': None,
        'before': None,
        'author': None,
        'entity': None,
        'arxiv_id': None
    }

    # Extract category:val
    cat_match = re.search(r'category:([^\s]+)', query)
    if cat_match:
        filters['category'] = cat_match.group(1)
        query = query.replace(cat_match.group(0), '')

    # Extract after:YYYY-MM-DD or YYYY
    after_match = re.search(r'after:(\d{4}-\d{2}-\d{2}|\d{4})', query)
    if after_match:
        val = after_match.group(1)
        filters['after'] = val if '-' in val else f"{val}-01-01"
        query = query.replace(after_match.group(0), '')

    # Extract before:YYYY-MM-DD or YYYY
    before_match = re.search(r'before:(\d{4}-\d{2}-\d{2}|\d{4})', query)
    if before_match:
        val = before_match.group(1)
        filters['before'] = val if '-' in val else f"{val}-12-31"
        query = query.replace(before_match.group(0), '')

    # Extract author:val (single word for now)
    author_match = re.search(r'author:([^\s]+)', query)
    if author_match:
        filters['author'] = author_match.group(1)
        query = query.replace(author_match.group(0), '')

    # Extract entity:val
    entity_match = re.search(r'entity:([^\s]+)', query)
    if entity_match:
        filters['entity'] = entity_match.group(1)
        query = query.replace(entity_match.group(0), '')

    # Extract arxiv_id
    arxiv_match = re.search(r'(?i)(?:arxiv:)?\s*(\d{4}\.\d{4,5}(?:v\d+)?|[a-z\-]+/\d{7}(?:v\d+)?)', query)
    if arxiv_match:
        extracted_id = arxiv_match.group(1)
        base_id = re.sub(r'(?i)v\d+$', '', extracted_id)
        filters['arxiv_id'] = base_id
        query = query.replace(arxiv_match.group(0), '')

    return query.strip(), filters


def _reset_statement_timeout(db: Session, is_postgres: bool) -> None:
    """Resets local statement_timeout on Postgres sessions."""
    if not is_postgres:
        return
    try:
        db.execute(text("RESET statement_timeout;"))
    except Exception:
        pass


def _lookup_exact_arxiv_match(
    arxiv_id: str, is_postgres: bool, db: Session
) -> Optional[Paper]:
    """Looks up an exact arXiv ID match with a short statement timeout."""
    try:
        if is_postgres:
            db.execute(text("SET LOCAL statement_timeout = 50;"))
        possible_ids = [arxiv_id] + [f"{arxiv_id}v{i}" for i in range(1, 10)]
        exact_match_row = (
            db.query(Paper, PaperEmbedding)
            .outerjoin(PaperEmbedding, Paper.id == PaperEmbedding.paper_id)
            .filter(Paper.arxiv_id.in_(possible_ids))
            .order_by(Paper.arxiv_id.desc())
            .first()
        )
        if exact_match_row:
            logger.info(f"event=search_exact_match arxiv_id={arxiv_id}")
            return exact_match_row[0]
        return None
    except OperationalError as e:
        logger.error(f"event=search_db_timeout error={str(e)}")
        raise HTTPException(status_code=503, detail="Search database timeout")
    finally:
        _reset_statement_timeout(db, is_postgres)


def _has_paper_filters(
    metadata_filters: Dict[str, Optional[str]],
    category: Optional[str],
    start_date: Optional[date],
    end_date: Optional[date],
) -> bool:
    """Returns True if any metadata or explicit Paper filter is active."""
    filter_keys = ("category", "after", "before", "author", "entity")
    return bool(
        category
        or start_date
        or end_date
        or any(metadata_filters.get(k) for k in filter_keys)
    )


def _apply_paper_filters(
    query_obj: Any,
    metadata_filters: Dict[str, Optional[str]],
    category: Optional[str],
    start_date: Optional[date],
    end_date: Optional[date],
) -> Any:
    """Applies parsed metadata filters and explicit query param filters to a Paper query."""
    if metadata_filters["category"]:
        query_obj = query_obj.filter(Paper.category == metadata_filters["category"])
    if metadata_filters["after"]:
        query_obj = query_obj.filter(Paper.published_date >= metadata_filters["after"])
    if metadata_filters["before"]:
        query_obj = query_obj.filter(Paper.published_date <= metadata_filters["before"])
    if metadata_filters["author"]:
        query_obj = query_obj.filter(
            Paper.authors.cast(Text).ilike(f"%{metadata_filters['author']}%")
        )
    if metadata_filters["entity"]:
        query_obj = query_obj.filter(
            Paper.entities.cast(Text).ilike(f"%{metadata_filters['entity']}%")
        )
    if category:
        query_obj = query_obj.filter(Paper.category.ilike(f"{category}%"))
    if start_date:
        query_obj = query_obj.filter(Paper.published_date >= start_date)
    if end_date:
        query_obj = query_obj.filter(Paper.published_date <= end_date)
    return query_obj


def _fetch_semantic_ids(
    clean_query: str,
    pool_size: int,
    metadata_filters: Dict[str, Optional[str]],
    category: Optional[str],
    start_date: Optional[date],
    end_date: Optional[date],
    db: Session,
) -> List[int]:
    """Fetches candidate paper IDs ordered by vector distance without hydrating full rows."""
    if not clean_query:
        return []
    try:
        query_embedding = query_cache.get_or_generate(
            clean_query, task_type="retrieval_query", db=db
        )
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        return []
    if not query_embedding:
        return []

    semantic_query = db.query(PaperEmbedding.paper_id).join(
        Paper, Paper.id == PaperEmbedding.paper_id
    )
    semantic_query = _apply_paper_filters(
        semantic_query, metadata_filters, category, start_date, end_date
    )
    rows = (
        semantic_query.order_by(PaperEmbedding.embedding.l2_distance(query_embedding))
        .limit(pool_size)
        .all()
    )
    return [row[0] for row in rows]


def _fetch_keyword_ids(
    clean_query: str,
    pool_size: int,
    is_postgres: bool,
    metadata_filters: Dict[str, Optional[str]],
    category: Optional[str],
    start_date: Optional[date],
    end_date: Optional[date],
    db: Session,
) -> List[int]:
    """Fetches candidate paper IDs from full-text or filter-only search."""
    keyword_query = _apply_paper_filters(
        db.query(Paper.id), metadata_filters, category, start_date, end_date
    )
    if not clean_query:
        rows = keyword_query.order_by(Paper.published_date.desc()).limit(pool_size).all()
        return [row[0] for row in rows]
    if is_postgres:
        ts_query = func.plainto_tsquery("english", clean_query)
        rows = (
            keyword_query.filter(Paper.search_vector.op("@@")(ts_query))
            .order_by(func.ts_rank_cd(Paper.search_vector, ts_query).desc())
            .limit(pool_size)
            .all()
        )
        return [row[0] for row in rows]

    rows = (
        keyword_query.filter(
            Paper.title.ilike(f"%{clean_query}%")
            | Paper.summary.ilike(f"%{clean_query}%")
        )
        .limit(pool_size)
        .all()
    )
    return [row[0] for row in rows]


def _compute_rrf_scores(
    semantic_ids: List[int],
    keyword_ids: List[int],
    exact_match_paper: Optional[Paper],
) -> Dict[int, float]:
    """Combines semantic and keyword candidate lists via Reciprocal Rank Fusion."""
    k = 60
    rrf_scores: Dict[int, float] = {}
    for i, pid in enumerate(semantic_ids):
        rrf_scores[pid] = rrf_scores.get(pid, 0.0) + 1.0 / (k + i + 1)
    for i, pid in enumerate(keyword_ids):
        rrf_scores[pid] = rrf_scores.get(pid, 0.0) + 1.0 / (k + i + 1)
    if exact_match_paper:
        rrf_scores[exact_match_paper.id] = float("inf")
    return rrf_scores


def _rank_and_paginate_papers(
    rrf_scores: Dict[int, float],
    exact_match_paper: Optional[Paper],
    sort_by: str,
    skip: int,
    limit: int,
    db: Session,
) -> List[Paper]:
    """Hydrates full Paper ORM objects only for the requested page."""
    sorted_ids = sorted(
        rrf_scores.keys(), key=lambda pid: rrf_scores[pid], reverse=True
    )
    if sort_by == "relevance":
        top_ids = sorted_ids[skip : skip + limit]
        if not top_ids:
            return []
        papers = db.query(Paper).filter(Paper.id.in_(top_ids)).all()
        paper_map = {p.id: p for p in papers}
        return [paper_map[pid] for pid in top_ids if pid in paper_map]

    candidate_ids = [
        pid for pid in sorted_ids if not exact_match_paper or pid != exact_match_paper.id
    ]
    if not candidate_ids and not exact_match_paper:
        return []

    all_papers = (
        db.query(Paper).filter(Paper.id.in_(candidate_ids)).all()
        if candidate_ids
        else []
    )
    if sort_by in ("date", "newest"):
        all_papers.sort(key=lambda p: p.published_date or date.min, reverse=True)
    elif sort_by == "title":
        all_papers.sort(key=lambda p: (p.title or "").lower())

    if exact_match_paper:
        all_papers.insert(0, exact_match_paper)
    return all_papers[skip : skip + limit]


@router.post("/search", response_model=List[PaperResponse])
def search_papers(
    query: str,
    skip: int = 0,
    limit: int = 100,
    sort_by: str = "relevance",
    category: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
) -> List[Paper]:
    is_postgres = "sqlite" not in settings.DATABASE_URL
    clean_query, metadata_filters = parse_query(query)

    exact_match_paper = None
    if metadata_filters.get("arxiv_id"):
        exact_match_paper = _lookup_exact_arxiv_match(
            metadata_filters["arxiv_id"], is_postgres, db
        )
        if not clean_query:
            return [exact_match_paper] if exact_match_paper else []

    if not clean_query and not _has_paper_filters(
        metadata_filters, category, start_date, end_date
    ):
        return []

    pool_size = min(max(skip + min(limit, 200) * 5, 250), 1000)
    semantic_ids = _fetch_semantic_ids(
        clean_query, pool_size, metadata_filters, category, start_date, end_date, db
    )
    keyword_ids = _fetch_keyword_ids(
        clean_query,
        pool_size,
        is_postgres,
        metadata_filters,
        category,
        start_date,
        end_date,
        db,
    )
    rrf_scores = _compute_rrf_scores(semantic_ids, keyword_ids, exact_match_paper)
    return _rank_and_paginate_papers(
        rrf_scores, exact_match_paper, sort_by, skip, limit, db
    )


@router.post("/chat")
def chat_with_papers(query: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    # 1. Search relevant papers using the new PaperEmbedding table
    query_embedding = query_cache.get_or_generate(
        query, task_type="retrieval_query", db=db,
    )

    # Join with Paper to get the source content
    results = db.query(Paper).join(PaperEmbedding).order_by(
        PaperEmbedding.embedding.l2_distance(query_embedding)
    ).limit(3).all()

    # 2. Construct context
    context = ""
    for paper in results:
        context += f"Title: {paper.title}\nSummary: {paper.summary}\n\n"

    # 3. Chat with Gemini
    response = llm_service.chat([], query, context)

    return {"response": response, "sources": [p.title for p in results]}
