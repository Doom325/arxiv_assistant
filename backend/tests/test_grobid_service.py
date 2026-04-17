"""Tests for GROBID TEI-XML parsing logic in services/grobid_service.py."""

import pytest
from lxml import etree

from services.grobid_service import (
    _build_raw,
    _full_text,
    _parse_authors,
    _parse_ids,
    _parse_tei,
    _parse_title,
    _parse_url,
    _text,
)

_NS = "http://www.tei-c.org/ns/1.0"


def _tei_wrap(*bibl_structs: str) -> bytes:
    """Wrap one or more <biblStruct> fragments in a minimal TEI envelope."""
    inner = "\n".join(bibl_structs)
    return f"""\
<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="{_NS}">
  <text>
    <back>
      <listBibl>
        {inner}
      </listBibl>
    </back>
  </text>
</TEI>""".encode("utf-8")


def _bibl(el: etree._Element):
    """Parse a raw XML string into an lxml Element for unit-testing helpers."""
    return el


def _make_bibl(xml_str: str) -> etree._Element:
    """Parse a <biblStruct> XML fragment into an lxml element."""
    full = f'<biblStruct xmlns="{_NS}">{xml_str}</biblStruct>'
    return etree.fromstring(full.encode("utf-8"))


# ── _text ────────────────────────────────────────────────────────────────


class TestText:
    def test_returns_text_at_xpath(self):
        node = _make_bibl('<analytic><title type="main">Deep Learning</title></analytic>')
        assert _text(node, "tei:analytic/tei:title") == "Deep Learning"

    def test_returns_none_for_missing_xpath(self):
        node = _make_bibl("<analytic/>")
        assert _text(node, "tei:analytic/tei:title") is None

    def test_returns_none_for_empty_text(self):
        node = _make_bibl('<analytic><title type="main">   </title></analytic>')
        assert _text(node, "tei:analytic/tei:title") is None

    def test_returns_none_for_none_node(self):
        assert _text(None, "tei:analytic/tei:title") is None


# ── _full_text ───────────────────────────────────────────────────────────


class TestFullText:
    def test_flattens_nested_elements(self):
        xml = f"""\
<biblStruct xmlns="{_NS}">
  <analytic>
    <title>Hello <hi>World</hi> Test</title>
  </analytic>
</biblStruct>"""
        node = etree.fromstring(xml.encode())
        result = _full_text(node)
        assert "Hello" in result
        assert "World" in result
        assert "Test" in result

    def test_returns_empty_for_none(self):
        assert _full_text(None) == ""

    def test_collapses_whitespace(self):
        xml = f"""\
<biblStruct xmlns="{_NS}">
  <analytic>
    <title>  Lots   of    space  </title>
  </analytic>
</biblStruct>"""
        node = etree.fromstring(xml.encode())
        result = _full_text(node)
        # No runs of multiple spaces
        assert "  " not in result


# ── _parse_title ─────────────────────────────────────────────────────────


class TestParseTitle:
    def test_analytic_main_title(self):
        bibl = _make_bibl(
            '<analytic><title type="main">Attention Is All You Need</title></analytic>'
        )
        assert _parse_title(bibl) == "Attention Is All You Need"

    def test_analytic_any_title_fallback(self):
        bibl = _make_bibl(
            '<analytic><title type="sub">A Subtitle</title></analytic>'
        )
        assert _parse_title(bibl) == "A Subtitle"

    def test_monogr_level_m_fallback(self):
        bibl = _make_bibl(
            '<monogr><title level="m">Conference Proceedings</title></monogr>'
        )
        assert _parse_title(bibl) == "Conference Proceedings"

    def test_monogr_any_title_fallback(self):
        bibl = _make_bibl(
            '<monogr><title level="j">Nature</title></monogr>'
        )
        assert _parse_title(bibl) == "Nature"

    def test_priority_analytic_over_monogr(self):
        bibl = _make_bibl(
            '<analytic><title type="main">Paper Title</title></analytic>'
            '<monogr><title level="m">Book Title</title></monogr>'
        )
        assert _parse_title(bibl) == "Paper Title"

    def test_empty_title_returns_empty_string(self):
        bibl = _make_bibl("<analytic/>")
        assert _parse_title(bibl) == ""

    def test_whitespace_only_title_skipped(self):
        bibl = _make_bibl(
            '<analytic><title type="main">   </title></analytic>'
            '<monogr><title level="m">Fallback</title></monogr>'
        )
        assert _parse_title(bibl) == "Fallback"


# ── _parse_authors ───────────────────────────────────────────────────────


class TestParseAuthors:
    def test_analytic_authors(self):
        bibl = _make_bibl("""\
<analytic>
  <author><persName><forename>Ashish</forename><surname>Vaswani</surname></persName></author>
  <author><persName><forename>Noam</forename><surname>Shazeer</surname></persName></author>
</analytic>""")
        authors = _parse_authors(bibl)
        assert authors == ["Ashish Vaswani", "Noam Shazeer"]

    def test_monogr_fallback(self):
        bibl = _make_bibl("""\
<monogr>
  <author><persName><forename>Ian</forename><surname>Goodfellow</surname></persName></author>
</monogr>""")
        authors = _parse_authors(bibl)
        assert authors == ["Ian Goodfellow"]

    def test_analytic_preferred_over_monogr(self):
        bibl = _make_bibl("""\
<analytic>
  <author><persName><forename>Alice</forename><surname>Smith</surname></persName></author>
</analytic>
<monogr>
  <author><persName><forename>Bob</forename><surname>Jones</surname></persName></author>
</monogr>""")
        authors = _parse_authors(bibl)
        assert authors == ["Alice Smith"]

    def test_missing_forename(self):
        bibl = _make_bibl("""\
<analytic>
  <author><persName><surname>Hinton</surname></persName></author>
</analytic>""")
        assert _parse_authors(bibl) == ["Hinton"]

    def test_missing_surname(self):
        bibl = _make_bibl("""\
<analytic>
  <author><persName><forename>Geoffrey</forename></persName></author>
</analytic>""")
        assert _parse_authors(bibl) == ["Geoffrey"]

    def test_no_authors_returns_empty_list(self):
        bibl = _make_bibl("<analytic><title>No Authors</title></analytic>")
        assert _parse_authors(bibl) == []

    def test_empty_persname_skipped(self):
        bibl = _make_bibl("""\
<analytic>
  <author><persName></persName></author>
  <author><persName><forename>Valid</forename><surname>Author</surname></persName></author>
</analytic>""")
        assert _parse_authors(bibl) == ["Valid Author"]


# ── _parse_ids ───────────────────────────────────────────────────────────


class TestParseIds:
    def test_arxiv_and_doi(self):
        bibl = _make_bibl("""\
<idno type="arXiv">2106.09685</idno>
<idno type="DOI">10.1234/example</idno>""")
        ids = _parse_ids(bibl)
        assert ids["arXiv"] == "2106.09685"
        assert ids["DOI"] == "10.1234/example"

    def test_no_ids(self):
        bibl = _make_bibl("<analytic/>")
        assert _parse_ids(bibl) == {}

    def test_empty_type_skipped(self):
        bibl = _make_bibl('<idno type="">some-value</idno>')
        assert _parse_ids(bibl) == {}

    def test_empty_text_skipped(self):
        bibl = _make_bibl('<idno type="arXiv"></idno>')
        assert _parse_ids(bibl) == {}


# ── _parse_url ───────────────────────────────────────────────────────────


class TestParseUrl:
    def test_ptr_target(self):
        bibl = _make_bibl('<ptr target="https://arxiv.org/abs/2106.09685"/>')
        assert _parse_url(bibl) == "https://arxiv.org/abs/2106.09685"

    def test_doi_fallback(self):
        bibl = _make_bibl('<idno type="DOI">10.1234/example</idno>')
        assert _parse_url(bibl) == "https://doi.org/10.1234/example"

    def test_ptr_preferred_over_doi(self):
        bibl = _make_bibl("""\
<ptr target="https://example.com/paper"/>
<idno type="DOI">10.1234/example</idno>""")
        assert _parse_url(bibl) == "https://example.com/paper"

    def test_no_url_returns_empty(self):
        bibl = _make_bibl("<analytic/>")
        assert _parse_url(bibl) == ""


# ── _build_raw ───────────────────────────────────────────────────────────


class TestBuildRaw:
    def test_full_entry(self):
        raw = _build_raw(
            title="My Paper",
            authors=["Alice", "Bob"],
            ids={"arXiv": "2301.00001", "DOI": "10.1234/x"},
            url="https://example.com",
            fallback_text="fallback",
        )
        assert "Alice, Bob" in raw
        assert "My Paper" in raw
        assert "arXiv:2301.00001" in raw
        assert "doi:10.1234/x" in raw
        assert "https://example.com" in raw

    def test_arxiv_id_in_raw(self):
        """The raw field must contain arXiv:XXXX.XXXXX so that
        citation_service's ARXIV_ID_PATTERN regex can match it."""
        import re

        ARXIV_ID_PATTERN = re.compile(r"\d{4}\.\d{4,5}")
        raw = _build_raw(
            title="Test",
            authors=[],
            ids={"arXiv": "2301.00001"},
            url="",
            fallback_text="",
        )
        assert ARXIV_ID_PATTERN.search(raw), f"arXiv ID not found in raw: {raw}"

    def test_fallback_when_empty(self):
        raw = _build_raw(
            title="", authors=[], ids={}, url="", fallback_text="Some raw citation text"
        )
        assert raw == "Some raw citation text"

    def test_no_duplicate_url(self):
        """URL already present as a piece should not appear twice."""
        raw = _build_raw(
            title="Paper",
            authors=[],
            ids={},
            url="https://example.com",
            fallback_text="",
        )
        assert raw.count("https://example.com") == 1


# ── _parse_tei (integration) ────────────────────────────────────────────


class TestParseTei:
    def test_normal_entry(self):
        xml = _tei_wrap("""\
<biblStruct>
  <analytic>
    <title type="main">LoRA: Low-Rank Adaptation</title>
    <author><persName><forename>Edward</forename><surname>Hu</surname></persName></author>
    <author><persName><forename>Yelong</forename><surname>Shen</surname></persName></author>
  </analytic>
  <idno type="arXiv">2106.09685</idno>
  <idno type="DOI">10.48550/arXiv.2106.09685</idno>
  <ptr target="https://arxiv.org/abs/2106.09685"/>
</biblStruct>""")
        results = _parse_tei(xml)
        assert len(results) == 1
        r = results[0]
        assert r["title"] == "LoRA: Low-Rank Adaptation"
        assert r["authors"] == ["Edward Hu", "Yelong Shen"]
        assert r["arxiv_id"] == "2106.09685"
        assert r["doi"] == "10.48550/arXiv.2106.09685"
        assert r["url"] == "https://arxiv.org/abs/2106.09685"
        assert "2106.09685" in r["raw"]

    def test_monogr_only_title(self):
        xml = _tei_wrap("""\
<biblStruct>
  <monogr>
    <title level="m">Deep Learning Book</title>
    <author><persName><forename>Ian</forename><surname>Goodfellow</surname></persName></author>
  </monogr>
</biblStruct>""")
        results = _parse_tei(xml)
        assert len(results) == 1
        assert results[0]["title"] == "Deep Learning Book"

    def test_author_fallback_to_monogr(self):
        xml = _tei_wrap("""\
<biblStruct>
  <analytic>
    <title type="main">Some Paper</title>
  </analytic>
  <monogr>
    <author><persName><forename>Jane</forename><surname>Doe</surname></persName></author>
  </monogr>
</biblStruct>""")
        results = _parse_tei(xml)
        assert len(results) == 1
        assert results[0]["authors"] == ["Jane Doe"]

    def test_empty_biblstruct_filtered(self):
        """An empty <biblStruct> should be skipped (raw is empty)."""
        xml = _tei_wrap("<biblStruct></biblStruct>")
        results = _parse_tei(xml)
        assert results == []

    def test_missing_authors_empty_list(self):
        xml = _tei_wrap("""\
<biblStruct>
  <analytic>
    <title type="main">Authorless Paper</title>
  </analytic>
</biblStruct>""")
        results = _parse_tei(xml)
        assert len(results) == 1
        assert results[0]["authors"] == []

    def test_doi_to_url_fallback(self):
        xml = _tei_wrap("""\
<biblStruct>
  <analytic>
    <title type="main">DOI Paper</title>
  </analytic>
  <idno type="DOI">10.1038/nature12373</idno>
</biblStruct>""")
        results = _parse_tei(xml)
        assert len(results) == 1
        assert results[0]["url"] == "https://doi.org/10.1038/nature12373"

    def test_malformed_xml_returns_empty(self):
        bad_xml = b"<not valid xml!!! <><>"
        results = _parse_tei(bad_xml)
        assert results == []

    def test_empty_tei_no_biblstruct(self):
        xml = f"""\
<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="{_NS}">
  <text><back><listBibl></listBibl></back></text>
</TEI>""".encode("utf-8")
        results = _parse_tei(xml)
        assert results == []

    def test_multiple_entries(self):
        b1 = """\
<biblStruct>
  <analytic><title type="main">Paper One</title></analytic>
</biblStruct>"""
        b2 = """\
<biblStruct>
  <analytic><title type="main">Paper Two</title></analytic>
  <idno type="arXiv">2301.00002</idno>
</biblStruct>"""
        b3 = """\
<biblStruct>
  <monogr>
    <title level="m">Book Three</title>
    <author><persName><forename>X</forename><surname>Y</surname></persName></author>
  </monogr>
</biblStruct>"""
        xml = _tei_wrap(b1, b2, b3)
        results = _parse_tei(xml)
        assert len(results) == 3
        assert results[0]["title"] == "Paper One"
        assert results[1]["title"] == "Paper Two"
        assert results[1]["arxiv_id"] == "2301.00002"
        assert results[2]["title"] == "Book Three"
        assert results[2]["authors"] == ["X Y"]

    def test_extra_fields_present(self):
        xml = _tei_wrap("""\
<biblStruct>
  <analytic><title type="main">Field Test</title></analytic>
  <idno type="arXiv">2401.12345</idno>
  <idno type="DOI">10.9999/test</idno>
</biblStruct>""")
        results = _parse_tei(xml)
        assert len(results) == 1
        r = results[0]
        assert "arxiv_id" in r
        assert "doi" in r
        assert r["arxiv_id"] == "2401.12345"
        assert r["doi"] == "10.9999/test"
        # Core contract fields also present
        assert "raw" in r
        assert "title" in r
        assert "authors" in r
        assert "url" in r

    def test_arxiv_id_regex_fires_on_raw(self):
        """Verify the raw field is matchable by the arXiv ID regex pattern
        used in citation_service for resolution."""
        import re

        ARXIV_ID_PATTERN = re.compile(r"\d{4}\.\d{4,5}")
        xml = _tei_wrap("""\
<biblStruct>
  <analytic><title type="main">Some Paper</title></analytic>
  <idno type="arXiv">2301.00001</idno>
</biblStruct>""")
        results = _parse_tei(xml)
        assert len(results) == 1
        match = ARXIV_ID_PATTERN.search(results[0]["raw"])
        assert match is not None
        assert match.group() == "2301.00001"
