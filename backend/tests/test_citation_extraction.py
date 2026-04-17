"""Tests for GROBID-based citation extraction via PDFProcessorLite shim."""

import unittest
from unittest.mock import patch

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from production_worker import PDFProcessorLite


class TestCitationExtraction(unittest.TestCase):
    def setUp(self):
        self.processor = PDFProcessorLite()

    @patch("production_worker.extract_citations")
    def test_extract_citations_delegates_to_grobid(self, mock_extract):
        """PDFProcessorLite.extract_citations should pass pdf_path to GROBID-backed extract_citations."""
        mock_extract.return_value = [
            {"raw": "Author. Title. arXiv:2301.00001", "title": "Title", "authors": ["Author"], "url": ""}
        ]
        result = self.processor.extract_citations("/fake/paper.pdf")
        mock_extract.assert_called_once_with("/fake/paper.pdf")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["title"], "Title")

    @patch("production_worker.extract_citations")
    def test_extract_citations_returns_empty_on_failure(self, mock_extract):
        mock_extract.return_value = []
        result = self.processor.extract_citations("/fake/bad.pdf")
        self.assertEqual(result, [])


if __name__ == '__main__':
    unittest.main()
