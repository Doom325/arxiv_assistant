import pytest
from unittest.mock import MagicMock, patch
import queue

from scripts.backfill_parallel import get_partition, classify_paper_raw, worker_process, log_queue

@pytest.fixture(autouse=True)
def clear_queue():
    while not log_queue.empty():
        try:
            log_queue.get_nowait()
        except queue.Empty:
            break
    yield

def test_get_partition():
    # Deterministic mapping test
    w_id1 = get_partition("1234.5678", 4)
    w_id2 = get_partition("1234.5678", 4)
    assert w_id1 == w_id2
    assert 0 <= w_id1 < 4
    
    w_id3 = get_partition("9999.1111", 4)
    w_id4 = get_partition("9999.1111", 4)
    assert w_id3 == w_id4
    assert 0 <= w_id3 < 4

def test_classify_paper_raw_success():
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "message": {"content": '{"is_agentic": true, "primary_category": "cs.AI", "patterns": [{"name": "Tool Use"}]}'},
        "eval_count": 100,
        "prompt_eval_count": 50,
        "eval_duration": 1000000000 # 1 sec
    }
    mock_session.post.return_value = mock_response
    
    result = classify_paper_raw("Title", "Abstract", mock_session)
    
    assert result["is_agentic"] is True
    assert result["_meta"]["eval_count"] == 100
    assert result["_meta"]["eval_duration"] == 1.0
    
    # Check POST kwargs
    mock_session.post.assert_called_once()
    args, kwargs = mock_session.post.call_args
    assert kwargs["timeout"] == 120
    assert kwargs["json"]["options"]["num_ctx"] == 4096

@patch("scripts.backfill_parallel.SessionLocal")
@patch("scripts.backfill_parallel.classify_paper_raw")
def test_worker_process_dry_run(mock_classify, mock_session_local):
    mock_classify.return_value = {"is_agentic": True}
    papers = [("1234.5678", "Title", "Abstract")]
    
    worker_process(0, papers, is_dry_run=True)
    
    # Should not call database
    mock_session_local.assert_not_called()
    assert log_queue.qsize() == 0

@patch("scripts.backfill_parallel.SessionLocal")
@patch("scripts.backfill_parallel.classify_paper_raw")
def test_worker_process_success(mock_classify, mock_session_local):
    mock_classify.return_value = {
        "is_agentic": True,
        "primary_category": "cs.AI",
        "patterns": [],
        "_meta": {"eval_count": 50, "eval_duration": 0.5}
    }
    
    db_mock = MagicMock()
    mock_session_local.return_value = db_mock
    papers = [("1234.5678", "Title", "Abstract")]
    
    worker_process(0, papers, is_dry_run=False)
    
    db_mock.add.assert_called_once()
    added_obj = db_mock.add.call_args[0][0]
    assert added_obj.arxiv_id == "1234.5678"
    assert added_obj.model_name == "gemma3:12b-parallel-backfill"
    
    db_mock.commit.assert_called_once()
    
    # Check logging queue
    assert log_queue.qsize() > 0
    log_msg = log_queue.get_nowait()
    assert log_msg["arxiv_id"] == "1234.5678"
    assert log_msg["status"] == "success"

@patch("scripts.backfill_parallel.SessionLocal")
@patch("scripts.backfill_parallel.classify_paper_raw")
def test_worker_process_error(mock_classify, mock_session_local):
    mock_classify.return_value = {"_error": "Connection Timeout"}
    
    db_mock = MagicMock()
    mock_session_local.return_value = db_mock
    papers = [("error.1234", "Title", "Abstract")]
    
    worker_process(1, papers, is_dry_run=False)
    
    added_obj = db_mock.add.call_args[0][0]
    assert added_obj.error == "Connection Timeout"
    assert added_obj.taxonomy_violations == ["PARSE_FAILED"]
    
    db_mock.commit.assert_called_once()
    
    log_msg = log_queue.get_nowait()
    assert log_msg["status"] == "error"
    assert log_msg["error_message"] == "Connection Timeout"
