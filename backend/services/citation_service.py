"""Citation resolution: links extracted citations to papers in the database.

Extracted from production_worker.py — resolve_citations() and backfill_citation_links().
"""

import logging
import re

from sqlalchemy import or_, func

from models import Paper, CitationLink

logger = logging.getLogger(__name__)

# Regex for ArXiv IDs: YYMM.XXXXX(vN)
# Matches: arXiv:2201.12345, 2201.12345, arxiv.org/abs/2201.12345
ARXIV_ID_PATTERN = re.compile(r'(?:arXiv:)?(\d{2})(\d{2})\.(\d{4,5})(?:v\d+)?')


def resolve_citations(paper: Paper, citations: list, db) -> int:
    """
    Extracts ArXiv IDs from citation text, filters for known papers,
    and links to local database in CitationLink table.
    Updates the paper's citations JSON in place.

    Returns the number of new links added.
    """
    if not citations:
        return 0

    links_added = 0
    updated_citations = []

    for cit in citations:
        raw_text = cit.get('raw', '')
        title = cit.get('title', '')
        url = cit.get('url', '')
        resolved_id = None

        # 1. Try to find ArXiv ID
        match = ARXIV_ID_PATTERN.search(raw_text)

        if match:
            yy = int(match.group(1))
            target_arxiv_id = f"{match.group(1)}{match.group(2)}.{match.group(3)}"

            # Check if target paper exists in our DB
            target_paper = db.query(Paper).filter(
                or_(
                    Paper.arxiv_id == target_arxiv_id,
                    Paper.arxiv_id.like(f"{target_arxiv_id}%")
                )
            ).first()

            if target_paper:
                resolved_id = target_paper.arxiv_id

            # Record in analytics table (deduplicate)
            existing = db.query(CitationLink).filter(
                CitationLink.source_paper_id == paper.id,
                CitationLink.target_arxiv_id == target_arxiv_id
            ).first()

            if not existing:
                new_link = CitationLink(
                    source_paper_id=paper.id,
                    target_arxiv_id=target_arxiv_id,
                    target_title=title,
                    target_url=url,
                    resolved_paper_id=target_paper.id if target_paper else None,
                    is_arxiv=True,
                    published_year=2000 + yy if yy is not None else None
                )
                db.add(new_link)
                links_added += 1
        else:
            # 2. Handle Non-ArXiv Citation
            if title and len(title) > 5:
                existing = db.query(CitationLink).filter(
                    CitationLink.source_paper_id == paper.id,
                    func.lower(CitationLink.target_title) == title.lower()
                ).first()

                if not existing:
                    new_link = CitationLink(
                        source_paper_id=paper.id,
                        target_arxiv_id=None,
                        target_title=title,
                        target_url=url,
                        resolved_paper_id=None,
                        is_arxiv=False,
                        published_year=None
                    )
                    db.add(new_link)
                    links_added += 1

        # Add resolved_id to the citation object for the JSON field
        cit['resolved_id'] = resolved_id
        updated_citations.append(cit)

    # Update the paper's JSON field directly
    paper.citations = updated_citations
    db.commit()

    if links_added > 0:
        logger.info(f"Resolved {links_added} new citation links for paper {paper.arxiv_id}")

    return links_added


def backfill_citation_links(session_factory) -> int:
    """One-time process to fill CitationLink table from existing citations JSON.

    Args:
        session_factory: A callable that returns a new DB session (e.g. SessionLocal).

    Returns:
        Total number of papers processed.
    """
    logger.info("Starting citation links backfill...")
    db = session_factory()
    try:
        papers = db.query(Paper).filter(Paper.citations.is_not(None)).all()
        logger.info(f"Found {len(papers)} papers with citations to backfill.")
        for paper in papers:
            resolve_citations(paper, paper.citations, db)
        return len(papers)
    finally:
        db.close()
    logger.info("Backfill complete.")
