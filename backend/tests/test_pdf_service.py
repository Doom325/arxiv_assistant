"""Tests for services/pdf_service.py — extract_citations (GROBID), process_pdf."""

import sys
from unittest.mock import patch, MagicMock

from services.pdf_service import extract_citations, process_pdf


class TestExtractCitations:
    @patch("services.pdf_service.extract_references_from_pdf")
    def test_delegates_to_grobid(self, mock_grobid):
        """extract_citations should pass pdf_path directly to GROBID."""
        mock_grobid.return_value = [
            {"raw": "Author. Title. arXiv:2301.00001", "title": "Title", "authors": ["Author"], "url": ""}
        ]
        result = extract_citations("/fake/paper.pdf")
        mock_grobid.assert_called_once_with("/fake/paper.pdf")
        assert len(result) == 1
        assert result[0]["title"] == "Title"

    @patch("services.pdf_service.extract_references_from_pdf")
    def test_returns_empty_on_failure(self, mock_grobid):
        mock_grobid.return_value = []
        result = extract_citations("/fake/missing.pdf")
        assert result == []


class TestProcessPdf:
    @patch("services.pdf_service.extract_citations")
    @patch("services.pdf_service.extract_text_from_pdf")
    def test_process_pdf_valid(self, mock_extract, mock_cit):
        mock_extract.return_value = "Abstract\nThis is the abstract.\n\nIntroduction\nThis is the intro."
        mock_cit.return_value = [{"title": "Cited Paper", "raw": "test", "authors": [], "url": ""}]

        # Mock embedding_service (used directly in process_pdf)
        with patch("services.pdf_service.embedding_service") as mock_embed:
            mock_embed.generate_embedding.return_value = [0.1, 0.2]
            mock_embed.__class__.__name__ = "MockEmbedding"

            # Mock nlp_service (lazy-imported inside process_pdf)
            mock_nlp_module = MagicMock()
            mock_nlp_module.nlp_service.extract_entities.return_value = [{"text": "BERT", "label": "Model"}]

            with patch.dict(sys.modules, {"services.nlp_service": mock_nlp_module}):
                result = process_pdf("/fake/path.pdf")

        assert result is not None
        assert result["file"] == "/fake/path.pdf"
        assert "sections" in result
        assert result["citations"] == [{"title": "Cited Paper", "raw": "test", "authors": [], "url": ""}]
        # extract_citations gets pdf_path, not text
        mock_cit.assert_called_once_with("/fake/path.pdf")

    @patch("services.pdf_service.extract_text_from_pdf")
    def test_process_pdf_no_text(self, mock_extract):
        mock_extract.return_value = ""
        result = process_pdf("/fake/empty.pdf")
        assert result is None
