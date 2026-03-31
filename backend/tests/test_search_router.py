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

    def test_empty_query(self):
        text, filters = parse_query("")
        assert text == ""
        assert all(v is None for v in filters.values())

    def test_only_filters_no_text(self):
        text, filters = parse_query("category:cs.AI author:Smith")
        assert text == ""
        assert filters["category"] == "cs.AI"
        assert filters["author"] == "Smith"
