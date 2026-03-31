"""Timeline service — citation graph traversal and timeline construction."""

import logging
from collections import defaultdict, deque
from datetime import date, datetime
from typing import Optional

import numpy as np
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session

from models import CitationLink, Paper, PaperEmbedding, UserLibrary
from services.llm_service import llm_service
from services.query_embedding_cache import query_cache

logger = logging.getLogger(__name__)


# ── Helpers ──────────────────────────────────────────


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


def _get_paper_embedding(paper: Paper) -> Optional[list[float]]:
    """Get best available embedding. Falls back: embedding -> abstract_embedding."""
    for raw in (paper.embedding, paper.abstract_embedding):
        if raw is None:
            continue
        if isinstance(raw, np.ndarray):
            return raw.tolist()
        if isinstance(raw, list):
            return raw
        return list(raw)
    return None


def _count_inbound_citations(
    edges: list[tuple[int, int]],
) -> dict[int, int]:
    """Count how many times each paper is cited within the subgraph."""
    counts: dict[int, int] = defaultdict(int)
    for _src, tgt in edges:
        counts[tgt] += 1
    return dict(counts)


# ── Response schemas ─────────────────────────────────


class TimelineNode(BaseModel):
    """A single paper node in the timeline visualization."""

    paper_id: Optional[int] = None  # None for ghost nodes
    arxiv_id: str
    title: str
    authors: object = None
    summary: Optional[str] = None
    published_date: Optional[str] = None
    category: Optional[str] = None
    citation_count: int = 0
    is_seminal: bool = False
    is_in_library: bool = False
    is_ghost: bool = False
    branch_id: int = 0
    x_position: float = 0.0
    y_position: float = 0.0


class TimelineEdge(BaseModel):
    """A directed edge between two papers in the timeline."""

    source_paper_id: int
    target_paper_id: int
    edge_type: str = "cites"


class TimelineResponse(BaseModel):
    """Full timeline graph response."""

    nodes: list[TimelineNode] = []
    edges: list[TimelineEdge] = []
    query: Optional[str] = None
    seed_paper_id: Optional[int] = None


# ── Citation graph queries ───────────────────────────


def get_papers_citing(
    paper_id: int,
    arxiv_id: Optional[str],
    db: Session,
) -> list[int]:
    """Return IDs of papers that cite the given paper.

    Matches on resolved_paper_id or target_arxiv_id.
    """
    conditions = [CitationLink.resolved_paper_id == paper_id]
    if arxiv_id is not None:
        conditions.append(CitationLink.target_arxiv_id == arxiv_id)

    rows = (
        db.query(CitationLink.source_paper_id)
        .filter(or_(*conditions))
        .distinct()
        .all()
    )
    return [r[0] for r in rows]


def get_papers_cited_by(
    paper_id: int,
    db: Session,
) -> list[int]:
    """Return IDs of papers cited by the given paper (resolved only)."""
    rows = (
        db.query(CitationLink.resolved_paper_id)
        .filter(
            CitationLink.source_paper_id == paper_id,
            CitationLink.resolved_paper_id.isnot(None),
        )
        .distinct()
        .all()
    )
    return [r[0] for r in rows]


def get_citation_subgraph(
    paper_ids: list[int],
    db: Session,
) -> list[tuple[int, int]]:
    """Return directed edges within the given set of papers."""
    if not paper_ids:
        return []

    rows = (
        db.query(
            CitationLink.source_paper_id,
            CitationLink.resolved_paper_id,
        )
        .filter(
            CitationLink.source_paper_id.in_(paper_ids),
            CitationLink.resolved_paper_id.in_(paper_ids),
            CitationLink.resolved_paper_id.isnot(None),
        )
        .all()
    )
    return [(r[0], r[1]) for r in rows]


# ── BFS traversal ────────────────────────────────────


def _fetch_arxiv_ids(
    paper_ids: set[int],
    db: Session,
) -> dict[int, str]:
    """Batch-fetch arxiv_id for a set of paper IDs."""
    if not paper_ids:
        return {}
    rows = (
        db.query(Paper.id, Paper.arxiv_id)
        .filter(
            Paper.id.in_(paper_ids),
            Paper.arxiv_id.isnot(None),
        )
        .all()
    )
    return {r[0]: r[1] for r in rows}


def _expand_forward(
    frontier: set[int],
    db: Session,
) -> set[int]:
    """Find papers that cite any paper in the frontier (single query)."""
    if not frontier:
        return set()

    arxiv_map = _fetch_arxiv_ids(frontier, db)
    arxiv_ids = list(arxiv_map.values())

    conditions = [CitationLink.resolved_paper_id.in_(frontier)]
    if arxiv_ids:
        conditions.append(CitationLink.target_arxiv_id.in_(arxiv_ids))

    rows = (
        db.query(CitationLink.source_paper_id)
        .filter(or_(*conditions))
        .distinct()
        .all()
    )
    return {r[0] for r in rows}


def _expand_backward(
    frontier: set[int],
    db: Session,
) -> set[int]:
    """Find papers cited by any paper in the frontier (single query)."""
    if not frontier:
        return set()

    rows = (
        db.query(CitationLink.resolved_paper_id)
        .filter(
            CitationLink.source_paper_id.in_(frontier),
            CitationLink.resolved_paper_id.isnot(None),
        )
        .distinct()
        .all()
    )
    return {r[0] for r in rows}


def bfs_citations(
    seed_id: int,
    db: Session,
    *,
    max_hops: int = 2,
    direction: str = "both",
) -> set[int]:
    """BFS traversal over the citation graph.

    Args:
        seed_id: Starting paper ID.
        db: SQLAlchemy session.
        max_hops: Maximum traversal depth.
        direction: "forward" (citing), "backward" (cited by),
                   or "both".

    Returns:
        Set of all discovered paper IDs (includes seed).
    """
    visited: set[int] = {seed_id}
    frontier: set[int] = {seed_id}

    for _hop in range(max_hops):
        if not frontier:
            break

        neighbors: set[int] = set()

        if direction in ("forward", "both"):
            neighbors |= _expand_forward(frontier, db)

        if direction in ("backward", "both"):
            neighbors |= _expand_backward(frontier, db)

        frontier = neighbors - visited
        visited |= frontier

    return visited


# ── Timeline construction ───────────────────────────


def _identify_seminal_papers(
    papers_map: dict[int, Paper],
    citation_counts: dict[int, int],
    *,
    top_n: int = 3,
) -> set[int]:
    """Score papers by age and citation rank; return top N IDs."""
    if not papers_map:
        return set()
    if len(papers_map) == 1:
        return set(papers_map.keys())

    paper_ids = list(papers_map.keys())
    dates: list[tuple[int, datetime]] = []
    for pid in paper_ids:
        pub = papers_map[pid].published_date
        if isinstance(pub, datetime):
            dt = pub
        elif isinstance(pub, date):
            dt = datetime.combine(pub, datetime.min.time())
        else:
            dt = datetime.min
        dates.append((pid, dt))

    dates.sort(key=lambda x: x[1])
    age_rank: dict[int, float] = {}
    max_idx = len(dates) - 1
    for i, (pid, _) in enumerate(dates):
        age_rank[pid] = i / max_idx if max_idx > 0 else 1.0

    max_cites = max(
        (citation_counts.get(pid, 0) for pid in paper_ids), default=0
    )
    cite_rank: dict[int, float] = {}
    for pid in paper_ids:
        raw = citation_counts.get(pid, 0)
        cite_rank[pid] = raw / max_cites if max_cites > 0 else 0.0

    scored = sorted(
        paper_ids,
        key=lambda pid: 0.5 * age_rank[pid] + 0.5 * cite_rank[pid],
        reverse=True,
    )
    return set(scored[:top_n])


def _detect_branches(
    paper_ids: list[int],
    edges: list[tuple[int, int]],
    papers_map: dict[int, Paper],
) -> dict[int, int]:
    """BFS branch detection. Fork when a node has 2+ unlinked children."""
    if not paper_ids:
        return {}

    pid_set = set(paper_ids)
    children_of: dict[int, set[int]] = defaultdict(set)
    parents_of: dict[int, set[int]] = defaultdict(set)
    edge_set: set[tuple[int, int]] = set()
    for src, tgt in edges:
        children_of[tgt].add(src)
        parents_of[src].add(tgt)
        edge_set.add((src, tgt))

    roots = {pid for pid in pid_set if not parents_of.get(pid)}
    if not roots:
        dated = sorted(
            pid_set,
            key=lambda p: getattr(
                papers_map.get(p), "published_date", None
            )
            or datetime.max,
        )
        roots = {dated[0]} if dated else pid_set

    assignments: dict[int, int] = {}
    branch_counter = 0
    queue: deque[tuple[int, int]] = deque()
    for r in sorted(roots):
        queue.append((r, branch_counter))
        branch_counter += 1

    visited: set[int] = set()
    while queue:
        node, branch = queue.popleft()
        if node in visited:
            continue
        visited.add(node)
        assignments[node] = branch

        kids = sorted(children_of.get(node, set()) - visited)
        if len(kids) >= 2:
            linked = any(
                (a, b) in edge_set or (b, a) in edge_set
                for a in kids
                for b in kids
                if a != b
            )
            if not linked:
                # First child inherits parent branch
                queue.append((kids[0], branch))
                for kid in kids[1:]:
                    queue.append((kid, branch_counter))
                    branch_counter += 1
                continue
        for kid in kids:
            queue.append((kid, branch))

    for pid in pid_set:
        if pid not in assignments:
            assignments[pid] = 0
    return assignments


def _get_library_paper_ids(db: Session) -> set[int]:
    """Get all paper IDs in the current user's library."""
    rows = (
        db.query(UserLibrary.paper_id)
        .filter(
            UserLibrary.user_id == 1,  # Hardcoded user
            UserLibrary.paper_id.isnot(None),
        )
        .all()
    )
    return {r[0] for r in rows}


def _fetch_ghost_nodes(
    cluster_ids: list[int],
    db: Session,
    *,
    max_ghosts: int = 10,
) -> tuple[list[TimelineNode], list[TimelineEdge]]:
    """TR-4.1 — Fetch top unresolved citations as ghost nodes."""
    if not cluster_ids:
        return [], []

    from sqlalchemy import func as sa_func

    # Find unresolved citations from cluster papers, grouped by target
    rows = (
        db.query(
            CitationLink.target_arxiv_id,
            CitationLink.target_title,
            CitationLink.published_year,
            sa_func.count(CitationLink.id).label("cite_count"),
            sa_func.array_agg(CitationLink.source_paper_id).label("source_ids"),
        )
        .filter(
            CitationLink.source_paper_id.in_(cluster_ids),
            CitationLink.resolved_paper_id.is_(None),
            CitationLink.target_arxiv_id.isnot(None),
        )
        .group_by(
            CitationLink.target_arxiv_id,
            CitationLink.target_title,
            CitationLink.published_year,
        )
        .order_by(sa_func.count(CitationLink.id).desc())
        .limit(max_ghosts)
        .all()
    )

    ghost_nodes: list[TimelineNode] = []
    ghost_edges: list[TimelineEdge] = []

    for row in rows:
        arxiv_id = row.target_arxiv_id or ""
        title = row.target_title or arxiv_id
        pub_year = row.published_year
        source_ids = row.source_ids or []

        ghost_nodes.append(TimelineNode(
            paper_id=None,
            arxiv_id=arxiv_id,
            title=title,
            published_date=f"{pub_year}-01-01" if pub_year else None,
            citation_count=row.cite_count,
            is_ghost=True,
        ))

        for src_id in source_ids:
            ghost_edges.append(TimelineEdge(
                source_paper_id=src_id,
                target_paper_id=-hash(arxiv_id) % 100000,  # Stable negative-ish ID for ghost
                edge_type="cites",
            ))

    return ghost_nodes, ghost_edges


def _build_nodes(
    papers_map: dict[int, Paper],
    citation_counts: dict[int, int],
    seminal_ids: set[int],
    branch_assignments: dict[int, int],
    library_ids: set[int] | None = None,
) -> list[TimelineNode]:
    """Build positioned TimelineNode list from paper data."""
    if not papers_map:
        return []
    if library_ids is None:
        library_ids = set()

    def _to_timestamp(pub: date | datetime | None) -> float:
        if isinstance(pub, datetime):
            return pub.timestamp()
        if isinstance(pub, date):
            return datetime.combine(pub, datetime.min.time()).timestamp()
        return 0.0

    def _to_iso(pub: date | datetime | None) -> str | None:
        if isinstance(pub, (date, datetime)):
            return pub.isoformat()
        return None

    timestamps: list[tuple[int, float]] = []
    for pid, paper in papers_map.items():
        timestamps.append((pid, _to_timestamp(paper.published_date)))

    ts_values = [t for _, t in timestamps]
    min_ts = min(ts_values)
    max_ts = max(ts_values)
    ts_range = max_ts - min_ts

    nodes: list[TimelineNode] = []
    for pid, paper in papers_map.items():
        ts = _to_timestamp(paper.published_date)
        x = (ts - min_ts) / ts_range if ts_range > 0 else 0.5
        bid = branch_assignments.get(pid, 0)
        y = float(bid)  # Lane index, frontend applies spacing

        pub_iso = _to_iso(paper.published_date)
        nodes.append(TimelineNode(
            paper_id=pid,
            arxiv_id=paper.arxiv_id or "",
            title=paper.title or "",
            authors=paper.authors,
            summary=paper.generated_summary or paper.summary,
            published_date=pub_iso,
            category=paper.category,
            citation_count=citation_counts.get(pid, 0),
            is_seminal=pid in seminal_ids,
            is_in_library=pid in library_ids,
            branch_id=bid,
            x_position=x,
            y_position=y,
        ))
    return nodes


def _compute_similarity_edges(
    papers_map: dict[int, Paper],
    *,
    threshold: float = 0.82,
    max_edges_per_node: int = 3,
) -> list[tuple[int, int]]:
    """Generate edges between semantically similar papers.

    Used as a fallback when no citation data exists.
    Connects older papers → newer papers (directed by date).
    """
    items: list[tuple[int, Paper, list[float]]] = []
    for pid, paper in papers_map.items():
        emb = _get_paper_embedding(paper)
        if emb is not None:
            items.append((pid, paper, emb))

    if len(items) < 2:
        return []

    # Sort by publication date so edges go old → new
    def _pub_ts(paper: Paper) -> float:
        pub = paper.published_date
        if isinstance(pub, datetime):
            return pub.timestamp()
        if isinstance(pub, date):
            return datetime.combine(pub, datetime.min.time()).timestamp()
        return 0.0

    items.sort(key=lambda x: _pub_ts(x[1]))

    edges: list[tuple[int, int]] = []
    edge_count: dict[int, int] = defaultdict(int)

    for i in range(len(items)):
        pid_a, paper_a, emb_a = items[i]
        best: list[tuple[float, int]] = []

        for j in range(i + 1, len(items)):
            pid_b, paper_b, emb_b = items[j]
            sim = _cosine_similarity(emb_a, emb_b)
            if sim >= threshold:
                best.append((sim, pid_b))

        # Take top-k most similar newer papers
        best.sort(key=lambda x: -x[0])
        for sim, pid_b in best[:max_edges_per_node]:
            if edge_count[pid_a] >= max_edges_per_node:
                break
            if edge_count[pid_b] >= max_edges_per_node * 2:
                continue
            edges.append((pid_a, pid_b))
            edge_count[pid_a] += 1
            edge_count[pid_b] += 1

    # If threshold was too strict and we got very few edges, retry with lower threshold
    if len(edges) < len(papers_map) // 3 and threshold > 0.7:
        return _compute_similarity_edges(
            papers_map, threshold=threshold - 0.05, max_edges_per_node=max_edges_per_node
        )

    return edges


def build_timeline_from_topic(
    query: str,
    db: Session,
    *,
    limit: int = 50,
    library_only: bool = False,
) -> TimelineResponse:
    """Build a timeline from a topic query via semantic search."""
    query_embedding = query_cache.get_or_generate(
        query, task_type="retrieval_query", db=db,
    )

    # Try PaperEmbedding table first, fall back to Paper.embedding column
    has_paper_embeddings = db.query(PaperEmbedding.id).limit(1).first() is not None

    if has_paper_embeddings:
        base_query = (
            db.query(Paper)
            .join(PaperEmbedding, PaperEmbedding.paper_id == Paper.id)
        )
        if library_only:
            library_ids = _get_library_paper_ids(db)
            if not library_ids:
                return TimelineResponse(query=query)
            base_query = base_query.filter(Paper.id.in_(library_ids))
        papers = (
            base_query
            .order_by(PaperEmbedding.embedding.l2_distance(query_embedding))
            .limit(limit)
            .all()
        )
    else:
        # Fall back to Paper.embedding column
        base_query = (
            db.query(Paper)
            .filter(Paper.embedding.isnot(None))
        )
        if library_only:
            library_ids = _get_library_paper_ids(db)
            if not library_ids:
                return TimelineResponse(query=query)
            base_query = base_query.filter(Paper.id.in_(library_ids))
        papers = (
            base_query
            .order_by(Paper.embedding.l2_distance(query_embedding))
            .limit(limit)
            .all()
        )
    if not papers:
        return TimelineResponse(query=query)

    paper_ids = [p.id for p in papers]
    papers_map: dict[int, Paper] = {p.id: p for p in papers}
    citation_edges = get_citation_subgraph(paper_ids, db)
    used_similarity = False

    # If no citation edges exist, generate similarity-based edges
    if citation_edges:
        edges = citation_edges
    else:
        edges = _compute_similarity_edges(papers_map)
        used_similarity = True

    library_ids_set = _get_library_paper_ids(db)
    citation_counts = _count_inbound_citations(edges)
    seminal_ids = _identify_seminal_papers(papers_map, citation_counts)
    branches = _detect_branches(paper_ids, edges, papers_map)
    nodes = _build_nodes(papers_map, citation_counts, seminal_ids, branches, library_ids_set)

    edge_type = "related" if used_similarity else "cites"
    edge_objects = [
        TimelineEdge(source_paper_id=s, target_paper_id=t, edge_type=edge_type)
        for s, t in edges
        if s in papers_map and t in papers_map
    ]

    # TR-4.1 — Ghost nodes for unresolved citations (only if we have citation data)
    if not used_similarity:
        ghost_nodes, ghost_edges = _fetch_ghost_nodes(paper_ids, db)
        nodes.extend(ghost_nodes)
        edge_objects.extend(ghost_edges)

    return TimelineResponse(nodes=nodes, edges=edge_objects, query=query)


def _fetch_papers_batch(
    paper_ids: set[int],
    db: Session,
) -> dict[int, Paper]:
    """Batch-fetch Paper objects by IDs (no N+1)."""
    if not paper_ids:
        return {}
    rows = db.query(Paper).filter(Paper.id.in_(paper_ids)).all()
    return {p.id: p for p in rows}


def build_timeline_from_paper(
    paper_id: int,
    db: Session,
    *,
    hops: int = 2,
) -> TimelineResponse:
    """Build a timeline radiating from a seed paper."""
    seed = db.query(Paper).filter(Paper.id == paper_id).first()
    if seed is None:
        return TimelineResponse(seed_paper_id=paper_id)

    one_hop_ids = bfs_citations(paper_id, db, max_hops=1) - {paper_id}
    all_ids = bfs_citations(paper_id, db, max_hops=hops)
    papers_map = _fetch_papers_batch(all_ids, db)

    seed_emb = _get_paper_embedding(seed)
    if seed_emb is not None:
        filtered: dict[int, Paper] = {paper_id: seed}
        for pid, paper in papers_map.items():
            if pid == paper_id:
                continue
            if pid in one_hop_ids:
                filtered[pid] = paper
                continue
            emb = _get_paper_embedding(paper)
            if emb is not None and _cosine_similarity(seed_emb, emb) > 0.7:
                filtered[pid] = paper
        papers_map = filtered

    paper_ids_list = list(papers_map.keys())
    edges = get_citation_subgraph(paper_ids_list, db)

    # Fallback: similarity edges when no citation data
    if not edges:
        edges = _compute_similarity_edges(papers_map)

    library_ids_set = _get_library_paper_ids(db)
    citation_counts = _count_inbound_citations(edges)
    seminal_ids = _identify_seminal_papers(papers_map, citation_counts)
    branches = _detect_branches(paper_ids_list, edges, papers_map)
    nodes = _build_nodes(
        papers_map, citation_counts, seminal_ids, branches, library_ids_set
    )
    edge_objects = [
        TimelineEdge(source_paper_id=s, target_paper_id=t)
        for s, t in edges
        if s in papers_map and t in papers_map
    ]

    # TR-4.1 — Ghost nodes
    ghost_nodes, ghost_edges = _fetch_ghost_nodes(paper_ids_list, db)
    nodes.extend(ghost_nodes)
    edge_objects.extend(ghost_edges)

    return TimelineResponse(
        nodes=nodes, edges=edge_objects, seed_paper_id=paper_id
    )
