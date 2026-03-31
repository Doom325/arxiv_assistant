"""Tests for services/citation_service.py — resolve_citations and ARXIV_ID_PATTERN."""

from services.citation_service import ARXIV_ID_PATTERN, resolve_citations
from models import Paper, CitationLink


class TestArxivIdPattern:
    def test_matches_standard_arxiv_id(self):
        m = ARXIV_ID_PATTERN.search("arXiv:2201.12345")
        assert m is not None
        assert m.group(1) == "22"
        assert m.group(2) == "01"
        assert m.group(3) == "12345"

    def test_matches_bare_id(self):
        m = ARXIV_ID_PATTERN.search("2305.04567")
        assert m is not None
        assert m.group(1) == "23"
        assert m.group(3) == "04567"

    def test_matches_versioned_id(self):
        m = ARXIV_ID_PATTERN.search("2201.12345v3")
        assert m is not None
        assert m.group(3) == "12345"

    def test_matches_id_in_url(self):
        m = ARXIV_ID_PATTERN.search("https://arxiv.org/abs/2402.09876")
        assert m is not None
        assert m.group(1) == "24"
        assert m.group(3) == "09876"

    def test_no_match_for_non_arxiv(self):
        m = ARXIV_ID_PATTERN.search("This is a random citation about neural networks.")
        assert m is None

    def test_matches_four_digit_id(self):
        m = ARXIV_ID_PATTERN.search("arXiv:1901.0456")
        assert m is not None
        assert m.group(3) == "0456"


class TestResolveCitations:
    def test_empty_citations(self, db_session):
        paper = Paper(arxiv_id="2401.00001", title="Test Paper")
        db_session.add(paper)
        db_session.commit()

        result = resolve_citations(paper, [], db_session)
        assert result == 0

    def test_none_citations(self, db_session):
        paper = Paper(arxiv_id="2401.00001", title="Test Paper")
        db_session.add(paper)
        db_session.commit()

        result = resolve_citations(paper, None, db_session)
        assert result == 0

    def test_arxiv_citation_creates_link(self, db_session):
        source = Paper(arxiv_id="2401.00001", title="Source Paper")
        db_session.add(source)
        db_session.commit()

        citations = [
            {"raw": "Vaswani et al. arXiv:2301.12345", "title": "Attention Paper", "url": ""}
        ]
        result = resolve_citations(source, citations, db_session)
        assert result == 1

        link = db_session.query(CitationLink).filter(
            CitationLink.source_paper_id == source.id
        ).first()
        assert link is not None
        assert link.target_arxiv_id == "2301.12345"
        assert link.is_arxiv is True
        assert link.published_year == 2023

    def test_arxiv_citation_resolves_to_local_paper(self, db_session):
        target = Paper(arxiv_id="2301.12345", title="Target Paper")
        source = Paper(arxiv_id="2401.00001", title="Source Paper")
        db_session.add_all([target, source])
        db_session.commit()

        citations = [
            {"raw": "See arXiv:2301.12345", "title": "Target Paper", "url": ""}
        ]
        resolve_citations(source, citations, db_session)

        link = db_session.query(CitationLink).first()
        assert link.resolved_paper_id == target.id
        # Also check the citation JSON was updated with resolved_id
        assert source.citations[0]["resolved_id"] == "2301.12345"

    def test_non_arxiv_citation_creates_link(self, db_session):
        source = Paper(arxiv_id="2401.00001", title="Source Paper")
        db_session.add(source)
        db_session.commit()

        citations = [
            {"raw": "Deep Learning, Goodfellow et al. MIT Press", "title": "Deep Learning Book", "url": ""}
        ]
        result = resolve_citations(source, citations, db_session)
        assert result == 1

        link = db_session.query(CitationLink).first()
        assert link.target_arxiv_id is None
        assert link.is_arxiv is False
        assert link.target_title == "Deep Learning Book"

    def test_short_title_non_arxiv_skipped(self, db_session):
        """Non-arxiv citations with titles <= 5 chars are ignored."""
        source = Paper(arxiv_id="2401.00001", title="Source Paper")
        db_session.add(source)
        db_session.commit()

        citations = [
            {"raw": "Some ref", "title": "abc", "url": ""}
        ]
        result = resolve_citations(source, citations, db_session)
        assert result == 0

    def test_deduplicates_arxiv_links(self, db_session):
        source = Paper(arxiv_id="2401.00001", title="Source Paper")
        db_session.add(source)
        db_session.commit()

        citations = [
            {"raw": "arXiv:2301.12345", "title": "Paper A", "url": ""},
        ]
        # First call creates the link
        resolve_citations(source, citations, db_session)
        # Second call should not create a duplicate
        result = resolve_citations(source, citations, db_session)
        assert result == 0

        count = db_session.query(CitationLink).filter(
            CitationLink.source_paper_id == source.id
        ).count()
        assert count == 1

    def test_multiple_mixed_citations(self, db_session):
        source = Paper(arxiv_id="2401.00001", title="Source Paper")
        db_session.add(source)
        db_session.commit()

        citations = [
            {"raw": "arXiv:2301.11111", "title": "Paper A", "url": ""},
            {"raw": "Neural nets book", "title": "A Long Book Title", "url": "http://example.com"},
            {"raw": "arXiv:2302.22222", "title": "Paper B", "url": ""},
        ]
        result = resolve_citations(source, citations, db_session)
        assert result == 3

        arxiv_links = db_session.query(CitationLink).filter(
            CitationLink.is_arxiv == True
        ).count()
        assert arxiv_links == 2
