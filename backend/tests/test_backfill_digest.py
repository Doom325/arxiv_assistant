"""Tests for scripts/email/backfill_digest.py (catch-up digests after #50)."""

import datetime
import importlib.util
import os
import types
from unittest.mock import patch

import pytest

from models import JobLog, Paper
from services.email_service import email_service

_SCRIPT = os.path.join(
    os.path.dirname(__file__), "..", "scripts", "email", "backfill_digest.py"
)


@pytest.fixture
def bf():
    spec = importlib.util.spec_from_file_location("backfill_digest", _SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


DAY = datetime.date(2026, 9, 28)


def _paper(db_session, arxiv_id, day=DAY, category="cs.AI"):
    p = Paper(
        arxiv_id=arxiv_id,
        title=f"Paper {arxiv_id}",
        authors=["A"],
        summary="First sentence. Second sentence.",
        published_date=datetime.datetime.combine(day, datetime.time(12)),
        category=category,
        pdf_url=f"http://arxiv.org/pdf/{arxiv_id}",
    )
    db_session.add(p)
    db_session.commit()
    return p


def test_selects_cs_ai_on_day_at_or_below_watermark(bf, db_session):
    keep = _paper(db_session, "2609.1")
    _paper(db_session, "2609.2", category="cs.LG")
    _paper(db_session, "2609.3", day=DAY - datetime.timedelta(days=1))
    above = _paper(db_session, "2609.4")

    got = bf.papers_for_day(db_session, DAY, max_paper_id=above.id - 1)

    assert [p.id for p in got] == [keep.id]


def test_send_logs_day_and_rerun_skips_it(bf, db_session):
    p = _paper(db_session, "2609.1")
    with patch.object(bf.settings, "EMAIL_RECIPIENTS", "reader@example.com"), \
         patch.object(bf.email_service, "send_catchup_digest", return_value=(True, "ok")) as send:
        assert bf.run(DAY, DAY, p.id, send=True, db=db_session) == 0
        assert bf.run(DAY, DAY, p.id, send=True, db=db_session) == 0

    assert send.call_count == 1
    log = db_session.query(JobLog).filter_by(job_name="email_digest_backfill").one()
    assert log.status == "SUCCESS" and log.job_details["date"] == DAY.isoformat()


def test_failed_send_is_retried_on_rerun(bf, db_session):
    p = _paper(db_session, "2609.1")
    with patch.object(bf.settings, "EMAIL_RECIPIENTS", "reader@example.com"), \
         patch.object(bf.email_service, "send_catchup_digest", side_effect=[(False, "boom"), (True, "ok")]) as send:
        assert bf.run(DAY, DAY, p.id, send=True, db=db_session) == 1
        assert bf.run(DAY, DAY, p.id, send=True, db=db_session) == 0
    assert send.call_count == 2


def test_dry_run_sends_nothing(bf, db_session):
    p = _paper(db_session, "2609.1")
    with patch.object(bf.email_service, "send_catchup_digest") as send:
        assert bf.run(DAY, DAY, p.id, send=False, db=db_session) == 0
    send.assert_not_called()
    assert db_session.query(JobLog).count() == 0


def test_seed_watermark_records_max_id_as_digest_success(bf, db_session):
    _paper(db_session, "2609.1")
    top = _paper(db_session, "2609.2")

    assert bf.seed_watermark(db_session) == top.id

    log = db_session.query(JobLog).filter_by(job_name="email_digest").one()
    assert log.status == "SUCCESS" and log.job_details["max_paper_id"] == top.id


def test_large_day_splits_into_parts(bf):
    assert [len(c) for c in bf.chunks(list(range(600)))] == [250, 250, 100]


def test_compact_email_fits_gmail_clip_limit():
    long_title = "Scaling Test-Time Compute for Agentic Reasoning with Verifier-Guided Search"
    papers = [
        types.SimpleNamespace(
            id=i, arxiv_id=f"2609.{i:05d}", title=long_title,
            summary="A long first sentence about the method and its results. " * 3,
            pdf_url=f"http://arxiv.org/pdf/2609.{i:05d}v1",
        )
        for i in range(250)
    ]
    html = email_service._generate_compact_html(papers, "arXiv cs.AI catch-up")
    assert len(html.encode()) < 102 * 1024
