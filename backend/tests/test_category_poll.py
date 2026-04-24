"""Tests for the daily arXiv poller with per-category high-water mark."""

import datetime
from unittest.mock import MagicMock, patch

import pytest

from models import CategoryPollState, Paper
from services.arxiv_service import ArxivService


# ── CategoryPollState ORM ─────────────────────────────


class TestCategoryPollStateModel:
    def test_create_read_update(self, db_session):
        state = CategoryPollState(
            category="cs.AI",
            last_successful_submitted_date=datetime.date(2026, 4, 20),
            last_run_at=datetime.datetime(2026, 4, 24, 0, 0, 0),
            last_success_at=datetime.datetime(2026, 4, 24, 0, 1, 0),
            last_error=None,
        )
        db_session.add(state)
        db_session.commit()

        fetched = db_session.query(CategoryPollState).filter_by(
            category="cs.AI"
        ).first()
        assert fetched is not None
        assert fetched.last_successful_submitted_date == datetime.date(
            2026, 4, 20
        )
        assert fetched.last_error is None

        fetched.last_successful_submitted_date = datetime.date(2026, 4, 22)
        fetched.last_error = "transient failure"
        db_session.commit()

        reread = db_session.query(CategoryPollState).filter_by(
            category="cs.AI"
        ).first()
        assert reread.last_successful_submitted_date == datetime.date(
            2026, 4, 22
        )
        assert reread.last_error == "transient failure"

    def test_defaults_nullable(self, db_session):
        """All tracking columns are nullable — initial row is minimal."""
        state = CategoryPollState(category="cs.LG")
        db_session.add(state)
        db_session.commit()

        fetched = db_session.query(CategoryPollState).filter_by(
            category="cs.LG"
        ).first()
        assert fetched.last_successful_submitted_date is None
        assert fetched.last_run_at is None
        assert fetched.last_success_at is None
        assert fetched.last_error is None


# ── ArxivService.fetch_papers_since ───────────────────


class TestFetchPapersSince:
    def _make_result(self, arxiv_id: str, published: datetime.datetime):
        result = MagicMock()
        result.entry_id = f"http://arxiv.org/abs/{arxiv_id}"
        result.title = f"Paper {arxiv_id}"
        author = MagicMock()
        author.name = "Author One"
        result.authors = [author]
        result.summary = "Summary"
        result.published = published
        result.updated = published
        result.pdf_url = f"http://arxiv.org/pdf/{arxiv_id}"
        result.primary_category = "cs.AI"
        return result

    def test_query_string_uses_submitted_date_range(self):
        """Verify the query includes the submittedDate:[YYYYMMDD0000 TO *] form."""
        service = ArxivService()
        captured = {}

        def fake_results(search):
            captured["query"] = search.query
            captured["sort_by"] = search.sort_by
            captured["sort_order"] = search.sort_order
            return iter([])

        with patch.object(service.client, "results", side_effect=fake_results):
            list(
                service.fetch_papers_since(
                    category="cs.AI",
                    since_date=datetime.date(2026, 4, 20),
                )
            )

        assert "cat:cs.AI" in captured["query"]
        assert "submittedDate:[202604200000 TO *]" in captured["query"]
        import arxiv
        assert captured["sort_by"] == arxiv.SortCriterion.SubmittedDate
        assert captured["sort_order"] == arxiv.SortOrder.Ascending

    def test_is_generator_and_yields_expected_shape(self):
        service = ArxivService()
        published = datetime.datetime(2026, 4, 21, 12, 0, 0)
        results = [
            self._make_result("2604.0001", published),
            self._make_result("2604.0002", published),
        ]
        with patch.object(service.client, "results", return_value=iter(results)):
            gen = service.fetch_papers_since(
                category="cs.AI", since_date=datetime.date(2026, 4, 20)
            )
            # Generator — not a list
            assert not isinstance(gen, list)
            first = next(gen)
            assert first["arxiv_id"] == "2604.0001"
            assert first["title"] == "Paper 2604.0001"
            assert first["category"] == "cs.AI"
            assert first["published_date"] == published
            rest = list(gen)
            assert len(rest) == 1
            assert rest[0]["arxiv_id"] == "2604.0002"

    def test_safety_cap_halts_iteration(self):
        """safety_cap prevents runaway loops from malformed queries."""
        service = ArxivService()
        published = datetime.datetime(2026, 4, 21, 12, 0, 0)
        # 5 results, cap at 2 — we only get 2 back.
        results = [
            self._make_result(f"2604.{i:04d}", published) for i in range(5)
        ]
        with patch.object(service.client, "results", return_value=iter(results)):
            yielded = list(
                service.fetch_papers_since(
                    category="cs.AI",
                    since_date=datetime.date(2026, 4, 20),
                    safety_cap=2,
                )
            )
        assert len(yielded) == 2


# ── scheduler.process_papers ──────────────────────────


@pytest.fixture
def patched_scheduler(db_session):
    """Patch scheduler's DB sessionmaker + inject deterministic helpers.

    ``conftest.py`` stubs ``sys.modules['scheduler']`` with a MagicMock so
    that FastAPI's app startup doesn't kick off a real APScheduler during
    test collection. We pop that stub and import the real module here so
    ``process_papers`` is the real function under test, then restore the
    stub afterwards so other test files stay unaffected.
    """
    import importlib
    import sys

    stub = sys.modules.pop("scheduler", None)
    try:
        scheduler = importlib.import_module("scheduler")

        def _session():
            # process_papers calls db.close(); short-circuit so the shared
            # test session survives across asserts.
            db_session.close = lambda: None
            return db_session

        with patch.object(scheduler, "SessionLocal", side_effect=_session):
            yield scheduler
    finally:
        # Remove real module and restore the MagicMock stub so other tests
        # that rely on the conftest behaviour still see a mock.
        sys.modules.pop("scheduler", None)
        if stub is not None:
            sys.modules["scheduler"] = stub


def _make_paper_data(arxiv_id: str, submitted: datetime.date) -> dict:
    return {
        "arxiv_id": arxiv_id,
        "title": f"Paper {arxiv_id}",
        "authors": ["A"],
        "summary": "s",
        "published_date": datetime.datetime.combine(
            submitted, datetime.time(12, 0, 0)
        ),
        "updated_date": datetime.datetime.combine(
            submitted, datetime.time(12, 0, 0)
        ),
        "pdf_url": f"http://arxiv.org/pdf/{arxiv_id}",
        "category": "cs.AI",
    }


class TestProcessPapers:
    def test_initial_run_uses_14_day_window(self, patched_scheduler, db_session):
        """No existing state row → since = today - 14 days."""
        scheduler = patched_scheduler
        captured = {}

        def fake_fetch(category, since_date, safety_cap=50000):
            captured["category"] = category
            captured["since_date"] = since_date
            return iter([])

        with patch.object(
            scheduler, "_collect_categories", return_value={"cs.AI"}
        ), patch.object(
            scheduler.arxiv_service, "fetch_papers_since", side_effect=fake_fetch
        ):
            scheduler.process_papers()

        expected_since = datetime.date.today() - datetime.timedelta(days=14)
        assert captured["category"] == "cs.AI"
        assert captured["since_date"] == expected_since

    def test_existing_state_uses_hwm_minus_one_day(
        self, patched_scheduler, db_session
    ):
        scheduler = patched_scheduler
        db_session.add(CategoryPollState(
            category="cs.AI",
            last_successful_submitted_date=datetime.date(2026, 4, 20),
        ))
        db_session.commit()

        captured = {}

        def fake_fetch(category, since_date, safety_cap=50000):
            captured["since_date"] = since_date
            return iter([])

        with patch.object(
            scheduler, "_collect_categories", return_value={"cs.AI"}
        ), patch.object(
            scheduler.arxiv_service, "fetch_papers_since", side_effect=fake_fetch
        ):
            scheduler.process_papers()

        assert captured["since_date"] == datetime.date(2026, 4, 19)

    def test_success_advances_high_water_mark(
        self, patched_scheduler, db_session
    ):
        scheduler = patched_scheduler
        papers = [
            _make_paper_data("2604.0001", datetime.date(2026, 4, 21)),
            _make_paper_data("2604.0002", datetime.date(2026, 4, 23)),
            _make_paper_data("2604.0003", datetime.date(2026, 4, 22)),
        ]
        with patch.object(
            scheduler, "_collect_categories", return_value={"cs.AI"}
        ), patch.object(
            scheduler.arxiv_service,
            "fetch_papers_since",
            return_value=iter(papers),
        ):
            scheduler.process_papers()

        state = db_session.query(CategoryPollState).filter_by(
            category="cs.AI"
        ).first()
        assert state is not None
        assert state.last_successful_submitted_date == datetime.date(
            2026, 4, 23
        )
        assert state.last_error is None
        assert state.last_success_at is not None
        assert state.last_run_at is not None

        # And the papers got ingested.
        assert db_session.query(Paper).count() == 3

    def test_failure_preserves_high_water_mark(
        self, patched_scheduler, db_session
    ):
        scheduler = patched_scheduler
        db_session.add(CategoryPollState(
            category="cs.AI",
            last_successful_submitted_date=datetime.date(2026, 4, 20),
        ))
        db_session.commit()

        def raise_fetch(category, since_date, safety_cap=50000):
            raise RuntimeError("arxiv.org is down")

        with patch.object(
            scheduler, "_collect_categories", return_value={"cs.AI"}
        ), patch.object(
            scheduler.arxiv_service,
            "fetch_papers_since",
            side_effect=raise_fetch,
        ):
            scheduler.process_papers()

        state = db_session.query(CategoryPollState).filter_by(
            category="cs.AI"
        ).first()
        # HWM unchanged → next run retries the gap.
        assert state.last_successful_submitted_date == datetime.date(
            2026, 4, 20
        )
        assert state.last_error == "arxiv.org is down"
        assert state.last_run_at is not None

    def test_only_advances_when_new_max_greater(
        self, patched_scheduler, db_session
    ):
        """If fetched papers are all older than the stored HWM, HWM stays."""
        scheduler = patched_scheduler
        db_session.add(CategoryPollState(
            category="cs.AI",
            last_successful_submitted_date=datetime.date(2026, 4, 25),
        ))
        db_session.commit()
        papers = [
            _make_paper_data("2604.0001", datetime.date(2026, 4, 21)),
        ]
        with patch.object(
            scheduler, "_collect_categories", return_value={"cs.AI"}
        ), patch.object(
            scheduler.arxiv_service,
            "fetch_papers_since",
            return_value=iter(papers),
        ):
            scheduler.process_papers()

        state = db_session.query(CategoryPollState).filter_by(
            category="cs.AI"
        ).first()
        assert state.last_successful_submitted_date == datetime.date(
            2026, 4, 25
        )
