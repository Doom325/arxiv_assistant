"""Search and chat endpoints, extracted from papers.py."""

import logging
import re
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy import func, Text
from sqlalchemy.orm import Session

from database import get_db
from models import Paper, PaperEmbedding
from schemas import PaperResponse
from services.llm_service import llm_service
from services.query_embedding_cache import query_cache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/papers", tags=["search"])


def parse_query(query: str):
    """Parses search query for metadata operators like category:, after:, before:, author:."""
    filters = {
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
    arxiv_match = re.search(r'(?i)(?:arxiv:)?\s*\b(\d{4}\.\d{4,5}|[a-z\-]+/\d{7})\b', query)
    if arxiv_match:
        filters['arxiv_id'] = arxiv_match.group(1)
        query = query.replace(arxiv_match.group(0), '')

    return query.strip(), filters


@router.post("/search", response_model=List[PaperResponse])
def search_papers(
    query: str,
    skip: int = 0,
    limit: int = 10000,
    sort_by: str = "relevance",
    category: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    # 1. Parse query for filters
    clean_query, metadata_filters = parse_query(query)

    # 2. Generate embedding with correct task type (cached)
    try:
        query_embedding = query_cache.get_or_generate(
            clean_query, task_type="retrieval_query", db=db,
        )
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        query_embedding = None

    # 3. Semantic Search: Query PaperEmbedding table
    semantic_query = db.query(PaperEmbedding, Paper).join(Paper)

    # Apply Filters (on Paper fields)
    # 1. Filters from metadata parsing (query string)
    if metadata_filters['category']:
        semantic_query = semantic_query.filter(Paper.category == metadata_filters['category'])
    if metadata_filters['after']:
        semantic_query = semantic_query.filter(Paper.published_date >= metadata_filters['after'])
    if metadata_filters['before']:
        semantic_query = semantic_query.filter(Paper.published_date <= metadata_filters['before'])
    if metadata_filters['author']:
        semantic_query = semantic_query.filter(Paper.authors.cast(Text).ilike(f"%{metadata_filters['author']}%"))
    if metadata_filters['entity']:
        semantic_query = semantic_query.filter(Paper.entities.cast(Text).ilike(f"%{metadata_filters['entity']}%"))
    if metadata_filters['arxiv_id']:
        semantic_query = semantic_query.filter(Paper.arxiv_id == metadata_filters['arxiv_id'])

    # 2. Filters from explicit query params (UI dropdowns/date pickers)
    if category:
        logger.info(f"Filtering by category: {category}")
        semantic_query = semantic_query.filter(Paper.category.ilike(f"{category}%"))
    if start_date:
        semantic_query = semantic_query.filter(Paper.published_date >= start_date)
    if end_date:
        semantic_query = semantic_query.filter(Paper.published_date <= end_date)

    # Order by Distance and Limit (Larger pool for RRF pagination)
    POOL_SIZE = 10000
    if query_embedding:
        semantic_results_raw = semantic_query.order_by(
            PaperEmbedding.embedding.l2_distance(query_embedding)
        ).limit(POOL_SIZE).all()
        semantic_papers = [p for _, p in semantic_results_raw]
    else:
        semantic_papers = []

    # 4. Full-Text Search (Keyword fallback)
    keyword_query = db.query(Paper)

    if metadata_filters['category']:
        keyword_query = keyword_query.filter(Paper.category == metadata_filters['category'])
    if metadata_filters['after']:
        keyword_query = keyword_query.filter(Paper.published_date >= metadata_filters['after'])
    if metadata_filters['before']:
        keyword_query = keyword_query.filter(Paper.published_date <= metadata_filters['before'])
    if metadata_filters['author']:
        keyword_query = keyword_query.filter(Paper.authors.cast(Text).ilike(f"%{metadata_filters['author']}%"))
    if metadata_filters['entity']:
        keyword_query = keyword_query.filter(Paper.entities.cast(Text).ilike(f"%{metadata_filters['entity']}%"))
    if metadata_filters['arxiv_id']:
        keyword_query = keyword_query.filter(Paper.arxiv_id == metadata_filters['arxiv_id'])

    # Explicit Params
    if category:
        keyword_query = keyword_query.filter(Paper.category.ilike(f"{category}%"))
    if start_date:
        keyword_query = keyword_query.filter(Paper.published_date >= start_date)
    if end_date:
        keyword_query = keyword_query.filter(Paper.published_date <= end_date)

    from config import settings
    if "sqlite" in settings.DATABASE_URL:
        if clean_query:
            keyword_results = keyword_query.filter(Paper.title.ilike(f"%{clean_query}%")).limit(POOL_SIZE).all()
        else:
            keyword_results = keyword_query.limit(POOL_SIZE).all()
    else:
        if clean_query:
            keyword_results = keyword_query.filter(
                Paper.search_vector.op('@@')(func.plainto_tsquery('english', clean_query))
            ).order_by(
                func.ts_rank_cd(Paper.search_vector, func.plainto_tsquery('english', clean_query)).desc()
            ).limit(POOL_SIZE).all()
        else:
            keyword_results = keyword_query.limit(POOL_SIZE).all()

    # 5. Reciprocal Rank Fusion (RRF)
    k = 60
    rrf_scores = {}

    for i, p in enumerate(semantic_papers):
        rrf_scores[p.id] = rrf_scores.get(p.id, 0) + 1.0 / (k + i + 1)

    for i, p in enumerate(keyword_results):
        rrf_scores[p.id] = rrf_scores.get(p.id, 0) + 1.0 / (k + i + 1)

    # 6. Final Ranking and Pagination
    if sort_by == "relevance":
        sorted_ids = sorted(rrf_scores.keys(), key=lambda pid: rrf_scores[pid], reverse=True)
        top_ids = sorted_ids[skip : skip + limit]

        if not top_ids:
            return []

        papers = db.query(Paper).filter(Paper.id.in_(top_ids)).all()
        paper_map = {p.id: p for p in papers}
        return [paper_map[pid] for pid in top_ids if pid in paper_map]

    else:
        top_ids = list(rrf_scores.keys())
        if not top_ids:
            return []

        all_papers = db.query(Paper).filter(Paper.id.in_(top_ids)).all()

        if sort_by == "date":
            all_papers.sort(key=lambda p: p.published_date, reverse=True)
        elif sort_by == "title":
            all_papers.sort(key=lambda p: (p.title or "").lower())

        return all_papers[skip : skip + limit]


@router.post("/chat")
def chat_with_papers(query: str, db: Session = Depends(get_db)):
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
