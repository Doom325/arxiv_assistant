import pytest
from unittest.mock import MagicMock, patch
from services.arxiv_service import ArxivService

@pytest.fixture
def arxiv_service():
    return ArxivService()

def test_fetch_papers(arxiv_service):
    # Mock the arxiv.Client and its results
    mock_result = MagicMock()
    mock_result.entry_id = "http://arxiv.org/abs/2101.00001"
    mock_result.title = "Test Paper"
    mock_result.authors = [MagicMock(name="Author One")]
    mock_result.authors[0].name = "Author One"
    mock_result.summary = "Test Summary"
    mock_result.published.date.return_value = "2021-01-01"
    mock_result.pdf_url = "http://arxiv.org/pdf/2101.00001"
    mock_result.primary_category = "cs.AI"

    with patch.object(arxiv_service.client, 'results', return_value=[mock_result]):
        papers = arxiv_service.fetch_papers(query="test", max_results=1)
        
        assert len(papers) == 1
        assert papers[0]['arxiv_id'] == "2101.00001"
        assert papers[0]['title'] == "Test Paper"
        assert papers[0]['authors'] == ["Author One"]

@patch('requests.get')
@patch('builtins.open', new_callable=MagicMock)
def test_download_pdf(mock_open, mock_get, arxiv_service):
    # Mock response
    mock_response = MagicMock()
    mock_response.content = b"PDF Content"
    mock_response.status_code = 200
    mock_get.return_value = mock_response
    
    # Mock file handle
    mock_file = MagicMock()
    mock_open.return_value.__enter__.return_value = mock_file

    arxiv_service.download_pdf("http://example.com/paper.pdf", "paper.pdf")
    
    mock_get.assert_called_once()
    mock_file.write.assert_called_once_with(b"PDF Content")

def test_extract_text(arxiv_service):
    with patch('core.pdf_utils.PdfReader') as MockPdfReader:
        mock_reader = MockPdfReader.return_value
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Page Text"
        mock_reader.pages = [mock_page]
        
        text = arxiv_service.extract_text("paper.pdf")
        
        assert "Page Text" in text
