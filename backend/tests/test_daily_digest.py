"""Regression tests for the daily digest ingestion watermark (issue #50).

The old digest selected papers by ``func.date(published_date) == yesterday``
at a fixed 10:00 IST — an hour after the poll — so any paper ingested later
(slow arXiv API, 429 backoff, weekend announcements) was never included in
any digest. The fix selects by a Paper.id high-water mark persisted in the
last successful ``email_digest`` JobLog, advances it only on a confirmed
send, and runs the digest in the same wrapper as the poll.
"""

import datetime
from unittest.mock import MagicMock, patch

import pytest
import pytz

from models import JobLog, Paper


@pytest.fixture
def digest_scheduler(db_session):
    """Real scheduler module with its SessionLocal bound to the test DB.

    Mirrors ``patched_scheduler`` in test_category_poll.py: conftest stubs
    ``sys.modules['scheduler']`` with a MagicMock so app startup doesn't
    launch APScheduler; we pop the stub, import the real module, restore
    the stub afterwards.
    """
    import importlib
    import sys

    stub = sys.modules.pop("scheduler", None)
    try:
        scheduler = importlib.import_module("scheduler")

        def _session():
            # The digest calls db.close(); short-circuit so the shared
            # test session survives across asserts.
            db_session.close = lambda: None
            return db_session

        with patch.object(scheduler, "SessionLocal", side_effect=_session):
            with patch.object(
                scheduler.settings, "EMAIL_RECIPIENTS", "reader@example.com"
            ):
                yield scheduler
    finally:
        sys.modules.pop("scheduler", None)
        if stub is not None:
            sys.modules["scheduler"] = stub


def _make_paper(db_session, arxiv_id, published, category="cs.AI"):
    paper = Paper(
        arxiv_id=arxiv_id,
        title=f"Paper {arxiv_id}",
        authors=["Author"],
        summary="Summary",
        published_date=published,
        updated_date=published,
        category=category,
        pdf_url=f"http://arxiv.org/pdf/{arxiv_id}",
    )
    db_session.add(paper)
    db_session.commit()
    return paper


def _seed_digest_log(db_session, max_paper_id):
    """A prior SUCCESSFUL digest that sent everything up to max_paper_id."""
    entry = JobLog(
        job_name="email_digest",
        status="SUCCESS",
        start_time=datetime.datetime.utcnow(),
        end_time=datetime.datetime.utcnow(),
        job_details={"mode": "watermark", "count": 1, "max_paper_id": max_paper_id},
    )
    db_session.add(entry)
    db_session.commit()
    return entry


def _sent_paper_ids(send_mock):
    """Paper ids passed to the (single-recipient) digest send, in order."""
    return [
        [p.id for p in call.args[1]]
        for call in send_mock.call_args_list
    ]


@pytest.fixture
def send_digest_ok(digest_scheduler):
    """Patch EmailService.send_daily_digest to a confirmed send."""
    with patch.object(
        digest_scheduler.email_service,
        "send_daily_digest",
        MagicMock(return_value=(True, "ok")),
    ) as send_mock:
        yield send_mock


# ── selection by watermark ────────────────────────────


class TestWatermarkSelection:
    def test_late_ingested_paper_with_old_published_date_is_included(
        self, digest_scheduler, db_session, send_digest_ok
    ):
        """The bug in #50: a paper ingested after its submission date is
        no longer 'yesterday' — it must still reach the next digest."""
        _seed_digest_log(db_session, max_paper_id=1)
        published_3_days_ago = datetime.datetime.utcnow() - datetime.timedelta(
            days=3
        )
        # Both within the 7-day window; they differ only in ingestion id.
        _make_paper(db_session, "2609.0001", published_3_days_ago)
        late_paper = _make_paper(db_session, "2609.0002", published_3_days_ago)

        digest_scheduler.send_daily_email_digest()

        assert _sent_paper_ids(send_digest_ok) == [[late_paper.id]]

    def test_already_sent_paper_is_not_resent(
        self, digest_scheduler, db_session, send_digest_ok
    ):
        _seed_digest_log(db_session, max_paper_id=2)
        yesterday = datetime.datetime.utcnow() - datetime.timedelta(days=1)
        _make_paper(db_session, "2609.0001", yesterday)
        _make_paper(db_session, "2609.0002", yesterday)

        digest_scheduler.send_daily_email_digest()

        assert _sent_paper_ids(send_digest_ok) == []
        log = (
            db_session.query(JobLog)
            .filter_by(job_name="email_digest")
            .order_by(JobLog.id.desc())
            .first()
        )
        assert log.status == "SUCCESS"
        assert log.job_details["count"] == 0

    def test_paper_older_than_7_days_is_excluded(
        self, digest_scheduler, db_session, send_digest_ok
    ):
        """The age bound keeps a historical backfill from flooding one
        digest, even though the paper was never sent (id > watermark)."""
        _seed_digest_log(db_session, max_paper_id=1)
        ancient = datetime.datetime.utcnow() - datetime.timedelta(days=8)
        _make_paper(db_session, "2609.0001", ancient)

        digest_scheduler.send_daily_email_digest()

        assert _sent_paper_ids(send_digest_ok) == []


# ── bootstrap (no prior digest) ───────────────────────


class TestBootstrap:
    def test_bootstrap_falls_back_to_yesterday_and_records_watermark(
        self, digest_scheduler, db_session, send_digest_ok
    ):
        """No prior watermark → legacy behaviour (published yesterday IST)
        for that one run, and the watermark is recorded from the rows
        actually selected."""
        ist = pytz.timezone("Asia/Kolkata")
        yesterday_ist = (
            datetime.datetime.now(ist).date() - datetime.timedelta(days=1)
        )
        yesterday_paper = _make_paper(
            db_session,
            "2609.0001",
            datetime.datetime.combine(yesterday_ist, datetime.time(12, 0)),
        )
        # Published 5 days ago: never ingested-before, but outside the
        # legacy yesterday window — must NOT ride along in bootstrap.
        _make_paper(
            db_session,
            "2609.0002",
            datetime.datetime.utcnow() - datetime.timedelta(days=5),
        )

        digest_scheduler.send_daily_email_digest()

        assert _sent_paper_ids(send_digest_ok) == [[yesterday_paper.id]]
        log = (
            db_session.query(JobLog)
            .filter_by(job_name="email_digest")
            .order_by(JobLog.id.desc())
            .first()
        )
        assert log.status == "SUCCESS"
        assert log.job_details["mode"] == "bootstrap"
        assert log.job_details["max_paper_id"] == yesterday_paper.id

    def test_bootstrap_watermark_is_used_by_next_run(
        self, digest_scheduler, db_session, send_digest_ok
    ):
        """After the bootstrap run records its watermark, the next run
        switches to ingestion-order selection (no re-send)."""
        ist = pytz.timezone("Asia/Kolkata")
        yesterday_ist = (
            datetime.datetime.now(ist).date() - datetime.timedelta(days=1)
        )
        paper = _make_paper(
            db_session,
            "2609.0001",
            datetime.datetime.combine(yesterday_ist, datetime.time(12, 0)),
        )

        digest_scheduler.send_daily_email_digest()
        digest_scheduler.send_daily_email_digest()

        # First run sends yesterday's paper; the second run (now on the
        # recorded watermark) selects nothing and sends no email at all.
        assert _sent_paper_ids(send_digest_ok) == [[paper.id]]
        second_log = (
            db_session.query(JobLog)
            .filter_by(job_name="email_digest")
            .order_by(JobLog.id.desc())
            .first()
        )
        assert second_log.status == "SUCCESS"
        assert second_log.job_details["mode"] == "watermark"
        assert second_log.job_details["count"] == 0


# ── watermark advances only on confirmed send ─────────


class TestWatermarkOnSendFailure:
    def test_failed_send_marks_job_failed_and_next_run_retries(
        self, digest_scheduler, db_session
    ):
        # Watermark 0 = nothing ever sent, so the fresh paper (id 1) is
        # inside the selection window.
        _seed_digest_log(db_session, max_paper_id=0)
        published_3_days_ago = datetime.datetime.utcnow() - datetime.timedelta(
            days=3
        )
        paper = _make_paper(db_session, "2609.0002", published_3_days_ago)

        with patch.object(
            digest_scheduler.email_service,
            "send_daily_digest",
            MagicMock(return_value=(False, "resend 500")),
        ) as failing_send:
            digest_scheduler.send_daily_email_digest()

        log = (
            db_session.query(JobLog)
            .filter_by(job_name="email_digest")
            .order_by(JobLog.id.desc())
            .first()
        )
        assert log.status == "FAILED"
        assert "resend 500" in log.error_message
        assert log.job_details["watermark_advanced"] is False
        assert failing_send.called

        # Next run: no SUCCESS row recorded the paper, so it retries.
        with patch.object(
            digest_scheduler.email_service,
            "send_daily_digest",
            MagicMock(return_value=(True, "ok")),
        ) as retry_send:
            digest_scheduler.send_daily_email_digest()

        assert _sent_paper_ids(retry_send) == [[paper.id]]

    def test_partial_recipient_failure_does_not_advance_watermark(
        self, digest_scheduler, db_session, send_digest_ok
    ):
        """Any unconfirmed recipient fails the job — a partial delivery
        must not silently drop the papers for the recipient that missed
        out (at-least-once: they may get a duplicate next run)."""
        # Watermark 0 = nothing ever sent, so the fresh paper (id 1) is
        # inside the selection window.
        _seed_digest_log(db_session, max_paper_id=0)
        published_3_days_ago = datetime.datetime.utcnow() - datetime.timedelta(
            days=3
        )
        _make_paper(db_session, "2609.0002", published_3_days_ago)
        send_digest_ok.side_effect = [
            (True, "ok"),
            (False, "resend rate limited"),
        ]

        with patch.object(
            digest_scheduler.settings, "EMAIL_RECIPIENTS", "a@x.com, b@x.com"
        ):
            digest_scheduler.send_daily_email_digest()

        log = (
            db_session.query(JobLog)
            .filter_by(job_name="email_digest")
            .order_by(JobLog.id.desc())
            .first()
        )
        assert log.status == "FAILED"
        assert "b@x.com" in log.error_message
        assert log.job_details["watermark_advanced"] is False


# ── poll + digest wrapper ─────────────────────────────


class TestPollAndDigestWrapper:
    def test_wrapper_runs_digest_after_poll(self, digest_scheduler):
        order = []
        with patch.object(
            digest_scheduler,
            "process_papers",
            side_effect=lambda: order.append("poll"),
        ), patch.object(
            digest_scheduler,
            "send_daily_email_digest",
            side_effect=lambda: order.append("digest"),
        ):
            digest_scheduler.run_daily_poll_and_digest()

        assert order == ["poll", "digest"]

    def test_wrapper_runs_digest_even_when_poll_raises(self, digest_scheduler):
        with patch.object(
            digest_scheduler,
            "process_papers",
            side_effect=RuntimeError("arxiv.org is down"),
        ) as poll, patch.object(
            digest_scheduler, "send_daily_email_digest"
        ) as digest:
            digest_scheduler.run_daily_poll_and_digest()

        poll.assert_called_once()
        digest.assert_called_once()
