"""Tests for routers/search.py — parse_query utility."""

from routers.search import parse_query


class TestParseQuery:
    def test_plain_query(self):
        text, filters = parse_query("transformer attention")
        assert text == "transformer attention"
        assert all(v is None for v in filters.values())

    def test_category_filter(self):
        text, filters = parse_query("attention category:cs.AI")
        assert text == "attention"
        assert filters["category"] == "cs.AI"

    def test_after_date(self):
        text, filters = parse_query("diffusion after:2024-01-15")
        assert text == "diffusion"
        assert filters["after"] == "2024-01-15"

    def test_after_year_only(self):
        text, filters = parse_query("diffusion after:2024")
        assert text == "diffusion"
        assert filters["after"] == "2024-01-01"

    def test_before_date(self):
        text, filters = parse_query("GAN before:2023-06-30")
        assert text == "GAN"
        assert filters["before"] == "2023-06-30"

    def test_before_year_only(self):
        text, filters = parse_query("GAN before:2023")
        assert text == "GAN"
        assert filters["before"] == "2023-12-31"

    def test_author_filter(self):
        text, filters = parse_query("reinforcement learning author:Sutton")
        assert text == "reinforcement learning"
        assert filters["author"] == "Sutton"

    def test_entity_filter(self):
        text, filters = parse_query("neural nets entity:BERT")
        assert text == "neural nets"
        assert filters["entity"] == "BERT"

    def test_multiple_filters(self):
        text, filters = parse_query(
            "attention category:cs.LG after:2023 author:Vaswani"
        )
        assert text == "attention"
        assert filters["category"] == "cs.LG"
        assert filters["after"] == "2023-01-01"
        assert filters["author"] == "Vaswani"

    def test_all_filters(self):
        text, filters = parse_query(
            "query category:cs.CV after:2023-01-01 before:2024-12-31 author:Doe entity:ResNet"
        )
        assert text == "query"
        assert filters["category"] == "cs.CV"
        assert filters["after"] == "2023-01-01"
        assert filters["before"] == "2024-12-31"
        assert filters["author"] == "Doe"
        assert filters["entity"] == "ResNet"

    def test_arxiv_id_extraction(self):
        text, filters = parse_query("arxiv:2310.01405 reinforcement learning")
        assert text == "reinforcement learning"
        assert filters["arxiv_id"] == "2310.01405"

    def test_arxiv_id_extraction_old_format(self):
        text, filters = parse_query("quant-ph/0101010")
        assert text == ""
        assert filters["arxiv_id"] == "quant-ph/0101010"

    def test_arxiv_id_extraction_no_prefix(self):
        text, filters = parse_query("2401.12345")
        assert text == ""
        assert filters["arxiv_id"] == "2401.12345"

    def test_empty_query(self):
        text, filters = parse_query("")
        assert text == ""
        assert all(v is None for v in filters.values())

    def test_only_filters_no_text(self):
        text, filters = parse_query("category:cs.AI author:Smith")
        assert text == ""
        assert filters["category"] == "cs.AI"
        assert filters["author"] == "Smith"

def test_search_db_timeout(client, monkeypatch):
    """Test that a database timeout during atomic lookup returns a 503 Service Unavailable."""
    from sqlalchemy.exc import OperationalError
    from sqlalchemy.orm import Session
    
    # Mock the database query to raise an OperationalError (simulating a timeout)
    def mock_query(*args, **kwargs):
        raise OperationalError("timeout", params=None, orig=None)
        
    monkeypatch.setattr(Session, "query", mock_query)
    
    response = client.post("/papers/search?query=arxiv:2310.01405")
    
    assert response.status_code == 503
    assert response.json()["detail"] == "Search database timeout"


def test_search_exact_match_found_no_text(client, db_session):
    # Add a mock paper
    from models import Paper
    from datetime import datetime
    p = Paper(arxiv_id="2310.01405", title="Exact Match Paper", published_date=datetime.now(), category="cs.AI", pdf_url="http://example.com/pdf")
    db_session.add(p)
    db_session.commit()
    
    response = client.post("/papers/search?query=arxiv:2310.01405")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Exact Match Paper"


def test_search_exact_match_found_with_text(client, db_session):
    # Add an exact match paper and some other paper
    from models import Paper
    from datetime import datetime
    p1 = Paper(arxiv_id="2310.01405", title="Exact Match Paper", published_date=datetime.now(), category="cs.AI", pdf_url="http://example.com/pdf")
    p2 = Paper(arxiv_id="1234.56789", title="Some other paper", published_date=datetime.now(), category="cs.CV", pdf_url="http://example.com/pdf")
    db_session.add(p1)
    db_session.add(p2)
    db_session.commit()
    
    # We pass some text so it does not bypass LLM
    response = client.post("/papers/search?query=arxiv:2310.01405 some text")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    # The exact match should be at rank 1 (index 0)
    assert data[0]["title"] == "Exact Match Paper"


def test_search_exact_match_not_found_no_text(client):
    response = client.post("/papers/search?query=arxiv:9999.99999")
    assert response.status_code == 200
    assert response.json() == []


def test_search_plain_text_query(client, db_session):
    """Test searching with standard keyword/semantic queries without arxiv_id."""
    from models import Paper
    from datetime import datetime
    p = Paper(
        arxiv_id="2401.00001",
        title="Attention Is All You Need with Transformers",
        summary="A novel neural network architecture based on self-attention mechanisms.",
        published_date=datetime.now(),
        category="cs.CL",
        pdf_url="http://example.com/pdf",
    )
    db_session.add(p)
    db_session.commit()

    response = client.post("/papers/search?query=transformer")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["arxiv_id"] == "2401.00001"


def test_search_plain_text_keyword_query(client, db_session):
    """Test standard keyword search without arxiv: prefix (checks is_postgres scoping)."""
    from models import Paper
    from datetime import datetime
    p = Paper(
        arxiv_id="2401.00002",
        title="Deep Reinforcement Learning for Agents",
        summary="A study on RL algorithms",
        published_date=datetime.now(),
        category="cs.AI",
        pdf_url="http://example.com/pdf",
    )
    db_session.add(p)
    db_session.commit()

    response = client.post("/papers/search?query=Reinforcement")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["title"] == "Deep Reinforcement Learning for Agents"


def test_search_plain_text_no_results(client):
    """Test searching with a query that matches no papers."""
    response = client.post("/papers/search?query=nonexistentqueryxyz")
    assert response.status_code == 200
    assert response.json() == []


def test_search_empty_query(client):
    response = client.post("/papers/search?query=")
    assert response.status_code == 200
    assert response.json() == []

    response = client.post("/papers/search?query=   ")
    assert response.status_code == 200
    assert response.json() == []


def test_search_sort_by_newest_and_title(client, db_session):
    """Test that sort_by='newest', 'date', and 'title' order results as expected."""
    from datetime import date
    from models import Paper

    older = Paper(
        arxiv_id="2401.10001",
        title="Zebra Agents in Practice",
        summary="A study on multi-agent orchestration.",
        published_date=date(2024, 1, 10),
        category="cs.AI",
        pdf_url="http://example.com/1.pdf",
    )
    newer = Paper(
        arxiv_id="2402.10002",
        title="Alpha Agents in Practice",
        summary="Another study on multi-agent orchestration.",
        published_date=date(2024, 2, 15),
        category="cs.AI",
        pdf_url="http://example.com/2.pdf",
    )
    db_session.add_all([older, newer])
    db_session.commit()

    newest_resp = client.post(
        "/papers/search?query=orchestration&sort_by=newest"
    )
    assert newest_resp.status_code == 200
    newest_data = newest_resp.json()
    assert [p["arxiv_id"] for p in newest_data[:2]] == ["2402.10002", "2401.10001"]

    date_resp = client.post(
        "/papers/search?query=orchestration&sort_by=date"
    )
    assert date_resp.status_code == 200
    assert [p["arxiv_id"] for p in date_resp.json()[:2]] == ["2402.10002", "2401.10001"]

    title_resp = client.post(
        "/papers/search?query=orchestration&sort_by=title"
    )
    assert title_resp.status_code == 200
    assert [p["title"] for p in title_resp.json()[:2]] == [
        "Alpha Agents in Practice",
        "Zebra Agents in Practice",
    ]


def test_search_filter_only_query(client, db_session):
    """Test searching with only metadata filters (e.g. category:cs.RO) and no residual text."""
    from datetime import date
    from models import Paper

    p_ro = Paper(
        arxiv_id="2403.00001",
        title="Robotic Manipulation Policy",
        summary="Learning dexterous policies.",
        published_date=date(2024, 3, 1),
        category="cs.RO",
        pdf_url="http://example.com/ro.pdf",
    )
    p_cl = Paper(
        arxiv_id="2403.00002",
        title="Language Modeling Basics",
        summary="Tokenization and scaling.",
        published_date=date(2024, 3, 2),
        category="cs.CL",
        pdf_url="http://example.com/cl.pdf",
    )
    db_session.add_all([p_ro, p_cl])
    db_session.commit()

    resp = client.post("/papers/search?query=category:cs.RO")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["arxiv_id"] == "2403.00001"


