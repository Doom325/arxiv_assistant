
import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from production_worker import PDFProcessorLite

class TestCitationExtraction(unittest.TestCase):
    def setUp(self):
        self.processor = PDFProcessorLite()

    def test_extract_citations_header_detection(self):
        # Test distinct headers
        texts = [
            "Some content\nReferences\n[1] Paper One",
            "Some content\nBibliography\n[1] Paper One",
            "Some content\nWorks Cited\n[1] Paper One",
        ]
        
        with patch.object(self.processor, '_parse_citations_with_mlx', return_value=[{"title": "Paper One"}]):
            for t in texts:
                citations = self.processor.extract_citations(t)
                self.assertEqual(len(citations), 1)
                self.assertEqual(citations[0]["title"], "Paper One")

    def test_extract_citations_fallback(self):
        # Test fallback to llm_service when HAS_MLX is False
        with patch('production_worker.HAS_MLX', False):
            with patch('production_worker.llm_service') as mock_llm:
                mock_llm.parse_citations.return_value = [{"title": "Paper Two"}]
                citations = self.processor.extract_citations("References\n[2] Paper Two")
                self.assertEqual(len(citations), 1)
                self.assertEqual(citations[0]["title"], "Paper Two")
                mock_llm.parse_citations.assert_called_once()

    def test_extract_citations_not_found(self):
        citations = self.processor.extract_citations("Random text without references header")
        self.assertEqual(citations, [])

if __name__ == '__main__':
    unittest.main()
