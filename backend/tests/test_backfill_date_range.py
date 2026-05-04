"""Tests for the date-range backfill script.

Focus on the per-day vs bulk control flow — that the right ``since/until``
pairs reach ``fetch_papers_since`` for each mode. Real ingestion is mocked
out via ``process_paper_entry`` and ``SessionLocal``.
"""

import datetime
from unittest.mock import MagicMock, patch

import pytest


def _import_backfill():
    """Import the script module bypassing conftest's scheduler MagicMock if any."""
    import importlib
    import sys
    sys.modules.pop("scripts.backfill_date_range", None)
    return importlib.import_module("scripts.backfill_date_range")


@pytest.fixture(autouse=True)
def _mock_session():
    """Stub SessionLocal so backfill() doesn't try to open a real DB."""
    fake_session = MagicMock()
    with patch(
        "scripts.backfill_date_range.SessionLocal",
        return_value=fake_session,
    ):
        yield fake_session


def test_per_day_mode_issues_one_query_per_day_per_category():
    mod = _import_backfill()
    captured = []

    def fake_fetch(category, since_date, until_date, **kw):
        captured.append((category, since_date, until_date))
        return iter([])

    with patch.object(
        mod.arxiv_service, "fetch_papers_since", side_effect=fake_fetch
    ):
        mod.backfill(
            start=datetime.date(2026, 5, 1),
            end=datetime.date(2026, 5, 3),
            categories=["cs.AI", "cs.LG"],
            per_day=True,
        )

    # 3 days × 2 categories = 6 queries.
    assert len(captured) == 6
    # Per-day mode: since == until on every call.
    for cat, since, until in captured:
        assert since == until

    # Days iterate newest → oldest.
    days_in_order = [s for _, s, _ in captured]
    assert days_in_order[0] == datetime.date(2026, 5, 3)
    assert days_in_order[-1] == datetime.date(2026, 5, 1)


def test_bulk_mode_issues_one_query_per_category():
    mod = _import_backfill()
    captured = []

    def fake_fetch(category, since_date, until_date, **kw):
        captured.append((category, since_date, until_date))
        return iter([])

    with patch.object(
        mod.arxiv_service, "fetch_papers_since", side_effect=fake_fetch
    ):
        mod.backfill(
            start=datetime.date(2026, 5, 1),
            end=datetime.date(2026, 5, 3),
            categories=["cs.AI", "cs.LG"],
            per_day=False,
        )

    # Bulk: one query per category, full range.
    assert len(captured) == 2
    for _cat, since, until in captured:
        assert since == datetime.date(2026, 5, 1)
        assert until == datetime.date(2026, 5, 3)


def test_iter_dates_descending_inclusive():
    mod = _import_backfill()
    dates = mod._iter_dates(
        datetime.date(2026, 5, 1),
        datetime.date(2026, 5, 3),
        descending=True,
    )
    assert dates == [
        datetime.date(2026, 5, 3),
        datetime.date(2026, 5, 2),
        datetime.date(2026, 5, 1),
    ]


def test_iter_dates_single_day():
    mod = _import_backfill()
    dates = mod._iter_dates(
        datetime.date(2026, 5, 1),
        datetime.date(2026, 5, 1),
    )
    assert dates == [datetime.date(2026, 5, 1)]


def test_per_day_aggregates_across_days():
    """Per-day mode must accumulate per-category counts across days, not reset."""
    mod = _import_backfill()

    def fake_fetch(category, since_date, until_date, **kw):
        # Yield 2 papers per (category, day).
        return iter([
            {"arxiv_id": f"{category}-{since_date}-1"},
            {"arxiv_id": f"{category}-{since_date}-2"},
        ])

    with patch.object(
        mod.arxiv_service, "fetch_papers_since", side_effect=fake_fetch
    ), patch.object(
        mod, "process_paper_entry", return_value=True
    ):
        result = mod.backfill(
            start=datetime.date(2026, 5, 1),
            end=datetime.date(2026, 5, 3),
            categories=["cs.AI"],
            per_day=True,
        )

    # 1 category × 3 days × 2 papers = 6 each.
    assert result["categories"]["cs.AI"]["new"] == 6
    assert result["categories"]["cs.AI"]["seen"] == 6
    assert result["total_new"] == 6
    assert result["total_seen"] == 6
