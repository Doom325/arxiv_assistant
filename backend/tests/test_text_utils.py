"""Tests for core/text_utils.py"""
from core.text_utils import sanitize_text, extract_sections


class TestSanitizeText:
    def test_none_input(self):
        assert sanitize_text(None) == ""

    def test_empty_string(self):
        assert sanitize_text("") == ""

    def test_normal_text(self):
        assert sanitize_text("hello world") == "hello world"

    def test_null_bytes(self):
        assert sanitize_text("hello\x00world") == "helloworld"

    def test_surrogates(self):
        text = "hello" + chr(0xD800) + "world"
        result = sanitize_text(text)
        assert "\ud800" not in result
        assert "hello" in result
        assert "world" in result

    def test_mixed_bad_chars(self):
        text = "test\x00" + chr(0xDFFF) + "data"
        result = sanitize_text(text)
        assert result == "testdata"


class TestExtractSections:
    def test_both_sections(self):
        text = """
Abstract
This paper presents a new method.

1. Introduction
We introduce our approach here.

2. Related Work
Previous work includes...
"""
        result = extract_sections(text)
        assert "new method" in result["abstract"]
        assert "introduce" in result["introduction"]

    def test_abstract_only(self):
        text = """
Abstract
This paper presents a novel algorithm for optimization.

Methods
We tested on several benchmarks.
"""
        result = extract_sections(text)
        assert "novel algorithm" in result["abstract"]

    def test_intro_only(self):
        text = """
Some preamble text.

1. Introduction
Machine learning has made great progress.

2. Background
Neural networks are...
"""
        result = extract_sections(text)
        assert "great progress" in result["introduction"]

    def test_no_sections(self):
        text = "Just some random text without any section headers."
        result = extract_sections(text)
        assert result["abstract"] == ""
        assert result["introduction"] == ""

    def test_abstract_truncation(self):
        """When no introduction follows, abstract is truncated to 2000 chars."""
        text = "Abstract\n" + "x" * 3000
        result = extract_sections(text)
        assert len(result["abstract"]) <= 2000
