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

from models import Paper, PaperEmbedding
from datetime import date

def test_search_papers_with_arxiv_id(client, db_session):
    # Create a paper and its embedding
    paper = Paper(
        arxiv_id="2310.01405",
        title="Test Paper ID Match",
        authors="Test Author",
        summary="Test Summary",
        published_date=date(2023, 10, 1),
        category="cs.AI",
        pdf_url="http://example.com/pdf",
    )
    db_session.add(paper)
    db_session.commit()

    paper_embedding = PaperEmbedding(
        paper_id=paper.id,
        embedding=[0.1] * 3072,
        embedding_config={"model": "test"},
        embedding_metadata={"type": "full"}
    )
    db_session.add(paper_embedding)
    db_session.commit()

    # Search with arxiv: ID using POST and 'query' param
    response = client.post("/papers/search?query=arxiv:2310.01405")
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) == 1
    assert data[0]["arxiv_id"] == "2310.01405"
