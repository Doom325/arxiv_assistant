"""Tests for core/pdf_utils.py"""
import errno
import os
import tempfile
import pytest
import requests
from unittest.mock import patch, MagicMock
from core.pdf_utils import (
    PdfDownloadError,
    download_pdf,
    download_pdf_strict,
    extract_text_from_pdf,
    get_local_pdf_path,
)


def _pdf_response(content: bytes = b"%PDF-1.4 minimal body") -> MagicMock:
    """A requests-style response whose body is a valid PDF."""
    response = MagicMock()
    response.content = content
    response.raise_for_status = MagicMock()
    return response


class TestExtractTextFromPdf:
    def test_valid_pdf(self, tmp_path):
        """Test extraction from a real (minimal) PDF."""
        # Create a minimal PDF using pypdf
        from pypdf import PdfWriter
        writer = PdfWriter()
        writer.add_blank_page(width=72, height=72)
        pdf_path = str(tmp_path / "test.pdf")
        with open(pdf_path, "wb") as f:
            writer.write(f)
        # Blank page has no text
        result = extract_text_from_pdf(pdf_path)
        assert isinstance(result, str)

    def test_nonexistent_file(self):
        result = extract_text_from_pdf("/nonexistent/path/file.pdf")
        assert result == ""

    def test_invalid_file(self, tmp_path):
        bad_file = tmp_path / "bad.pdf"
        bad_file.write_text("this is not a pdf")
        result = extract_text_from_pdf(str(bad_file))
        assert result == ""


class TestGetLocalPdfPath:
    def test_exact_match(self, tmp_path):
        pdf = tmp_path / "2401.12345.pdf"
        pdf.write_text("fake")
        result = get_local_pdf_path("2401.12345", str(tmp_path))
        assert result == str(pdf)

    def test_version_stripped(self, tmp_path):
        pdf = tmp_path / "2401.12345.pdf"
        pdf.write_text("fake")
        result = get_local_pdf_path("2401.12345v2", str(tmp_path))
        assert result == str(pdf)

    def test_not_found(self, tmp_path):
        result = get_local_pdf_path("9999.99999", str(tmp_path))
        assert result is None

    def test_zero_byte_file_counts_as_missing(self, tmp_path):
        """A 0-byte stub (the disk-full incident) must be treated as absent.

        Regression: the old implementation used os.path.exists, so an empty
        ``<id>.pdf`` was reported as present and every later read failed.
        """
        (tmp_path / "2401.12345.pdf").write_bytes(b"")
        assert get_local_pdf_path("2401.12345", str(tmp_path)) is None


class TestDownloadPdfStrict:
    """download_pdf_strict: validated, atomic, structured errors."""

    @patch("core.pdf_utils.requests.get")
    def test_success_writes_validated_pdf(self, mock_get, tmp_path):
        mock_get.return_value = _pdf_response(b"%PDF-1.5 body")
        path = download_pdf_strict(
            "http://x/paper.pdf", "2401.00001", str(tmp_path), delay_seconds=0
        )
        assert os.path.exists(path)
        with open(path, "rb") as f:
            assert f.read().startswith(b"%PDF-")
        assert not [p for p in os.listdir(tmp_path) if p.endswith(".part")]

    @patch("core.pdf_utils.requests.get")
    def test_empty_body_rejected(self, mock_get, tmp_path):
        mock_get.return_value = _pdf_response(b"")
        with pytest.raises(PdfDownloadError) as ei:
            download_pdf_strict("http://x/p.pdf", "2401.1", str(tmp_path), delay_seconds=0)
        assert ei.value.code == "pdf_invalid_body"
        assert not os.path.exists(os.path.join(tmp_path, "2401.1.pdf"))

    @patch("core.pdf_utils.requests.get")
    def test_html_body_rejected_and_leaves_no_file(self, mock_get, tmp_path):
        mock_get.return_value = _pdf_response(b"<!DOCTYPE html><html>error</html>")
        with pytest.raises(PdfDownloadError) as ei:
            download_pdf_strict("http://x/p.pdf", "2401.2", str(tmp_path), delay_seconds=0)
        assert ei.value.code == "pdf_invalid_body"
        assert ei.value.retryable is False
        assert not os.path.exists(os.path.join(tmp_path, "2401.2.pdf"))

    @pytest.mark.parametrize(
        "status,retryable",
        [(429, True), (500, True), (503, True), (404, False), (403, False)],
    )
    @patch("core.pdf_utils.requests.get")
    def test_http_error_status_and_retryability(
        self, mock_get, status, retryable, tmp_path
    ):
        response = MagicMock()
        response.status_code = status
        response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=response
        )
        mock_get.return_value = response
        with pytest.raises(PdfDownloadError) as ei:
            download_pdf_strict("http://x/p.pdf", "2401.3", str(tmp_path), delay_seconds=0)
        assert ei.value.code == "pdf_http_error"
        assert ei.value.http_status == status
        assert ei.value.retryable is retryable

    @patch("core.pdf_utils.requests.get")
    def test_timeout_is_retryable(self, mock_get, tmp_path):
        mock_get.side_effect = requests.exceptions.Timeout("slow")
        with pytest.raises(PdfDownloadError) as ei:
            download_pdf_strict("http://x/p.pdf", "2401.4", str(tmp_path), delay_seconds=0)
        assert ei.value.code == "pdf_timeout"
        assert ei.value.retryable is True

    @patch("core.pdf_utils.requests.get")
    def test_connection_error_is_retryable(self, mock_get, tmp_path):
        mock_get.side_effect = requests.exceptions.ConnectionError("down")
        with pytest.raises(PdfDownloadError) as ei:
            download_pdf_strict("http://x/p.pdf", "2401.5", str(tmp_path), delay_seconds=0)
        assert ei.value.code == "pdf_network_error"
        assert ei.value.retryable is True

    @patch("core.pdf_utils.os.replace")
    @patch("core.pdf_utils.requests.get")
    def test_disk_full_is_non_retryable_and_leaves_no_file(
        self, mock_get, mock_replace, tmp_path
    ):
        mock_get.return_value = _pdf_response(b"%PDF-1.4 body")
        mock_replace.side_effect = OSError(errno.ENOSPC, "No space left on device")
        with pytest.raises(PdfDownloadError) as ei:
            download_pdf_strict("http://x/p.pdf", "2401.6", str(tmp_path), delay_seconds=0)
        assert ei.value.code == "pdf_disk_full"
        assert ei.value.retryable is False
        assert not os.path.exists(os.path.join(tmp_path, "2401.6.pdf"))
        assert not [p for p in os.listdir(tmp_path) if p.endswith(".part")]

    @patch("core.pdf_utils.requests.get")
    def test_existing_zero_byte_file_is_replaced(self, mock_get, tmp_path):
        (tmp_path / "2401.7.pdf").write_bytes(b"")
        mock_get.return_value = _pdf_response(b"%PDF-1.4 real")
        path = download_pdf_strict(
            "http://x/p.pdf", "2401.7", str(tmp_path), delay_seconds=0
        )
        assert os.path.getsize(path) > 0
        with open(path, "rb") as f:
            assert f.read().startswith(b"%PDF-")


class TestDownloadPdfLenient:
    """download_pdf: backwards-compatible str|None wrapper for workers/scripts."""

    @patch("core.pdf_utils.time.sleep")
    @patch("core.pdf_utils.requests.get")
    def test_success_returns_path(self, mock_get, _sleep, tmp_path):
        mock_get.return_value = _pdf_response()
        result = download_pdf("http://x/paper.pdf", "2401.00001", str(tmp_path))
        assert result is not None
        assert os.path.exists(result)

    @patch("core.pdf_utils.time.sleep")
    @patch("core.pdf_utils.requests.get")
    def test_failure_returns_none(self, mock_get, _sleep, tmp_path):
        mock_get.side_effect = Exception("Network error")
        result = download_pdf("http://x/paper.pdf", "2401.00001", str(tmp_path))
        assert result is None

    @patch("core.pdf_utils.time.sleep")
    @patch("core.pdf_utils.requests.get")
    def test_invalid_body_returns_none_and_leaves_no_file(
        self, mock_get, _sleep, tmp_path
    ):
        mock_get.return_value = _pdf_response(b"not a pdf")
        result = download_pdf("http://x/paper.pdf", "2401.9", str(tmp_path))
        assert result is None
        assert not os.path.exists(os.path.join(tmp_path, "2401.9.pdf"))
