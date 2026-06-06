import datetime

import arxiv
import pytest
from unittest.mock import MagicMock, patch
from services.arxiv_service import ArxivService, ARXIV_429_MAX_RETRIES

@pytest.fixture
def arxiv_service():
    return ArxivService()


def _mock_result(arxiv_id="2101.00001"):
    """Build a fake arxiv result row with all fields fetch_papers_since reads."""
    result = MagicMock()
    result.entry_id = f"http://arxiv.org/abs/{arxiv_id}"
    result.title = "Test Paper"
    author = MagicMock()
    author.name = "Author One"
    result.authors = [author]
    result.summary = "Test Summary"
    result.published = datetime.datetime(2026, 1, 5)
    result.updated = datetime.datetime(2026, 1, 5)
    result.pdf_url = f"http://arxiv.org/pdf/{arxiv_id}"
    result.primary_category = "cs.AI"
    return result

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


def test_fetch_papers_since_with_until_date(arxiv_service):
    """``until_date`` must produce a closed ``submittedDate:[X TO Y]`` range query."""
    import datetime
    captured = {}

    def fake_search(query, **kwargs):
        captured["query"] = query
        return MagicMock()

    with patch("services.arxiv_service.arxiv.Search", side_effect=fake_search), \
         patch.object(arxiv_service.client, "results", return_value=iter([])):
        list(arxiv_service.fetch_papers_since(
            category="cs.AI",
            since_date=datetime.date(2026, 1, 1),
            until_date=datetime.date(2026, 1, 31),
        ))

    assert "submittedDate:[202601010000 TO 202601312359]" in captured["query"]
    assert "cat:cs.AI" in captured["query"]


def test_fetch_papers_since_without_until_date_defaults_to_tomorrow(arxiv_service):
    """Omitting ``until_date`` defaults the upper bound to tomorrow."""
    import datetime
    captured = {}

    def fake_search(query, **kwargs):
        captured["query"] = query
        return MagicMock()

    with patch("services.arxiv_service.arxiv.Search", side_effect=fake_search), \
         patch.object(arxiv_service.client, "results", return_value=iter([])):
        list(arxiv_service.fetch_papers_since(
            category="cs.AI",
            since_date=datetime.date(2026, 1, 1),
        ))

    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    tomorrow_str = tomorrow.strftime("%Y%m%d2359")
    assert f"submittedDate:[202601010000 TO {tomorrow_str}]" in captured["query"]


def test_fetch_papers_since_descending_uses_descending_sort_order(arxiv_service):
    """``descending=True`` must pass arxiv.SortOrder.Descending to the Search."""
    import datetime
    import arxiv as arxiv_lib
    captured = {}

    def fake_search(query, **kwargs):
        captured["query"] = query
        captured["sort_order"] = kwargs.get("sort_order")
        return MagicMock()

    with patch("services.arxiv_service.arxiv.Search", side_effect=fake_search), \
         patch.object(arxiv_service.client, "results", return_value=iter([])):
        list(arxiv_service.fetch_papers_since(
            category="cs.AI",
            since_date=datetime.date(2026, 1, 1),
            until_date=datetime.date(2026, 1, 31),
            descending=True,
        ))

    assert captured["sort_order"] == arxiv_lib.SortOrder.Descending


def test_fetch_papers_since_default_is_ascending(arxiv_service):
    """Daily-poll callers omit ``descending`` and must keep ascending sort."""
    import datetime
    import arxiv as arxiv_lib
    captured = {}

    def fake_search(query, **kwargs):
        captured["sort_order"] = kwargs.get("sort_order")
        return MagicMock()

    with patch("services.arxiv_service.arxiv.Search", side_effect=fake_search), \
         patch.object(arxiv_service.client, "results", return_value=iter([])):
        list(arxiv_service.fetch_papers_since(
            category="cs.AI",
            since_date=datetime.date(2026, 1, 1),
        ))

    assert captured["sort_order"] == arxiv_lib.SortOrder.Ascending


def test_fetch_papers_since_passes_max_results_to_search(arxiv_service):
    """``arxiv.Search(max_results=...)`` must be set to safety_cap, otherwise
    the lib's default 100 silently truncates multi-page queries."""
    import datetime
    captured = {}

    def fake_search(*args, **kwargs):
        captured.update(kwargs)
        return MagicMock()

    with patch("services.arxiv_service.arxiv.Search", side_effect=fake_search), \
         patch.object(arxiv_service.client, "results", return_value=iter([])):
        list(arxiv_service.fetch_papers_since(
            category="cs.AI",
            since_date=datetime.date(2026, 1, 1),
            safety_cap=5000,
        ))

    assert captured["max_results"] == 5000


def test_fetch_papers_since_retries_on_429_then_succeeds(arxiv_service):
    """A transient HTTP 429 must be retried with backoff, not surfaced."""
    err = arxiv.HTTPError(url="http://export.arxiv.org/api", retry=3, status=429)
    results_mock = MagicMock(side_effect=[err, iter([_mock_result()])])

    with patch("services.arxiv_service.arxiv.Search", return_value=MagicMock()), \
         patch("services.arxiv_service.time.sleep") as mock_sleep, \
         patch.object(arxiv_service.client, "results", results_mock):
        papers = list(arxiv_service.fetch_papers_since(
            category="cs.AI",
            since_date=datetime.date(2026, 1, 1),
            until_date=datetime.date(2026, 1, 31),
        ))

    assert len(papers) == 1
    assert papers[0]["arxiv_id"] == "2101.00001"
    assert results_mock.call_count == 2  # initial attempt + one retry
    assert mock_sleep.call_count == 1    # backed off once before retrying


def test_fetch_papers_since_reraises_non_429(arxiv_service):
    """Non-429 HTTP errors must propagate immediately without retrying."""
    err = arxiv.HTTPError(url="http://export.arxiv.org/api", retry=3, status=503)
    results_mock = MagicMock(side_effect=err)

    with patch("services.arxiv_service.arxiv.Search", return_value=MagicMock()), \
         patch("services.arxiv_service.time.sleep") as mock_sleep, \
         patch.object(arxiv_service.client, "results", results_mock):
        with pytest.raises(arxiv.HTTPError):
            list(arxiv_service.fetch_papers_since(
                category="cs.AI",
                since_date=datetime.date(2026, 1, 1),
                until_date=datetime.date(2026, 1, 31),
            ))

    assert results_mock.call_count == 1  # no retry for non-429
    assert mock_sleep.call_count == 0


def test_fetch_papers_since_gives_up_after_max_429_retries(arxiv_service):
    """Persistent 429s must eventually surface after exhausting retries."""
    err = arxiv.HTTPError(url="http://export.arxiv.org/api", retry=3, status=429)
    results_mock = MagicMock(side_effect=err)

    with patch("services.arxiv_service.arxiv.Search", return_value=MagicMock()), \
         patch("services.arxiv_service.time.sleep") as mock_sleep, \
         patch.object(arxiv_service.client, "results", results_mock):
        with pytest.raises(arxiv.HTTPError):
            list(arxiv_service.fetch_papers_since(
                category="cs.AI",
                since_date=datetime.date(2026, 1, 1),
                until_date=datetime.date(2026, 1, 31),
            ))

    # initial attempt + ARXIV_429_MAX_RETRIES retries, sleeping before each retry
    assert results_mock.call_count == ARXIV_429_MAX_RETRIES + 1
    assert mock_sleep.call_count == ARXIV_429_MAX_RETRIES
