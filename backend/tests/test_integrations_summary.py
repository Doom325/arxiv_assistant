"""Tests for the summarization state machine in routers/integrations.py.

Covers the move from the legacy ``__ERROR__`` sentinel in
``papers.generated_summary`` to dedicated
``summary_status`` / ``summary_error`` / ``summary_attempted_at`` columns.
"""

from datetime import date, datetime, timezone
from unittest.mock import patch

import pytest

from models import Paper
from routers import integrations


@pytest.fixture
def sample_paper(db_session):
    paper = Paper(
        arxiv_id="9999.0001",
        title="A Test Paper",
        authors=["Author A"],
        summary="Upstream abstract",
        published_date=date(2025, 1, 1),
        category="cs.AI",
        pdf_url="http://example.com/pdf",
        embedding=[0.1] * 768,
    )
    db_session.add(paper)
    db_session.commit()
    db_session.refresh(paper)
    return paper


def _patch_session_local(db_session):
    """Point ``integrations.SessionLocal()`` at the test DB session.

    The production helper closes the session in a finally block, so we hand
    out a non-closing shim so the outer test fixture can still assert state
    after the background function returns.
    """

    class _SessionShim:
        def __init__(self, session):
            self._session = session

        def __getattr__(self, name):
            return getattr(self._session, name)

        def close(self):
            # no-op; db_session fixture owns the real lifecycle
            return None

    return patch.object(
        integrations,
        "SessionLocal",
        lambda: _SessionShim(db_session),
    )


class TestRunSummarizationFailures:
    def test_pdf_download_failure_populates_error_columns(
        self, db_session, sample_paper, tmp_path
    ):
        """PDF-download failure must set summary_status='failed' and populate
        summary_error without touching generated_summary."""
        with patch.object(integrations.settings, "PDF_SAVE_DIR", str(tmp_path)), \
             patch.object(
                 integrations.arxiv_service,
                 "download_pdf",
                 side_effect=RuntimeError("network boom"),
             ), \
             _patch_session_local(db_session):
            integrations.run_summarization(sample_paper.id, sample_paper.pdf_url)

        db_session.expire_all()
        refreshed = db_session.query(Paper).filter(Paper.id == sample_paper.id).one()
        assert refreshed.summary_status == "failed"
        assert refreshed.generated_summary is None
        assert isinstance(refreshed.summary_error, dict)
        assert refreshed.summary_error["code"] == "pdf_download_failed"
        assert "network boom" in refreshed.summary_error["message"]
        assert refreshed.summary_error["attempt_count"] == 1
        assert refreshed.summary_attempted_at is not None

    def test_llm_failure_populates_error_columns(
        self, db_session, sample_paper, tmp_path
    ):
        """Pre-existing PDF + failing LLM must record 'summarization_failed'."""
        # Pre-create the PDF so the download path is skipped.
        pdf_path = tmp_path / f"{sample_paper.arxiv_id}.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 test")

        with patch.object(integrations.settings, "PDF_SAVE_DIR", str(tmp_path)), \
             patch.object(
                 integrations.summarization_service,
                 "generate_summary",
                 side_effect=RuntimeError("context too small"),
             ), \
             _patch_session_local(db_session):
            integrations.run_summarization(sample_paper.id, sample_paper.pdf_url)

        db_session.expire_all()
        refreshed = db_session.query(Paper).filter(Paper.id == sample_paper.id).one()
        assert refreshed.summary_status == "failed"
        assert refreshed.generated_summary is None
        assert refreshed.summary_error["code"] == "summarization_failed"
        assert "context too small" in refreshed.summary_error["message"]
        assert refreshed.summary_attempted_at is not None


class TestRunSummarizationSuccess:
    def test_success_clears_error_and_populates_summary(
        self, db_session, sample_paper, tmp_path
    ):
        """On success, generated_summary is written, status='succeeded',
        and any prior summary_error is cleared."""
        # Seed a prior failed attempt to ensure it gets cleared on success.
        sample_paper.summary_status = "failed"
        sample_paper.summary_error = {
            "code": "summarization_failed",
            "message": "prior failure",
            "attempted_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
            "attempt_count": 1,
        }
        db_session.commit()

        pdf_path = tmp_path / f"{sample_paper.arxiv_id}.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 test")

        expected_summary = "A clean, successful summary of the paper."
        with patch.object(integrations.settings, "PDF_SAVE_DIR", str(tmp_path)), \
             patch.object(
                 integrations.summarization_service,
                 "generate_summary",
                 return_value=expected_summary,
             ), \
             _patch_session_local(db_session):
            integrations.run_summarization(sample_paper.id, sample_paper.pdf_url)

        db_session.expire_all()
        refreshed = db_session.query(Paper).filter(Paper.id == sample_paper.id).one()
        assert refreshed.summary_status == "succeeded"
        assert refreshed.generated_summary == expected_summary
        assert refreshed.summary_error is None
        assert refreshed.summary_attempted_at is not None


class TestSummarizePaperEndpoint:
    def test_retry_after_failure_without_force(
        self, client, db_session, sample_paper
    ):
        """A previously-failed paper must be retry-eligible without
        ``force=True``. The endpoint should schedule the task and reset the
        status to 'pending'."""
        sample_paper.summary_status = "failed"
        sample_paper.summary_error = {
            "code": "summarization_failed",
            "message": "prior failure",
            "attempted_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
            "attempt_count": 1,
        }
        sample_paper.generated_summary = None
        db_session.commit()

        response = client.post(f"/papers/{sample_paper.id}/summarize")
        assert response.status_code == 200
        assert response.json()["message"] == "Summarization started"

        db_session.expire_all()
        refreshed = db_session.query(Paper).filter(Paper.id == sample_paper.id).one()
        assert refreshed.summary_status == "pending"
        assert refreshed.summary_error is None

    def test_success_short_circuits_without_force(
        self, client, db_session, sample_paper
    ):
        """If a paper already has a successful summary, the endpoint returns
        it directly without scheduling another run."""
        sample_paper.generated_summary = "existing summary"
        sample_paper.summary_status = "succeeded"
        db_session.commit()

        response = client.post(f"/papers/{sample_paper.id}/summarize")
        assert response.status_code == 200
        body = response.json()
        assert body["message"] == "Summary already exists"
        assert body["summary"] == "existing summary"

    def test_force_retries_even_with_existing_summary(
        self, client, db_session, sample_paper
    ):
        """``force=True`` re-runs even when a successful summary exists."""
        sample_paper.generated_summary = "existing summary"
        sample_paper.summary_status = "succeeded"
        db_session.commit()

        response = client.post(
            f"/papers/{sample_paper.id}/summarize?force=true"
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Summarization started"

        db_session.expire_all()
        refreshed = db_session.query(Paper).filter(Paper.id == sample_paper.id).one()
        assert refreshed.summary_status == "pending"


class TestModelSelection:
    def test_list_models_endpoint(self, client):
        """GET /models/summarization returns the cross-provider list, default, and default_provider."""
        with patch.object(
            integrations,
            "list_all_summarization_models",
            return_value=[
                {"id": "gemini-3-flash-preview", "provider": "gemini"},
                {"id": "gemma3:27b", "provider": "local"},
            ],
        ):
            response = client.get("/models/summarization")
        assert response.status_code == 200
        body = response.json()
        assert body["models"] == [
            {"id": "gemini-3-flash-preview", "provider": "gemini"},
            {"id": "gemma3:27b", "provider": "local"},
        ]
        assert "default_provider" in body
        assert "default" in body

    def test_unknown_model_rejected(self, client, db_session, sample_paper):
        """Unknown model values must be rejected with 400, not silently forwarded."""
        with patch.object(
            integrations,
            "list_all_summarization_models",
            return_value=[{"id": "model-a", "provider": "local"}],
        ):
            response = client.post(
                f"/papers/{sample_paper.id}/summarize?model=evil-model"
            )
        assert response.status_code == 400
        assert "Unknown model" in response.json()["detail"]

    def test_known_model_accepted_and_threaded(self, client, db_session, sample_paper, tmp_path):
        """A model on the allowlist reaches summarize_text via generate_summary."""
        pdf_path = tmp_path / f"{sample_paper.arxiv_id}.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 test")

        with patch.object(integrations.settings, "PDF_SAVE_DIR", str(tmp_path)), \
             patch.object(
                 integrations,
                 "list_all_summarization_models",
                 return_value=[
                     {"id": "model-a", "provider": "local"},
                     {"id": "model-b", "provider": "local"},
                 ],
             ), \
             patch.object(
                 integrations.summarization_service,
                 "generate_summary",
                 return_value="ok",
             ) as mock_gen, \
             _patch_session_local(db_session):
            response = client.post(
                f"/papers/{sample_paper.id}/summarize?force=true&model=model-b"
            )
            assert response.status_code == 200
            mock_gen.assert_called_once()
            assert mock_gen.call_args.kwargs["model"] == "model-b"



    def test_temperature_threaded_to_generate_summary(self, client, db_session, sample_paper, tmp_path):
        """A user-supplied temperature must reach summarization_service.generate_summary."""
        pdf_path = tmp_path / f"{sample_paper.arxiv_id}.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 test")

        with patch.object(integrations.settings, "PDF_SAVE_DIR", str(tmp_path)), \
             patch.object(
                 integrations,
                 "list_all_summarization_models",
                 return_value=[{"id": "model-a", "provider": "local"}],
             ), \
             patch.object(
                 integrations.summarization_service,
                 "generate_summary",
                 return_value="ok",
             ) as mock_gen, \
             _patch_session_local(db_session):
            response = client.post(
                f"/papers/{sample_paper.id}/summarize?force=true&model=model-a&temperature=0.7"
            )
            assert response.status_code == 200
            assert response.json()["temperature"] == 0.7
            mock_gen.assert_called_once()
            assert mock_gen.call_args.kwargs["temperature"] == 0.7

    def test_temperature_out_of_range_rejected(self, client, db_session, sample_paper):
        """temperature outside [0, 2] must be 400."""
        response = client.post(
            f"/papers/{sample_paper.id}/summarize?force=true&temperature=3.5"
        )
        assert response.status_code == 400
        assert "temperature must be in" in response.json()["detail"]
