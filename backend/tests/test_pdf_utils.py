"""Tests for core/pdf_utils.py"""
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from core.pdf_utils import extract_text_from_pdf, get_local_pdf_path, download_pdf


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


class TestDownloadPdf:
    @patch("core.pdf_utils.requests.get")
    def test_success(self, mock_get, tmp_path):
        mock_response = MagicMock()
        mock_response.content = b"fake pdf content"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = download_pdf("http://example.com/paper.pdf", "2401.00001", str(tmp_path))
        assert result is not None
        assert os.path.exists(result)

    @patch("core.pdf_utils.requests.get")
    def test_failure(self, mock_get, tmp_path):
        mock_get.side_effect = Exception("Network error")
        result = download_pdf("http://example.com/paper.pdf", "2401.00001", str(tmp_path))
        assert result is None
