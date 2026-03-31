"""Tests for the query embedding cache service."""

import hashlib
import threading
from collections import OrderedDict
from unittest.mock import MagicMock, patch

import pytest

from services.query_embedding_cache import (
    QueryEmbeddingCache,
    _cache_key,
    _normalize,
    _validate,
)


# ── Normalization ────────────────────────────────────


class TestNormalize:
    def test_lowercase_and_strip(self) -> None:
        assert _normalize("  Hello World  ") == "hello world"

    def test_collapse_whitespace(self) -> None:
        assert _normalize("hello   world") == "hello world"

    def test_truncate(self) -> None:
        long = "a" * 2000
        assert len(_normalize(long)) == 1000

    def test_empty_string(self) -> None:
        assert _normalize("") == ""

    def test_tabs_and_newlines(self) -> None:
        assert _normalize("hello\t\nworld") == "hello world"


# ── Cache key ────────────────────────────────────────


class TestCacheKey:
    def test_deterministic(self) -> None:
        a = _cache_key("hello", "retrieval_query", "model-v1")
        b = _cache_key("hello", "retrieval_query", "model-v1")
        assert a == b

    def test_sha256_hex(self) -> None:
        key = _cache_key("q", "t", "m")
        assert len(key) == 64  # SHA-256 hex length

    def test_different_task_type_produces_different_key(self) -> None:
        a = _cache_key("hello", "retrieval_query", "m")
        b = _cache_key("hello", "retrieval_document", "m")
        assert a != b

    def test_different_model_produces_different_key(self) -> None:
        a = _cache_key("hello", "t", "model-v1")
        b = _cache_key("hello", "t", "model-v2")
        assert a != b

    def test_matches_manual_sha256(self) -> None:
        raw = "q|t|m"
        expected = hashlib.sha256(raw.encode()).hexdigest()
        assert _cache_key("q", "t", "m") == expected


# ── Validation ───────────────────────────────────────


class TestValidate:
    def test_valid_embedding(self) -> None:
        assert _validate([0.1] * 768) is True

    def test_empty_list_rejected(self) -> None:
        assert _validate([]) is False

    def test_wrong_dimension_rejected(self) -> None:
        assert _validate([0.1] * 100) is False

    def test_non_list_rejected(self) -> None:
        assert _validate("not a list") is False  # type: ignore[arg-type]

    def test_none_rejected(self) -> None:
        assert _validate(None) is False  # type: ignore[arg-type]


# ── LRU eviction ─────────────────────────────────────


class TestLruEviction:
    def test_evicts_oldest_when_full(self) -> None:
        cache = QueryEmbeddingCache(max_size=2)
        emb = [0.1] * 768
        cache._lru_put("k1", emb)
        cache._lru_put("k2", emb)
        cache._lru_put("k3", emb)

        assert "k1" not in cache._lru
        assert "k2" in cache._lru
        assert "k3" in cache._lru

    def test_move_to_end_on_access(self) -> None:
        cache = QueryEmbeddingCache(max_size=3)
        emb = [0.1] * 768
        cache._lru_put("k1", emb)
        cache._lru_put("k2", emb)
        cache._lru_put("k1", emb)  # re-access k1
        cache._lru_put("k3", emb)
        cache._lru_put("k4", emb)

        # k2 should have been evicted (oldest untouched)
        assert "k2" not in cache._lru
        assert "k1" in cache._lru


# ── Thread safety ────────────────────────────────────


class TestThreadSafety:
    def test_concurrent_lru_writes(self) -> None:
        cache = QueryEmbeddingCache(max_size=500)
        emb = [0.1] * 768

        def writer(start: int) -> None:
            for i in range(100):
                cache._lru_put(f"key-{start + i}", emb)

        threads = [
            threading.Thread(target=writer, args=(i * 100,))
            for i in range(5)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # No crash, and LRU respects max_size
        assert len(cache._lru) <= 500


# ── get_or_generate ──────────────────────────────────


class TestGetOrGenerate:
    @staticmethod
    def _make_cache() -> QueryEmbeddingCache:
        return QueryEmbeddingCache(max_size=64)

    @patch("services.query_embedding_cache.llm_service")
    def test_lru_hit_skips_db_and_api(
        self,
        mock_llm: MagicMock,
    ) -> None:
        mock_llm.embedding_model = "test-model"
        cache = self._make_cache()
        emb = [0.5] * 768

        # Pre-populate LRU
        normalized = _normalize("test query")
        key = _cache_key(normalized, "retrieval_query", "test-model")
        cache._lru_put(key, emb)

        db = MagicMock()
        result = cache.get_or_generate(
            "test query", task_type="retrieval_query", db=db,
        )

        assert result == emb
        db.query.assert_not_called()
        mock_llm.generate_embedding.assert_not_called()

    @patch("services.query_embedding_cache.llm_service")
    def test_miss_calls_api_and_caches(
        self,
        mock_llm: MagicMock,
    ) -> None:
        mock_llm.embedding_model = "test-model"
        mock_llm.generate_embedding.return_value = [0.3] * 768
        cache = self._make_cache()

        # DB returns no row
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        result = cache.get_or_generate(
            "new query", task_type="retrieval_query", db=db,
        )

        assert result == [0.3] * 768
        mock_llm.generate_embedding.assert_called_once()

    @patch("services.query_embedding_cache.llm_service")
    def test_invalid_embedding_not_cached(
        self,
        mock_llm: MagicMock,
    ) -> None:
        mock_llm.embedding_model = "test-model"
        mock_llm.generate_embedding.return_value = []  # invalid
        cache = self._make_cache()

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        result = cache.get_or_generate(
            "bad query", task_type="retrieval_query", db=db,
        )

        assert result == []
        # LRU should NOT contain this entry
        assert len(cache._lru) == 0

    @patch("services.query_embedding_cache.llm_service")
    def test_case_insensitive_hit(
        self,
        mock_llm: MagicMock,
    ) -> None:
        mock_llm.embedding_model = "test-model"
        cache = self._make_cache()
        emb = [0.7] * 768

        normalized = _normalize("Transformer Architecture")
        key = _cache_key(normalized, "retrieval_query", "test-model")
        cache._lru_put(key, emb)

        db = MagicMock()
        result = cache.get_or_generate(
            "  TRANSFORMER   architecture  ",
            task_type="retrieval_query",
            db=db,
        )

        assert result == emb
        mock_llm.generate_embedding.assert_not_called()
