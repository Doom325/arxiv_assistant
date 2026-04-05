import datetime
from unittest.mock import MagicMock, patch
import pytest
from scripts.manual_trigger import backfill_papers
from models import UserConfig, Paper

@patch('scripts.manual_trigger.SessionLocal')
@patch('scripts.manual_trigger.arxiv_service')
@patch('scripts.manual_trigger.process_paper_entry')
def test_backfill_papers(mock_process, mock_arxiv, mock_session_local):
    # Mocking DB Session
    mock_db = MagicMock()
    mock_session_local.return_value = mock_db
    
    # Mock UserConfig query to return one config with single category
    mock_config = MagicMock()
    mock_config.categories = ["cs.CV"]
    
    def mock_query(model):
        query_mock = MagicMock()
        if model is UserConfig:
            query_mock.all.return_value = [mock_config]
        elif model is Paper.arxiv_id:
            # For the existance check, pretend paper doesn't exist yet
            filter_mock = MagicMock()
            filter_mock.all.return_value = []
            query_mock.filter.return_value = filter_mock
        return query_mock
        
    mock_db.query.side_effect = mock_query
    
    # Mock arXiv response
    mock_paper_data = {
        'arxiv_id': '2301.00001',
        'title': 'Test Paper',
        'published_date': datetime.datetime(2026, 4, 4, 12, 0, 0)
    }
    mock_arxiv.fetch_papers.return_value = [mock_paper_data]
    
    # Run backfill
    start_date = datetime.date(2026, 4, 3)
    end_date = datetime.date(2026, 4, 5)
    
    backfill_papers(start_date, end_date)
    
    # Verify process_paper_entry was called
    mock_process.assert_called_once_with(mock_db, mock_paper_data)
    mock_db.close.assert_called_once()
    
    # Verify fetch called with correct category
    mock_arxiv.fetch_papers.assert_called_once_with(query="cat:cs.CV", max_results=800)

@patch('scripts.manual_trigger.SessionLocal')
@patch('scripts.manual_trigger.arxiv_service')
@patch('scripts.manual_trigger.process_paper_entry')
def test_backfill_papers_outside_date_range(mock_process, mock_arxiv, mock_session_local):
    mock_db = MagicMock()
    mock_session_local.return_value = mock_db
    mock_config = MagicMock()
    mock_config.categories = ["cs.CV"]
    mock_db.query.return_value.all.return_value = [mock_config]
    
    # Mock arXiv response with OUTSIDE date
    mock_paper_data = {
        'arxiv_id': '2301.00002',
        'title': 'Old Paper',
        'published_date': datetime.datetime(2026, 4, 1, 12, 0, 0)
    }
    mock_arxiv.fetch_papers.return_value = [mock_paper_data]
    
    start_date = datetime.date(2026, 4, 3)
    end_date = datetime.date(2026, 4, 5)
    
    backfill_papers(start_date, end_date)
    
    # Verify process_paper_entry was NOT called because date is outside range
    mock_process.assert_not_called()
    mock_db.close.assert_called_once()

@patch('scripts.manual_trigger.SessionLocal')
@patch('scripts.manual_trigger.arxiv_service')
@patch('scripts.manual_trigger.process_paper_entry')
def test_backfill_papers_duplicate(mock_process, mock_arxiv, mock_session_local):
    mock_db = MagicMock()
    mock_session_local.return_value = mock_db
    mock_config = MagicMock()
    mock_config.categories = ["cs.CV"]
    
    def mock_query(model):
        query_mock = MagicMock()
        if model is UserConfig:
            query_mock.all.return_value = [mock_config]
        elif model is Paper.arxiv_id:
            # Simulate paper already existing in the db
            class MockPaperId:
                arxiv_id = '2301.00001'
            filter_mock = MagicMock()
            filter_mock.all.return_value = [MockPaperId()]
            query_mock.filter.return_value = filter_mock
        return query_mock
    mock_db.query.side_effect = mock_query

    mock_paper_data = {
        'arxiv_id': '2301.00001',
        'title': 'Test Paper',
        'published_date': datetime.datetime(2026, 4, 4, 12, 0, 0)
    }
    mock_arxiv.fetch_papers.return_value = [mock_paper_data]
    
    backfill_papers(datetime.date(2026, 4, 3), datetime.date(2026, 4, 5))
    
    # duplicate -> NOT ingested
    mock_process.assert_not_called()
    mock_db.close.assert_called_once()

@patch('scripts.manual_trigger.SessionLocal')
@patch('scripts.manual_trigger.arxiv_service')
@patch('scripts.manual_trigger.process_paper_entry')
def test_backfill_papers_per_paper_exception(mock_process, mock_arxiv, mock_session_local):
    # Tests that one ingestion failure doesn't break the whole backfill
    mock_db = MagicMock()
    mock_session_local.return_value = mock_db
    
    # Return empty UserConfig to trigger default categories
    def mock_query(model):
        query_mock = MagicMock()
        if model is UserConfig:
            query_mock.all.return_value = []
        elif model is Paper.arxiv_id:
            filter_mock = MagicMock()
            filter_mock.all.return_value = []
            query_mock.filter.return_value = filter_mock
        return query_mock
    mock_db.query.side_effect = mock_query

    # Two papers: first fails, second succeeds
    paper1 = {'arxiv_id': '2301.00001', 'title': 'P1', 'published_date': datetime.datetime(2026, 4, 4, 12, 0, 0)}
    paper2 = {'arxiv_id': '2301.00002', 'title': 'P2', 'published_date': datetime.datetime(2026, 4, 4, 12, 0, 0)}
    
    mock_arxiv.fetch_papers.return_value = [paper1, paper2]
    
    # Mock process_paper_entry to raise Exception on the first call, succeed on second
    def fake_process_paper_entry(db, paper_data):
        if paper_data['arxiv_id'] == '2301.00001':
            raise Exception("Ingestion failed")
        return MagicMock()
    
    mock_process.side_effect = fake_process_paper_entry
    
    backfill_papers(datetime.date(2026, 4, 3), datetime.date(2026, 4, 5))
    
    # process_paper_entry should be called for both papers despite the first failing (across 11 categories: 11 * 2 = 22)
    assert mock_process.call_count == 22
    mock_db.close.assert_called_once()
    assert mock_arxiv.fetch_papers.call_count == 11  # Called for the 11 default categories

@patch('scripts.manual_trigger.SessionLocal')
@patch('scripts.manual_trigger.arxiv_service')
def test_backfill_papers_fatal_exception(mock_arxiv, mock_session_local):
    mock_db = MagicMock()
    mock_session_local.return_value = mock_db
    mock_db.query.side_effect = Exception("Database connection failure")
    
    with pytest.raises(Exception, match="Database connection failure"):
        backfill_papers(datetime.date(2026, 4, 3), datetime.date(2026, 4, 5))
    
    # Ensure finally block closes DB even on fatal exceptions
    mock_db.close.assert_called_once()

