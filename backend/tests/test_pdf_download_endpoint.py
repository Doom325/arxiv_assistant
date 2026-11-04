"""Tests for the on-demand PDF download endpoint and the ``pdf_available`` flag.

Covers:
- ``pdf_available`` on the single-paper detail response (true/false), and that
  the list endpoint does NOT compute it (no per-row filesystem hit).
- ``POST /papers/{id}/pdf/download``: idempotent "already available", a fresh
  download, and structured errors for disk full (507) and upstream failure
  (502), plus id resolution by arXiv id and a 404 for an unknown paper.
"""

import os
from datetime import datetime

from unittest.mock import patch

from core.pdf_utils import PdfDownloadError
from models import Paper
from routers import papers


def _make_paper(db_session, arxiv_id: str = "2401.00001") -> Paper:
    paper = Paper(
        arxiv_id=arxiv_id,
        title="A Test Paper",
        authors=["Author A"],
        summary="abstract",
        published_date=datetime(2025, 1, 1),
        category="cs.AI",
        pdf_url=f"http://arxiv.org/pdf/{arxiv_id}",
        embedding=[0.1] * 768,
    )
    db_session.add(paper)
    db_session.commit()
    db_session.refresh(paper)
    return paper


def _write_pdf(tmp_path, arxiv_id: str, body: bytes = b"%PDF-1.4 ok") -> str:
    path = tmp_path / f"{arxiv_id}.pdf"
    path.write_bytes(body)
    return str(path)


class TestPdfAvailableFlag:
    def test_detail_reports_false_when_absent(self, client, db_session, tmp_path):
        paper = _make_paper(db_session)
        with patch.object(papers.settings, "PDF_SAVE_DIR", str(tmp_path)):
            resp = client.get(f"/papers/{paper.id}")
        assert resp.status_code == 200
        assert resp.json()["pdf_available"] is False

    def test_detail_reports_true_when_present(self, client, db_session, tmp_path):
        paper = _make_paper(db_session)
        _write_pdf(tmp_path, paper.arxiv_id)
        with patch.object(papers.settings, "PDF_SAVE_DIR", str(tmp_path)):
            resp = client.get(f"/papers/{paper.id}")
        assert resp.status_code == 200
        assert resp.json()["pdf_available"] is True

    def test_detail_zero_byte_pdf_reports_false(self, client, db_session, tmp_path):
        """A 0-byte stub must read as unavailable (disk-full incident)."""
        paper = _make_paper(db_session)
        _write_pdf(tmp_path, paper.arxiv_id, body=b"")
        with patch.object(papers.settings, "PDF_SAVE_DIR", str(tmp_path)):
            resp = client.get(f"/papers/{paper.id}")
        assert resp.json()["pdf_available"] is False

    def test_list_does_not_compute_pdf_available(self, client, db_session, tmp_path):
        paper = _make_paper(db_session)
        _write_pdf(tmp_path, paper.arxiv_id)
        with patch.object(papers.settings, "PDF_SAVE_DIR", str(tmp_path)):
            resp = client.get("/papers/")
        assert resp.status_code == 200
        # The list endpoint must stay free of per-row filesystem hits, so the
        # field is left unset (null) there even though the file exists on disk.
        assert all(item["pdf_available"] is None for item in resp.json())


class TestDownloadEndpoint:
    def test_already_available_is_idempotent(self, client, db_session, tmp_path):
        paper = _make_paper(db_session)
        _write_pdf(tmp_path, paper.arxiv_id)
        with patch.object(papers.settings, "PDF_SAVE_DIR", str(tmp_path)), \
             patch.object(papers, "download_pdf_strict") as mock_dl:
            resp = client.post(f"/papers/{paper.id}/pdf/download")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "available"
        assert body["pdf_available"] is True
        mock_dl.assert_not_called()

    def test_download_when_missing(self, client, db_session, tmp_path):
        paper = _make_paper(db_session)

        def fake_download(url, arxiv_id, pdf_dir, **kwargs):
            path = os.path.join(pdf_dir, f"{arxiv_id}.pdf")
            with open(path, "wb") as f:
                f.write(b"%PDF-1.4 fetched")
            return path

        with patch.object(papers.settings, "PDF_SAVE_DIR", str(tmp_path)), \
             patch.object(
                 papers, "download_pdf_strict", side_effect=fake_download
             ) as mock_dl:
            resp = client.post(f"/papers/{paper.id}/pdf/download")
        assert resp.status_code == 200
        assert resp.json()["status"] == "downloaded"
        mock_dl.assert_called_once()
        assert os.path.exists(os.path.join(tmp_path, f"{paper.arxiv_id}.pdf"))

    def test_disk_full_returns_507(self, client, db_session, tmp_path):
        paper = _make_paper(db_session)
        with patch.object(papers.settings, "PDF_SAVE_DIR", str(tmp_path)), \
             patch.object(
                 papers,
                 "download_pdf_strict",
                 side_effect=PdfDownloadError(
                     "No space left on the PDF storage volume.",
                     code="pdf_disk_full",
                     retryable=False,
                 ),
             ):
            resp = client.post(f"/papers/{paper.id}/pdf/download")
        assert resp.status_code == 507
        detail = resp.json()["detail"]
        assert detail["code"] == "pdf_disk_full"
        assert detail["retryable"] is False
        assert "No space left" in detail["message"]

    def test_upstream_429_returns_502(self, client, db_session, tmp_path):
        paper = _make_paper(db_session)
        with patch.object(papers.settings, "PDF_SAVE_DIR", str(tmp_path)), \
             patch.object(
                 papers,
                 "download_pdf_strict",
                 side_effect=PdfDownloadError(
                     "arXiv returned HTTP 429 while downloading the PDF.",
                     code="pdf_http_error",
                     retryable=True,
                     http_status=429,
                 ),
             ):
            resp = client.post(f"/papers/{paper.id}/pdf/download")
        assert resp.status_code == 502
        detail = resp.json()["detail"]
        assert detail["code"] == "pdf_http_error"
        assert detail["retryable"] is True
        assert detail["http_status"] == 429

    def test_unknown_paper_returns_404(self, client, db_session, tmp_path):
        with patch.object(papers.settings, "PDF_SAVE_DIR", str(tmp_path)):
            resp = client.post("/papers/99999/pdf/download")
        assert resp.status_code == 404

    def test_resolves_by_arxiv_id(self, client, db_session, tmp_path):
        paper = _make_paper(db_session, arxiv_id="2402.54321")
        _write_pdf(tmp_path, paper.arxiv_id)
        with patch.object(papers.settings, "PDF_SAVE_DIR", str(tmp_path)):
            resp = client.post(f"/papers/{paper.arxiv_id}/pdf/download")
        assert resp.status_code == 200
        assert resp.json()["status"] == "available"
