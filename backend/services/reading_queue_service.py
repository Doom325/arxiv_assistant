"""Reading queue service — discovery scoring and queue management."""

import logging
import math
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
from sqlalchemy import func, nullslast
from sqlalchemy.orm import Session

from models import Paper, ReadingQueue, UserInterestProfile, UserLibrary

logger = logging.getLogger(__name__)

# ── Scoring weights ──────────────────────────────────

# Bookmark rescoring (existing papers the user saved)
WEIGHT_INTEREST = 0.35
WEIGHT_FRESHNESS = 0.15

# Discovery scoring (surfacing new papers)
DISC_WEIGHT_INTEREST = 0.50
DISC_WEIGHT_BEST_MATCH = 0.35
DISC_WEIGHT_FRESHNESS = 0.15

# Discovery similarity threshold — papers below this are skipped
DISCOVERY_THRESHOLD = 0.80

# Freshness decay constant (days)
FRESHNESS_DECAY = 0.03

# Interest vector half-life (days)
INTEREST_HALF_LIFE = 30

# Minimum engaged papers before discovery activates
MIN_ENGAGED_FOR_DISCOVERY = 3

# Hardcoded user for now (matches library.py)
USER_ID = 1


# ── Utilities ─────────────────────────────────────────


def _cosine_similarity(
    vec_a: list[float],
    vec_b: list[float],
) -> float:
    """Cosine similarity between two vectors."""
    a = np.array(vec_a, dtype=np.float64)
    b = np.array(vec_b, dtype=np.float64)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def _to_embedding_list(raw_embedding: object) -> Optional[list[float]]:
    """Safely convert a pgvector/numpy embedding to a plain list."""
    if raw_embedding is None:
        return None
    if isinstance(raw_embedding, np.ndarray):
        emb = raw_embedding.tolist()
    elif not isinstance(raw_embedding, list):
        emb = list(raw_embedding)
    else:
        emb = raw_embedding
    if len(emb) != 768:
        return None
    return emb


def _get_paper_embedding(paper: Paper) -> Optional[list[float]]:
    """Get best available 768D embedding for a paper.

    Falls back: embedding → abstract_embedding.
    """
    emb = _to_embedding_list(paper.embedding)
    if emb is not None:
        return emb
    return _to_embedding_list(paper.abstract_embedding)


def _to_datetime(val: object) -> Optional[datetime]:
    """Coerce date/datetime to datetime."""
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    return datetime(val.year, val.month, val.day)


def _freshness_score(published_date: object) -> float:
    """Exponential freshness decay from published date."""
    pub_dt = _to_datetime(published_date)
    if pub_dt is None:
        return 0.0
    days_since = max((datetime.utcnow() - pub_dt).days, 0)
    return math.exp(-FRESHNESS_DECAY * days_since)


# ── Interest vector ───────────────────────────────────


def compute_user_interest_vector(
    db: Session,
    user_id: int = USER_ID,
) -> Optional[list[float]]:
    """Build a time-decayed average embedding from engaged papers.

    Engaged = bookmarked OR has a generated_summary.
    Returns None on cold start (no papers with embeddings).
    """
    library_paper_ids = (
        db.query(UserLibrary.paper_id)
        .filter(
            UserLibrary.user_id == user_id,
            UserLibrary.paper_id.isnot(None),
        )
        .subquery()
    )

    papers = (
        db.query(Paper)
        .filter(
            (Paper.id.in_(library_paper_ids))
            | (Paper.generated_summary.isnot(None))
        )
        .filter(
            (Paper.embedding.isnot(None))
            | (Paper.abstract_embedding.isnot(None))
        )
        .all()
    )

    if not papers:
        return None

    now = datetime.utcnow()
    weighted_sum = np.zeros(768, dtype=np.float64)
    total_weight = 0.0

    for paper in papers:
        emb = _get_paper_embedding(paper)
        if emb is None:
            continue

        pub_dt = _to_datetime(paper.published_date)
        days_old = max((now - pub_dt).days if pub_dt else 0, 0)
        decay = math.exp(-math.log(2) * days_old / INTEREST_HALF_LIFE)

        weighted_sum += np.array(emb, dtype=np.float64) * decay
        total_weight += decay

    if total_weight == 0:
        return None

    return (weighted_sum / total_weight).tolist()


def _get_engaged_embeddings(
    db: Session,
    user_id: int = USER_ID,
) -> list[tuple[int, list[float]]]:
    """Return (paper_id, embedding) for all engaged papers."""
    library_paper_ids = (
        db.query(UserLibrary.paper_id)
        .filter(
            UserLibrary.user_id == user_id,
            UserLibrary.paper_id.isnot(None),
        )
        .subquery()
    )

    papers = (
        db.query(Paper)
        .filter(
            (Paper.id.in_(library_paper_ids))
            | (Paper.generated_summary.isnot(None))
        )
        .filter(
            (Paper.embedding.isnot(None))
            | (Paper.abstract_embedding.isnot(None))
        )
        .all()
    )

    results = []
    for paper in papers:
        emb = _get_paper_embedding(paper)
        if emb is not None:
            results.append((paper.id, emb))
    return results


# ── Scoring ───────────────────────────────────────────


def score_paper(
    paper: Paper,
    interest_vector: Optional[list[float]],
) -> dict:
    """Score a paper for bookmark queue (interest + freshness).

    Returns dict with individual scores and combined priority_score.
    """
    interest_sim = 0.0
    emb = _get_paper_embedding(paper)
    if interest_vector is not None and emb is not None:
        interest_sim = max(
            0.0, _cosine_similarity(emb, interest_vector)
        )

    freshness = _freshness_score(paper.published_date)

    max_possible = WEIGHT_INTEREST + WEIGHT_FRESHNESS
    raw = WEIGHT_INTEREST * interest_sim + WEIGHT_FRESHNESS * freshness
    priority_score = min(raw / max_possible, 1.0)

    return {
        "priority_score": priority_score,
        "interest_similarity": interest_sim,
        "freshness_score": freshness,
        "citation_impact": 0.0,
        "category_score": 0.0,
        "entity_overlap": 0.0,
        "peer_reads_score": 0.0,
    }


def _score_paper_for_discovery(
    paper_id: int,
    paper_emb: list[float],
    published_date: object,
    interest_vector: list[float],
    engaged_embeddings: list[tuple[int, list[float]]],
) -> tuple[float, float, float, int, float]:
    """Score a candidate paper for discovery.

    Returns (priority_score, interest_sim, freshness,
             best_match_id, best_match_score).
    """
    interest_sim = max(
        0.0, _cosine_similarity(paper_emb, interest_vector)
    )

    best_match_id = 0
    best_match_score = 0.0
    for eng_id, eng_emb in engaged_embeddings:
        if eng_id == paper_id:
            continue  # skip self-match
        sim = _cosine_similarity(paper_emb, eng_emb)
        if sim > best_match_score:
            best_match_score = sim
            best_match_id = eng_id

    freshness = _freshness_score(published_date)

    raw = (
        DISC_WEIGHT_INTEREST * interest_sim
        + DISC_WEIGHT_BEST_MATCH * best_match_score
        + DISC_WEIGHT_FRESHNESS * freshness
    )
    priority_score = min(raw, 1.0)

    return (
        priority_score,
        interest_sim,
        freshness,
        best_match_id,
        best_match_score,
    )


# ── Discovery pipeline ────────────────────────────────


def run_discovery(
    db: Session,
    user_id: int = USER_ID,
    since_days: int = 7,
) -> int:
    """Find relevant papers from recent ingestion and add to queue.

    Scans papers published in the last `since_days` that have
    embeddings, are not already in the queue, and scores them
    against the user's interest profile + individual engaged
    paper similarity.

    Returns count of papers added.
    """
    interest_vector = compute_user_interest_vector(db, user_id)
    if interest_vector is None:
        logger.info("Discovery: cold start, no interest vector")
        return 0

    engaged = _get_engaged_embeddings(db, user_id)
    if len(engaged) < MIN_ENGAGED_FOR_DISCOVERY:
        logger.info(
            "Discovery: only %d engaged papers, need %d",
            len(engaged),
            MIN_ENGAGED_FOR_DISCOVERY,
        )
        return 0

    # IDs already in queue for this user
    existing_ids = set(
        pid
        for (pid,) in db.query(ReadingQueue.paper_id)
        .filter(ReadingQueue.user_id == user_id)
        .all()
    )

    # Candidate papers: recent, have embedding, not in queue
    cutoff = datetime.utcnow() - timedelta(days=since_days)
    candidates = (
        db.query(Paper)
        .filter(
            (Paper.embedding.isnot(None))
            | (Paper.abstract_embedding.isnot(None)),
            Paper.published_date >= cutoff,
        )
        .all()
    )

    now = datetime.utcnow()
    added = 0
    batch: list[ReadingQueue] = []

    for paper in candidates:
        if paper.id in existing_ids:
            continue

        emb = _get_paper_embedding(paper)
        if emb is None:
            continue

        (
            priority_score,
            interest_sim,
            freshness,
            best_match_id,
            best_match_score,
        ) = _score_paper_for_discovery(
            paper.id, emb, paper.published_date, interest_vector, engaged
        )

        if priority_score < DISCOVERY_THRESHOLD:
            continue

        entry = ReadingQueue(
            user_id=user_id,
            paper_id=paper.id,
            read_status="unread",
            source="discovery",
            priority_score=priority_score,
            interest_similarity=interest_sim,
            freshness_score=freshness,
            best_match_paper_id=best_match_id if best_match_id else None,
            best_match_score=best_match_score,
            scored_at=now,
        )
        batch.append(entry)
        existing_ids.add(paper.id)
        added += 1

    if batch:
        db.bulk_save_objects(batch)
        db.commit()

    logger.info(
        "Discovery: scanned %d candidates, added %d (threshold=%.2f)",
        len(candidates),
        added,
        DISCOVERY_THRESHOLD,
    )
    return added


# ── Library sync ──────────────────────────────────────


def sync_queue_from_library(
    db: Session,
    user_id: int = USER_ID,
) -> tuple[int, int]:
    """Sync reading queue with library bookmarks.

    Returns (added_count, removed_count).
    Only touches source='bookmark' entries.
    """
    library_ids = set(
        pid
        for (pid,) in db.query(UserLibrary.paper_id)
        .filter(
            UserLibrary.user_id == user_id,
            UserLibrary.paper_id.isnot(None),
        )
        .distinct()
        .all()
    )

    bookmark_queue_ids = set(
        pid
        for (pid,) in db.query(ReadingQueue.paper_id)
        .filter(
            ReadingQueue.user_id == user_id,
            ReadingQueue.source == "bookmark",
        )
        .all()
    )

    to_add = library_ids - bookmark_queue_ids
    added = 0
    for paper_id in to_add:
        # If already in queue as discovery, upgrade to bookmark
        existing = (
            db.query(ReadingQueue)
            .filter(
                ReadingQueue.user_id == user_id,
                ReadingQueue.paper_id == paper_id,
            )
            .first()
        )
        if existing:
            existing.source = "bookmark"
        else:
            db.add(
                ReadingQueue(
                    user_id=user_id,
                    paper_id=paper_id,
                    read_status="unread",
                    source="bookmark",
                )
            )
        added += 1

    to_remove = bookmark_queue_ids - library_ids
    removed = 0
    if to_remove:
        removed = (
            db.query(ReadingQueue)
            .filter(
                ReadingQueue.user_id == user_id,
                ReadingQueue.source == "bookmark",
                ReadingQueue.paper_id.in_(to_remove),
            )
            .delete(synchronize_session="fetch")
        )

    db.commit()
    return added, removed


# ── Rescore ───────────────────────────────────────────


def rescore_queue(
    db: Session,
    user_id: int = USER_ID,
) -> int:
    """Recompute priority scores for all unread/reading entries.

    Returns count of papers rescored.
    """
    interest_vector = compute_user_interest_vector(db, user_id)

    # Cache interest profile
    profile = (
        db.query(UserInterestProfile)
        .filter(UserInterestProfile.user_id == user_id)
        .first()
    )
    if interest_vector:
        if profile:
            profile.interest_vector = interest_vector
            profile.computed_at = datetime.utcnow()
        else:
            profile = UserInterestProfile(
                user_id=user_id,
                interest_vector=interest_vector,
                computed_at=datetime.utcnow(),
            )
            db.add(profile)

    entries = (
        db.query(ReadingQueue)
        .filter(
            ReadingQueue.user_id == user_id,
            ReadingQueue.read_status.in_(["unread", "reading"]),
        )
        .all()
    )

    paper_ids = [e.paper_id for e in entries]
    if not paper_ids:
        db.commit()
        return 0

    papers_map = {
        p.id: p
        for p in db.query(Paper).filter(Paper.id.in_(paper_ids)).all()
    }

    # For discovery rescoring, we also need engaged embeddings
    engaged = (
        _get_engaged_embeddings(db, user_id)
        if interest_vector
        else []
    )

    now = datetime.utcnow()
    count = 0
    for entry in entries:
        paper = papers_map.get(entry.paper_id)
        if not paper:
            continue

        if entry.source == "discovery" and interest_vector and engaged:
            emb = _get_paper_embedding(paper)
            if emb:
                (
                    score,
                    isim,
                    fresh,
                    bmid,
                    bmscore,
                ) = _score_paper_for_discovery(
                    paper.id,
                    emb,
                    paper.published_date,
                    interest_vector,
                    engaged,
                )
                entry.priority_score = score
                entry.interest_similarity = isim
                entry.freshness_score = fresh
                entry.best_match_paper_id = bmid if bmid else None
                entry.best_match_score = bmscore
            else:
                scores = score_paper(paper, interest_vector)
                entry.priority_score = scores["priority_score"]
                entry.interest_similarity = scores["interest_similarity"]
                entry.freshness_score = scores["freshness_score"]
        else:
            scores = score_paper(paper, interest_vector)
            entry.priority_score = scores["priority_score"]
            entry.interest_similarity = scores["interest_similarity"]
            entry.freshness_score = scores["freshness_score"]
            entry.citation_impact = scores["citation_impact"]
            entry.category_score = scores["category_score"]
            entry.entity_overlap = scores["entity_overlap"]
            entry.peer_reads_score = scores["peer_reads_score"]

        entry.scored_at = now
        count += 1

    if profile and interest_vector:
        profile.papers_used = len(papers_map)

    db.commit()
    return count


# ── Queue reads ───────────────────────────────────────


def get_queue(
    db: Session,
    user_id: int = USER_ID,
    status: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    """Fetch the prioritized reading queue with paper metadata."""
    query = (
        db.query(ReadingQueue, Paper)
        .join(Paper, ReadingQueue.paper_id == Paper.id)
        .filter(ReadingQueue.user_id == user_id)
    )

    if status:
        query = query.filter(ReadingQueue.read_status == status)
    if source:
        query = query.filter(ReadingQueue.source == source)

    query = query.order_by(
        nullslast(ReadingQueue.manual_priority.desc()),
        ReadingQueue.priority_score.desc(),
    )

    results = query.offset(offset).limit(limit).all()

    # Collect best_match paper titles in one query
    match_ids = {
        e.best_match_paper_id
        for e, _ in results
        if e.best_match_paper_id
    }
    match_titles: dict[int, str] = {}
    if match_ids:
        for pid, title in (
            db.query(Paper.id, Paper.title)
            .filter(Paper.id.in_(match_ids))
            .all()
        ):
            match_titles[pid] = title

    items = []
    for entry, paper in results:
        items.append({
            "paper_id": paper.id,
            "arxiv_id": paper.arxiv_id,
            "title": paper.title,
            "authors": paper.authors,
            "summary": paper.summary,
            "published_date": (
                paper.published_date.isoformat()
                if paper.published_date
                else None
            ),
            "category": paper.category,
            "pdf_url": paper.pdf_url,
            "generated_summary": paper.generated_summary,
            "priority_score": entry.priority_score,
            "interest_similarity": entry.interest_similarity,
            "citation_impact": entry.citation_impact,
            "freshness_score": entry.freshness_score,
            "category_score": entry.category_score,
            "entity_overlap": entry.entity_overlap,
            "peer_reads_score": entry.peer_reads_score,
            "read_status": entry.read_status,
            "source": entry.source,
            "best_match_paper_id": entry.best_match_paper_id,
            "best_match_score": entry.best_match_score,
            "best_match_title": match_titles.get(
                entry.best_match_paper_id
            ),
            "manual_priority": entry.manual_priority,
            "added_at": (
                entry.added_at.isoformat() if entry.added_at else None
            ),
            "scored_at": (
                entry.scored_at.isoformat() if entry.scored_at else None
            ),
            "read_at": (
                entry.read_at.isoformat() if entry.read_at else None
            ),
        })

    return items


def get_queue_stats(
    db: Session,
    user_id: int = USER_ID,
) -> dict:
    """Get queue statistics for the user."""
    base = db.query(func.count(ReadingQueue.id)).filter(
        ReadingQueue.user_id == user_id
    )

    total_unread = (
        base.filter(ReadingQueue.read_status == "unread").scalar() or 0
    )
    total_reading = (
        base.filter(ReadingQueue.read_status == "reading").scalar() or 0
    )
    total_read = (
        base.filter(ReadingQueue.read_status == "read").scalar() or 0
    )
    total_skipped = (
        base.filter(ReadingQueue.read_status == "skipped").scalar() or 0
    )

    discovery_unread = (
        db.query(func.count(ReadingQueue.id))
        .filter(
            ReadingQueue.user_id == user_id,
            ReadingQueue.source == "discovery",
            ReadingQueue.read_status == "unread",
        )
        .scalar()
        or 0
    )
    bookmark_unread = (
        db.query(func.count(ReadingQueue.id))
        .filter(
            ReadingQueue.user_id == user_id,
            ReadingQueue.source == "bookmark",
            ReadingQueue.read_status == "unread",
        )
        .scalar()
        or 0
    )

    avg_priority = (
        db.query(func.avg(ReadingQueue.priority_score))
        .filter(
            ReadingQueue.user_id == user_id,
            ReadingQueue.read_status == "unread",
        )
        .scalar()
        or 0.0
    )

    high_priority = (
        db.query(func.count(ReadingQueue.id))
        .filter(
            ReadingQueue.user_id == user_id,
            ReadingQueue.read_status == "unread",
            ReadingQueue.priority_score >= 0.7,
        )
        .scalar()
        or 0
    )

    estimated_hours = round(total_unread * 0.25, 1)

    return {
        "total_unread": total_unread,
        "total_reading": total_reading,
        "total_read": total_read,
        "total_skipped": total_skipped,
        "discovery_unread": discovery_unread,
        "bookmark_unread": bookmark_unread,
        "avg_priority": round(float(avg_priority), 3),
        "high_priority_count": high_priority,
        "estimated_reading_hours": estimated_hours,
    }


# ── Status mutations ──────────────────────────────────


def mark_read(
    db: Session,
    paper_id: int,
    user_id: int = USER_ID,
) -> Optional[ReadingQueue]:
    entry = _get_entry(db, user_id, paper_id)
    if not entry:
        return None
    entry.read_status = "read"
    entry.read_at = datetime.utcnow()
    db.commit()
    return entry


def mark_reading(
    db: Session,
    paper_id: int,
    user_id: int = USER_ID,
) -> Optional[ReadingQueue]:
    entry = _get_entry(db, user_id, paper_id)
    if not entry:
        return None
    entry.read_status = "reading"
    db.commit()
    return entry


def mark_skipped(
    db: Session,
    paper_id: int,
    user_id: int = USER_ID,
) -> Optional[ReadingQueue]:
    entry = _get_entry(db, user_id, paper_id)
    if not entry:
        return None
    entry.read_status = "skipped"
    db.commit()
    return entry


def update_manual_priority(
    db: Session,
    paper_id: int,
    priority: Optional[int],
    user_id: int = USER_ID,
) -> Optional[ReadingQueue]:
    entry = _get_entry(db, user_id, paper_id)
    if not entry:
        return None
    entry.manual_priority = priority
    db.commit()
    return entry


def remove_from_queue(
    db: Session,
    paper_id: int,
    user_id: int = USER_ID,
) -> bool:
    deleted = (
        db.query(ReadingQueue)
        .filter(
            ReadingQueue.user_id == user_id,
            ReadingQueue.paper_id == paper_id,
        )
        .delete(synchronize_session="fetch")
    )
    db.commit()
    return deleted > 0


def add_paper_to_queue(
    db: Session,
    paper_id: int,
    user_id: int = USER_ID,
    source: str = "bookmark",
) -> Optional[ReadingQueue]:
    """Add a single paper to the queue with initial scoring."""
    existing = _get_entry(db, user_id, paper_id)
    if existing:
        # Upgrade discovery → bookmark if bookmarked
        if source == "bookmark" and existing.source == "discovery":
            existing.source = "bookmark"
            db.commit()
        return existing

    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        return None

    profile = (
        db.query(UserInterestProfile)
        .filter(UserInterestProfile.user_id == user_id)
        .first()
    )
    iv = _to_embedding_list(
        profile.interest_vector if profile else None
    )

    scores = score_paper(paper, iv)

    entry = ReadingQueue(
        user_id=user_id,
        paper_id=paper_id,
        read_status="unread",
        source=source,
        priority_score=scores["priority_score"],
        interest_similarity=scores["interest_similarity"],
        freshness_score=scores["freshness_score"],
        scored_at=datetime.utcnow() if iv else None,
    )
    db.add(entry)
    db.commit()
    return entry


# ── Internal helpers ──────────────────────────────────


def _get_entry(
    db: Session,
    user_id: int,
    paper_id: int,
) -> Optional[ReadingQueue]:
    return (
        db.query(ReadingQueue)
        .filter(
            ReadingQueue.user_id == user_id,
            ReadingQueue.paper_id == paper_id,
        )
        .first()
    )
