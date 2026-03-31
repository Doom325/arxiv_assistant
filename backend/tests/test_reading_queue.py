"""Tests for reading queue service and router."""

import math
from datetime import datetime, date, timedelta
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from models import (
    Paper,
    ReadingQueue,
    User,
    UserInterestProfile,
    UserLibrary,
)
from services.reading_queue_service import (
    _cosine_similarity,
    add_paper_to_queue,
    compute_user_interest_vector,
    rescore_queue,
    score_paper,
    sync_queue_from_library,
    INTEREST_HALF_LIFE,
    WEIGHT_FRESHNESS,
    WEIGHT_INTEREST,
)


# ── Unit: cosine similarity ──────────────────────────


class TestCosineSimilarity:
    def test_identical_vectors(self):
        v = [1.0, 0.0, 0.0]
        assert _cosine_similarity(v, v) == pytest.approx(1.0)

    def test_orthogonal_vectors(self):
        a = [1.0, 0.0, 0.0]
        b = [0.0, 1.0, 0.0]
        assert _cosine_similarity(a, b) == pytest.approx(0.0)

    def test_opposite_vectors(self):
        a = [1.0, 0.0]
        b = [-1.0, 0.0]
        assert _cosine_similarity(a, b) == pytest.approx(-1.0)

    def test_zero_vector(self):
        a = [0.0, 0.0]
        b = [1.0, 1.0]
        assert _cosine_similarity(a, b) == 0.0


# ── Unit: score_paper ────────────────────────────────


class TestScorePaper:
    def _make_paper(
        self,
        embedding=None,
        published_date=None,
    ):
        paper = MagicMock()
        paper.embedding = embedding
        paper.published_date = published_date
        return paper

    def test_cold_start_no_interest_vector(self):
        """No interest vector → interest_similarity = 0."""
        paper = self._make_paper(
            embedding=[0.5] * 768,
            published_date=datetime.utcnow(),
        )
        scores = score_paper(paper, interest_vector=None)
        assert scores["interest_similarity"] == 0.0
        assert scores["freshness_score"] > 0.0
        assert scores["priority_score"] >= 0.0

    def test_fresh_paper_scores_higher(self):
        """A paper published today should score higher than 30 days ago."""
        interest = [0.5] * 768
        fresh = self._make_paper(
            embedding=[0.5] * 768,
            published_date=datetime.utcnow(),
        )
        stale = self._make_paper(
            embedding=[0.5] * 768,
            published_date=datetime.utcnow() - timedelta(days=30),
        )
        fresh_scores = score_paper(fresh, interest)
        stale_scores = score_paper(stale, interest)
        assert fresh_scores["freshness_score"] > stale_scores[
            "freshness_score"
        ]
        assert fresh_scores["priority_score"] > stale_scores[
            "priority_score"
        ]

    def test_no_embedding_paper(self):
        """Paper without embedding gets 0 interest."""
        paper = self._make_paper(
            embedding=None,
            published_date=datetime.utcnow(),
        )
        interest = [0.5] * 768
        scores = score_paper(paper, interest)
        assert scores["interest_similarity"] == 0.0

    def test_score_bounded(self):
        """Priority score should be between 0 and 1."""
        paper = self._make_paper(
            embedding=[1.0] * 768,
            published_date=datetime.utcnow(),
        )
        interest = [1.0] * 768
        scores = score_paper(paper, interest)
        assert 0.0 <= scores["priority_score"] <= 1.0

    def test_freshness_decay(self):
        """Freshness decays exponentially."""
        paper = self._make_paper(
            published_date=datetime.utcnow() - timedelta(days=10),
        )
        scores = score_paper(paper, None)
        expected = math.exp(-0.03 * 10)
        assert scores["freshness_score"] == pytest.approx(
            expected, abs=0.01
        )

    def test_no_date_paper(self):
        """Paper without date gets 0 freshness."""
        paper = self._make_paper(
            embedding=[0.5] * 768,
            published_date=None,
        )
        scores = score_paper(paper, [0.5] * 768)
        assert scores["freshness_score"] == 0.0

    def test_mvp_signals_only(self):
        """Phase 2 signals should be 0 in MVP."""
        paper = self._make_paper(
            embedding=[0.5] * 768,
            published_date=datetime.utcnow(),
        )
        scores = score_paper(paper, [0.5] * 768)
        assert scores["citation_impact"] == 0.0
        assert scores["category_score"] == 0.0
        assert scores["entity_overlap"] == 0.0
        assert scores["peer_reads_score"] == 0.0


# ── Unit: score normalization ────────────────────────


class TestScoreNormalization:
    def test_perfect_score_is_one(self):
        """Identical vectors + today's paper → score near 1.0."""
        paper = MagicMock()
        paper.embedding = [1.0] * 768
        paper.published_date = datetime.utcnow()

        scores = score_paper(paper, [1.0] * 768)
        # Interest sim = 1.0, freshness ~ 1.0
        assert scores["priority_score"] == pytest.approx(1.0, abs=0.02)

    def test_worst_score_near_zero(self):
        """No interest vector + very old paper → score near 0."""
        paper = MagicMock()
        paper.embedding = None
        paper.published_date = datetime.utcnow() - timedelta(days=365)

        scores = score_paper(paper, None)
        assert scores["priority_score"] < 0.05


# ── Helper: create test fixtures in DB ───────────────


def _make_user(db_session) -> User:
    """Insert a default test user and return it."""
    user = User(id=1, email="test@example.com", is_active=True)
    db_session.add(user)
    db_session.commit()
    return user


def _make_paper_row(
    db_session,
    *,
    arxiv_id: str = "2401.00001",
    title: str = "Test Paper",
    embedding=None,
    abstract_embedding=None,
    published_date=None,
    generated_summary=None,
    category: str = "cs.AI",
) -> Paper:
    """Insert a Paper row and return it."""
    paper = Paper(
        arxiv_id=arxiv_id,
        title=title,
        authors=["Author A"],
        summary="A test summary.",
        published_date=published_date or datetime.utcnow(),
        category=category,
        pdf_url=f"http://example.com/{arxiv_id}.pdf",
        embedding=embedding,
        abstract_embedding=abstract_embedding,
        generated_summary=generated_summary,
    )
    db_session.add(paper)
    db_session.commit()
    db_session.refresh(paper)
    return paper


def _make_library_entry(
    db_session,
    user_id: int,
    paper_id: int,
) -> UserLibrary:
    """Insert a UserLibrary bookmark."""
    entry = UserLibrary(
        user_id=user_id,
        paper_id=paper_id,
        list_name="Bookmarks",
    )
    db_session.add(entry)
    db_session.commit()
    return entry


def _make_queue_entry(
    db_session,
    user_id: int,
    paper_id: int,
    *,
    source: str = "bookmark",
    read_status: str = "unread",
    priority_score: float = 0.5,
) -> ReadingQueue:
    """Insert a ReadingQueue entry."""
    entry = ReadingQueue(
        user_id=user_id,
        paper_id=paper_id,
        source=source,
        read_status=read_status,
        priority_score=priority_score,
    )
    db_session.add(entry)
    db_session.commit()
    db_session.refresh(entry)
    return entry


# ── Service: compute_user_interest_vector ────────────


class TestComputeUserInterestVector:
    def test_cold_start_returns_none(self, db_session):
        """No engaged papers returns None."""
        _make_user(db_session)
        result = compute_user_interest_vector(db_session, user_id=1)
        assert result is None

    def test_single_bookmarked_paper(self, db_session):
        """One bookmarked paper with embedding returns that embedding."""
        user = _make_user(db_session)
        emb = [0.1] * 768
        paper = _make_paper_row(
            db_session,
            arxiv_id="2401.00001",
            embedding=emb,
            published_date=datetime.utcnow(),
        )
        _make_library_entry(db_session, user.id, paper.id)

        result = compute_user_interest_vector(db_session, user_id=1)
        assert result is not None
        assert len(result) == 768
        # Single paper: result should match the paper embedding
        assert result == pytest.approx(emb, abs=1e-6)

    def test_time_decay_weighting(self, db_session):
        """Recent papers should be weighted more than old papers."""
        user = _make_user(db_session)
        recent_emb = [1.0] * 768
        old_emb = [0.0] * 768

        recent_paper = _make_paper_row(
            db_session,
            arxiv_id="2401.00001",
            embedding=recent_emb,
            published_date=datetime.utcnow(),
        )
        old_paper = _make_paper_row(
            db_session,
            arxiv_id="2401.00002",
            embedding=old_emb,
            published_date=datetime.utcnow() - timedelta(days=90),
        )
        _make_library_entry(db_session, user.id, recent_paper.id)
        _make_library_entry(db_session, user.id, old_paper.id)

        result = compute_user_interest_vector(db_session, user_id=1)
        assert result is not None
        # Recent paper (emb=1.0) has higher weight than old (emb=0.0).
        # The average should be pulled toward 1.0.
        recent_decay = math.exp(
            -math.log(2) * 0 / INTEREST_HALF_LIFE
        )  # 1.0
        old_decay = math.exp(
            -math.log(2) * 90 / INTEREST_HALF_LIFE
        )  # ~0.125
        expected_val = (
            1.0 * recent_decay + 0.0 * old_decay
        ) / (recent_decay + old_decay)
        assert result[0] == pytest.approx(expected_val, abs=0.01)

    def test_summary_paper_included(self, db_session):
        """Paper with generated_summary (not bookmarked) is engaged."""
        _make_user(db_session)
        emb = [0.3] * 768
        _make_paper_row(
            db_session,
            arxiv_id="2401.00003",
            embedding=emb,
            published_date=datetime.utcnow(),
            generated_summary="A generated summary.",
        )

        result = compute_user_interest_vector(db_session, user_id=1)
        assert result is not None
        assert result[0] == pytest.approx(0.3, abs=1e-6)

    def test_paper_without_embedding_skipped(self, db_session):
        """Paper with no embedding at all is skipped entirely."""
        user = _make_user(db_session)
        _make_paper_row(
            db_session,
            arxiv_id="2401.00004",
            embedding=None,
            abstract_embedding=None,
            published_date=datetime.utcnow(),
        )
        # No library entry needed; paper has generated_summary
        # but no embedding — should not count.
        result = compute_user_interest_vector(db_session, user_id=1)
        assert result is None


# ── Service: sync_queue_from_library ─────────────────


class TestSyncQueueFromLibrary:
    def test_adds_missing_papers(self, db_session):
        """Papers in library but not queue get added."""
        user = _make_user(db_session)
        p1 = _make_paper_row(
            db_session, arxiv_id="2401.00010"
        )
        p2 = _make_paper_row(
            db_session, arxiv_id="2401.00011"
        )
        _make_library_entry(db_session, user.id, p1.id)
        _make_library_entry(db_session, user.id, p2.id)

        added, removed = sync_queue_from_library(
            db_session, user_id=1
        )
        assert added == 2
        assert removed == 0

        # Verify entries exist in queue
        count = (
            db_session.query(ReadingQueue)
            .filter(ReadingQueue.user_id == 1)
            .count()
        )
        assert count == 2

    def test_removes_unbookmarked_papers(self, db_session):
        """Queue entries for papers no longer in library are removed."""
        user = _make_user(db_session)
        paper = _make_paper_row(
            db_session, arxiv_id="2401.00012"
        )
        # Queue entry exists but no library entry
        _make_queue_entry(
            db_session, user.id, paper.id, source="bookmark"
        )

        added, removed = sync_queue_from_library(
            db_session, user_id=1
        )
        assert added == 0
        assert removed == 1

        count = (
            db_session.query(ReadingQueue)
            .filter(ReadingQueue.user_id == 1)
            .count()
        )
        assert count == 0

    def test_discovery_upgraded_to_bookmark(self, db_session):
        """Discovery entry is upgraded to bookmark source on sync."""
        user = _make_user(db_session)
        paper = _make_paper_row(
            db_session, arxiv_id="2401.00013"
        )
        _make_queue_entry(
            db_session, user.id, paper.id, source="discovery"
        )
        _make_library_entry(db_session, user.id, paper.id)

        added, removed = sync_queue_from_library(
            db_session, user_id=1
        )
        assert added == 1  # counts as added (upgraded)
        assert removed == 0

        entry = (
            db_session.query(ReadingQueue)
            .filter(
                ReadingQueue.user_id == 1,
                ReadingQueue.paper_id == paper.id,
            )
            .first()
        )
        assert entry.source == "bookmark"

    def test_idempotent_sync(self, db_session):
        """Running sync twice produces no extra adds or removes."""
        user = _make_user(db_session)
        paper = _make_paper_row(
            db_session, arxiv_id="2401.00014"
        )
        _make_library_entry(db_session, user.id, paper.id)

        sync_queue_from_library(db_session, user_id=1)
        added, removed = sync_queue_from_library(
            db_session, user_id=1
        )
        assert added == 0
        assert removed == 0

    def test_only_touches_bookmark_source(self, db_session):
        """Discovery entries without library match are NOT removed."""
        user = _make_user(db_session)
        paper = _make_paper_row(
            db_session, arxiv_id="2401.00015"
        )
        _make_queue_entry(
            db_session, user.id, paper.id, source="discovery"
        )

        added, removed = sync_queue_from_library(
            db_session, user_id=1
        )
        assert removed == 0

        count = (
            db_session.query(ReadingQueue)
            .filter(ReadingQueue.user_id == 1)
            .count()
        )
        assert count == 1


# ── Service: rescore_queue ───────────────────────────


class TestRescoreQueue:
    def test_rescores_unread_entries(self, db_session):
        """Unread queue entries get rescored."""
        user = _make_user(db_session)
        emb = [0.5] * 768
        paper = _make_paper_row(
            db_session,
            arxiv_id="2401.00020",
            embedding=emb,
            published_date=datetime.utcnow(),
        )
        _make_queue_entry(
            db_session,
            user.id,
            paper.id,
            priority_score=0.0,
        )

        count = rescore_queue(db_session, user_id=1)
        assert count == 1

        entry = (
            db_session.query(ReadingQueue)
            .filter(ReadingQueue.paper_id == paper.id)
            .first()
        )
        # Score should be updated (freshness > 0 for today's paper)
        assert entry.priority_score > 0.0
        assert entry.scored_at is not None

    def test_skips_read_and_skipped(self, db_session):
        """Already read/skipped entries are not rescored."""
        user = _make_user(db_session)
        p1 = _make_paper_row(
            db_session, arxiv_id="2401.00021"
        )
        p2 = _make_paper_row(
            db_session, arxiv_id="2401.00022"
        )
        _make_queue_entry(
            db_session,
            user.id,
            p1.id,
            read_status="read",
        )
        _make_queue_entry(
            db_session,
            user.id,
            p2.id,
            read_status="skipped",
        )

        count = rescore_queue(db_session, user_id=1)
        assert count == 0

    def test_empty_queue_returns_zero(self, db_session):
        """Empty queue returns 0 rescored."""
        _make_user(db_session)
        count = rescore_queue(db_session, user_id=1)
        assert count == 0

    def test_rescores_reading_entries(self, db_session):
        """Entries with status 'reading' are also rescored."""
        user = _make_user(db_session)
        paper = _make_paper_row(
            db_session,
            arxiv_id="2401.00023",
            embedding=[0.5] * 768,
            published_date=datetime.utcnow(),
        )
        _make_queue_entry(
            db_session,
            user.id,
            paper.id,
            read_status="reading",
            priority_score=0.0,
        )

        count = rescore_queue(db_session, user_id=1)
        assert count == 1

    def test_caches_interest_profile(self, db_session):
        """Rescore creates/updates UserInterestProfile."""
        user = _make_user(db_session)
        emb = [0.5] * 768
        paper = _make_paper_row(
            db_session,
            arxiv_id="2401.00024",
            embedding=emb,
            published_date=datetime.utcnow(),
        )
        _make_library_entry(db_session, user.id, paper.id)
        _make_queue_entry(db_session, user.id, paper.id)

        rescore_queue(db_session, user_id=1)

        profile = (
            db_session.query(UserInterestProfile)
            .filter(UserInterestProfile.user_id == 1)
            .first()
        )
        assert profile is not None
        assert profile.computed_at is not None


# ── Service: add_paper_to_queue ──────────────────────


class TestAddPaperToQueue:
    def test_add_new_paper(self, db_session):
        """Adding a paper creates a queue entry."""
        _make_user(db_session)
        paper = _make_paper_row(
            db_session,
            arxiv_id="2401.00030",
            embedding=[0.5] * 768,
            published_date=datetime.utcnow(),
        )

        result = add_paper_to_queue(
            db_session, paper.id, user_id=1
        )
        assert result is not None
        assert result.paper_id == paper.id
        assert result.source == "bookmark"
        assert result.read_status == "unread"

    def test_duplicate_returns_existing(self, db_session):
        """Adding same paper twice returns the existing entry."""
        _make_user(db_session)
        paper = _make_paper_row(
            db_session, arxiv_id="2401.00031"
        )

        first = add_paper_to_queue(
            db_session, paper.id, user_id=1
        )
        second = add_paper_to_queue(
            db_session, paper.id, user_id=1
        )
        assert first.id == second.id

        count = (
            db_session.query(ReadingQueue)
            .filter(ReadingQueue.user_id == 1)
            .count()
        )
        assert count == 1

    def test_discovery_upgraded_to_bookmark(self, db_session):
        """Adding bookmark when discovery entry exists upgrades source."""
        _make_user(db_session)
        paper = _make_paper_row(
            db_session, arxiv_id="2401.00032"
        )
        _make_queue_entry(
            db_session, 1, paper.id, source="discovery"
        )

        result = add_paper_to_queue(
            db_session, paper.id, user_id=1, source="bookmark"
        )
        assert result.source == "bookmark"

    def test_nonexistent_paper_returns_none(self, db_session):
        """Adding a paper that doesn't exist returns None."""
        _make_user(db_session)
        result = add_paper_to_queue(
            db_session, 99999, user_id=1
        )
        assert result is None

    def test_discovery_source_preserved(self, db_session):
        """Adding as discovery when discovery already exists keeps source."""
        _make_user(db_session)
        paper = _make_paper_row(
            db_session, arxiv_id="2401.00033"
        )
        _make_queue_entry(
            db_session, 1, paper.id, source="discovery"
        )

        result = add_paper_to_queue(
            db_session,
            paper.id,
            user_id=1,
            source="discovery",
        )
        assert result.source == "discovery"


# ── Router: queue endpoints ──────────────────────────


class TestQueueRouter:
    def _setup_user_and_paper(self, db_session):
        """Create user, paper, and queue entry for router tests."""
        user = _make_user(db_session)
        paper = _make_paper_row(
            db_session,
            arxiv_id="2401.00040",
            embedding=[0.5] * 768,
            published_date=datetime.utcnow(),
        )
        _make_queue_entry(db_session, user.id, paper.id)
        return user, paper

    def test_get_queue_returns_list(self, client, db_session):
        """GET /queue returns a list of queue items."""
        user, paper = self._setup_user_and_paper(db_session)
        response = client.get("/queue")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["paper_id"] == paper.id
        assert data[0]["title"] == "Test Paper"

    def test_get_queue_empty(self, client, db_session):
        """GET /queue with no entries returns empty list."""
        _make_user(db_session)
        response = client.get("/queue")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_queue_stats(self, client, db_session):
        """GET /queue/stats returns stats object."""
        user, _ = self._setup_user_and_paper(db_session)
        response = client.get("/queue/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total_unread"] == 1
        assert data["total_reading"] == 0
        assert data["total_read"] == 0
        assert data["total_skipped"] == 0
        assert "avg_priority" in data
        assert "estimated_reading_hours" in data

    def test_mark_as_read(self, client, db_session):
        """POST /queue/{paper_id}/read marks entry as read."""
        user, paper = self._setup_user_and_paper(db_session)
        response = client.post(f"/queue/{paper.id}/read")
        assert response.status_code == 200
        assert response.json()["message"] == "Marked as read"

        entry = (
            db_session.query(ReadingQueue)
            .filter(ReadingQueue.paper_id == paper.id)
            .first()
        )
        assert entry.read_status == "read"
        assert entry.read_at is not None

    def test_mark_as_reading(self, client, db_session):
        """POST /queue/{paper_id}/reading marks entry as reading."""
        user, paper = self._setup_user_and_paper(db_session)
        response = client.post(f"/queue/{paper.id}/reading")
        assert response.status_code == 200
        assert response.json()["message"] == "Marked as reading"

        entry = (
            db_session.query(ReadingQueue)
            .filter(ReadingQueue.paper_id == paper.id)
            .first()
        )
        assert entry.read_status == "reading"

    def test_mark_as_skipped(self, client, db_session):
        """POST /queue/{paper_id}/skip marks entry as skipped."""
        user, paper = self._setup_user_and_paper(db_session)
        response = client.post(f"/queue/{paper.id}/skip")
        assert response.status_code == 200
        assert response.json()["message"] == "Marked as skipped"

        entry = (
            db_session.query(ReadingQueue)
            .filter(ReadingQueue.paper_id == paper.id)
            .first()
        )
        assert entry.read_status == "skipped"

    def test_update_priority(self, client, db_session):
        """PATCH /queue/{paper_id}/priority updates manual priority."""
        user, paper = self._setup_user_and_paper(db_session)
        response = client.patch(
            f"/queue/{paper.id}/priority",
            json={"priority": 3},
        )
        assert response.status_code == 200

        entry = (
            db_session.query(ReadingQueue)
            .filter(ReadingQueue.paper_id == paper.id)
            .first()
        )
        assert entry.manual_priority == 3

    def test_update_priority_invalid(self, client, db_session):
        """PATCH /queue/{paper_id}/priority rejects invalid values."""
        user, paper = self._setup_user_and_paper(db_session)
        response = client.patch(
            f"/queue/{paper.id}/priority",
            json={"priority": 5},
        )
        assert response.status_code == 400

    def test_update_priority_null(self, client, db_session):
        """PATCH /queue/{paper_id}/priority accepts null (auto)."""
        user, paper = self._setup_user_and_paper(db_session)
        # First set a priority
        client.patch(
            f"/queue/{paper.id}/priority",
            json={"priority": 2},
        )
        # Then clear it
        response = client.patch(
            f"/queue/{paper.id}/priority",
            json={"priority": None},
        )
        assert response.status_code == 200

        entry = (
            db_session.query(ReadingQueue)
            .filter(ReadingQueue.paper_id == paper.id)
            .first()
        )
        assert entry.manual_priority is None

    def test_remove_from_queue(self, client, db_session):
        """DELETE /queue/{paper_id} removes entry."""
        user, paper = self._setup_user_and_paper(db_session)
        response = client.delete(f"/queue/{paper.id}")
        assert response.status_code == 200

        count = (
            db_session.query(ReadingQueue)
            .filter(ReadingQueue.paper_id == paper.id)
            .count()
        )
        assert count == 0

    def test_remove_nonexistent_returns_404(
        self, client, db_session
    ):
        """DELETE /queue/{paper_id} for missing entry returns 404."""
        _make_user(db_session)
        response = client.delete("/queue/99999")
        assert response.status_code == 404

    def test_mark_read_nonexistent_returns_404(
        self, client, db_session
    ):
        """POST /queue/{paper_id}/read for missing entry returns 404."""
        _make_user(db_session)
        response = client.post("/queue/99999/read")
        assert response.status_code == 404

    def test_rescore_endpoint(self, client, db_session):
        """POST /queue/rescore triggers sync + rescore."""
        user, paper = self._setup_user_and_paper(db_session)
        response = client.post("/queue/rescore")
        assert response.status_code == 200
        data = response.json()
        assert "rescored" in data
        assert "added" in data
        assert "removed" in data
        assert data["message"] == "Rescore complete"

    def test_get_queue_filter_by_status(
        self, client, db_session
    ):
        """GET /queue?status=unread filters correctly."""
        user = _make_user(db_session)
        p1 = _make_paper_row(
            db_session,
            arxiv_id="2401.00041",
            embedding=[0.5] * 768,
            published_date=datetime.utcnow(),
        )
        p2 = _make_paper_row(
            db_session,
            arxiv_id="2401.00042",
            embedding=[0.5] * 768,
            published_date=datetime.utcnow(),
        )
        _make_queue_entry(
            db_session, user.id, p1.id, read_status="unread"
        )
        _make_queue_entry(
            db_session, user.id, p2.id, read_status="read"
        )

        response = client.get("/queue?status=unread")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["read_status"] == "unread"

    def test_get_queue_filter_by_source(
        self, client, db_session
    ):
        """GET /queue?source=discovery filters correctly."""
        user = _make_user(db_session)
        p1 = _make_paper_row(
            db_session,
            arxiv_id="2401.00043",
            embedding=[0.5] * 768,
            published_date=datetime.utcnow(),
        )
        p2 = _make_paper_row(
            db_session,
            arxiv_id="2401.00044",
            embedding=[0.5] * 768,
            published_date=datetime.utcnow(),
        )
        _make_queue_entry(
            db_session, user.id, p1.id, source="bookmark"
        )
        _make_queue_entry(
            db_session, user.id, p2.id, source="discovery"
        )

        response = client.get("/queue?source=discovery")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["source"] == "discovery"


# ── Cold start: empty state ──────────────────────────


class TestColdStart:
    def test_empty_queue_returns_list(self, client, db_session):
        """GET /queue with no data returns empty list."""
        _make_user(db_session)
        response = client.get("/queue")
        assert response.status_code == 200
        assert response.json() == []

    def test_empty_stats_returns_zeros(self, client, db_session):
        """GET /queue/stats with no data returns all zeros."""
        _make_user(db_session)
        response = client.get("/queue/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total_unread"] == 0
        assert data["total_reading"] == 0
        assert data["total_read"] == 0
        assert data["total_skipped"] == 0
        assert data["discovery_unread"] == 0
        assert data["bookmark_unread"] == 0
        assert data["avg_priority"] == 0.0
        assert data["high_priority_count"] == 0
        assert data["estimated_reading_hours"] == 0.0

    def test_rescore_empty_queue(self, client, db_session):
        """POST /queue/rescore on empty queue succeeds."""
        _make_user(db_session)
        response = client.post("/queue/rescore")
        assert response.status_code == 200
        data = response.json()
        assert data["rescored"] == 0
        assert data["added"] == 0
        assert data["removed"] == 0

    def test_interest_vector_cold_start(self, db_session):
        """compute_user_interest_vector returns None on cold start."""
        _make_user(db_session)
        result = compute_user_interest_vector(
            db_session, user_id=1
        )
        assert result is None

    def test_sync_empty_library(self, db_session):
        """sync_queue_from_library with empty library returns (0, 0)."""
        _make_user(db_session)
        added, removed = sync_queue_from_library(
            db_session, user_id=1
        )
        assert added == 0
        assert removed == 0
