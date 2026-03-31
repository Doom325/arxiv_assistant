"""Tests for services/pdf_service.py — find_reference_section, extract_citations, process_pdf."""

import sys
from unittest.mock import patch, MagicMock

from services.pdf_service import find_reference_section, extract_citations, process_pdf


class TestFindReferenceSection:
    def test_finds_references_header(self):
        text = "Some intro text.\n\nReferences\n[1] First citation.\n[2] Second citation."
        result = find_reference_section(text)
        assert result is not None
        assert "[1] First citation" in result

    def test_finds_numbered_references_header(self):
        text = "Body text.\n\n7. References\nSmith et al. 2020."
        result = find_reference_section(text)
        assert result is not None
        assert "Smith" in result

    def test_finds_bibliography_header(self):
        text = "Content.\n\nBibliography\nEntry one.\nEntry two."
        result = find_reference_section(text)
        assert result is not None
        assert "Entry one" in result

    def test_returns_none_when_no_header(self):
        text = "This text has no reference section at all."
        result = find_reference_section(text)
        assert result is None

    def test_truncates_to_5000_chars(self):
        refs = "A" * 6000
        text = f"Intro.\n\nReferences\n{refs}"
        result = find_reference_section(text)
        assert result is not None
        assert len(result) == 5000

    def test_case_insensitive(self):
        text = "Body.\n\nREFERENCES\n[1] Some citation."
        result = find_reference_section(text)
        assert result is not None


class TestExtractCitations:
    @patch("services.pdf_service.HAS_MLX", False)
    @patch("services.pdf_service.llm_service")
    def test_calls_llm_parse_citations(self, mock_llm):
        """When HAS_MLX is False, should use llm_service.parse_citations."""
        mock_llm.parse_citations.return_value = [
            {"raw": "test", "title": "Test Paper", "authors": [], "url": None}
        ]
        text = "Body text.\n\nReferences\n[1] Test citation text."
        result = extract_citations(text)
        mock_llm.parse_citations.assert_called_once()
        assert len(result) == 1
        assert result[0]["title"] == "Test Paper"

    def test_returns_empty_when_no_refs(self):
        text = "No reference section here."
        result = extract_citations(text)
        assert result == []


class TestProcessPdf:
    @patch("services.pdf_service.HAS_MLX", False)
    @patch("services.pdf_service.llm_service")
    @patch("services.pdf_service.extract_citations")
    @patch("services.pdf_service.extract_text_from_pdf")
    def test_process_pdf_valid(self, mock_extract, mock_cit, mock_llm):
        mock_extract.return_value = "Abstract\nThis is the abstract.\n\nIntroduction\nThis is the intro."
        mock_cit.return_value = [{"title": "Cited Paper"}]
        mock_llm.generate_embedding.return_value = [0.1, 0.2]

        # Mock nlp_service module (lazy-imported inside process_pdf, requires gliner/torch)
        mock_nlp_module = MagicMock()
        mock_nlp_module.nlp_service.extract_entities.return_value = [{"text": "BERT", "label": "Model"}]

        with patch.dict(sys.modules, {"services.nlp_service": mock_nlp_module}):
            result = process_pdf("/fake/path.pdf")

        assert result is not None
        assert result["file"] == "/fake/path.pdf"
        assert "sections" in result
        assert result["citations"] == [{"title": "Cited Paper"}]
        assert "embeddings" in result

    @patch("services.pdf_service.extract_text_from_pdf")
    def test_process_pdf_no_text(self, mock_extract):
        mock_extract.return_value = ""
        result = process_pdf("/fake/empty.pdf")
        assert result is None

    @patch("services.pdf_service.HAS_MLX", False)
    @patch("services.pdf_service.llm_service")
    @patch("services.pdf_service.extract_citations")
    @patch("services.pdf_service.extract_text_from_pdf")
    def test_process_pdf_no_citations(self, mock_extract, mock_cit, mock_llm):
        mock_extract.return_value = "Abstract\nSome abstract text."
        mock_cit.return_value = []
        mock_llm.generate_embedding.return_value = [0.1]

        mock_nlp_module = MagicMock()
        mock_nlp_module.nlp_service.extract_entities.return_value = []

        with patch.dict(sys.modules, {"services.nlp_service": mock_nlp_module}):
            result = process_pdf("/fake/path.pdf")

        assert result is not None
        assert result["citations"] == []
