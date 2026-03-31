"""Two-tier query embedding cache: in-memory LRU + PostgreSQL.

Lookup flow:
    1. Normalize + truncate query
    2. Compute SHA-256 cache key
    3. LRU check (under lock) → hit → return
    4. PostgreSQL check → hit → populate LRU, return
    5. Gemini API call → validate → write PostgreSQL + LRU → return
"""

from __future__ import annotations

import hashlib
import logging
import re
import threading
import time
from collections import OrderedDict
from datetime import datetime, timedelta

from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from config import settings
from models.query_cache import QueryEmbedding
from services.llm_service import embedding_service

logger = logging.getLogger(__name__)

_MAX_QUERY_LEN = 1000
_EXPECTED_DIM = 768
_STALE_HOURS = 24


def _normalize(query: str) -> str:
    """Lowercase, strip, collapse whitespace, truncate."""
    text = query.lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text[:_MAX_QUERY_LEN]


def _cache_key(
    normalized: str,
    task_type: str,
    model_name: str,
) -> str:
    """Deterministic SHA-256 key from query + task_type + model."""
    raw = f"{normalized}|{task_type}|{model_name}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _validate(embedding: list[float]) -> bool:
    """Return True only if embedding is a non-empty list of expected dim."""
    return (
        isinstance(embedding, list)
        and len(embedding) == _EXPECTED_DIM
    )


class QueryEmbeddingCache:
    """Per-process LRU backed by a shared PostgreSQL table."""

    def __init__(self, max_size: int | None = None) -> None:
        self._max_size = max_size or settings.QUERY_CACHE_LRU_SIZE
        self._lru: OrderedDict[str, list[float]] = OrderedDict()
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_or_generate(
        self,
        query: str,
        *,
        task_type: str = "retrieval_query",
        db: Session,
    ) -> list[float]:
        """Return embedding from cache or generate via LLM service."""
        start = time.monotonic()
        model_name = embedding_service.embedding_model
        normalized = _normalize(query)
        key = _cache_key(normalized, task_type, model_name)

        # --- Tier 1: LRU ---
        with self._lock:
            if key in self._lru:
                self._lru.move_to_end(key)
                elapsed = (time.monotonic() - start) * 1000
                logger.info(
                    "query_cache event=hit source=lru"
                    " latency_ms=%.2f key=%s",
                    elapsed,
                    key[:12],
                )
                return self._lru[key]

        # --- Tier 2: PostgreSQL ---
        row: QueryEmbedding | None = (
            db.query(QueryEmbedding)
            .filter(QueryEmbedding.query_hash == key)
            .first()
        )
        if row is not None:
            embedding = list(row.embedding)
            if _validate(embedding):
                row.hit_count += 1
                if row.last_used_at < datetime.utcnow() - timedelta(
                    hours=_STALE_HOURS,
                ):
                    row.last_used_at = datetime.utcnow()
                db.commit()
                self._lru_put(key, embedding)
                elapsed = (time.monotonic() - start) * 1000
                logger.info(
                    "query_cache event=hit source=postgres"
                    " latency_ms=%.2f key=%s",
                    elapsed,
                    key[:12],
                )
                return embedding

        # --- Tier 3: Gemini API ---
        embedding = embedding_service.generate_embedding(
            query, task_type=task_type,
        )

        if not _validate(embedding):
            elapsed = (time.monotonic() - start) * 1000
            logger.warning(
                "query_cache event=skip_invalid source=api"
                " latency_ms=%.2f dim=%d key=%s",
                elapsed,
                len(embedding) if isinstance(embedding, list) else -1,
                key[:12],
            )
            return embedding

        # Persist to PostgreSQL (upsert — race-safe)
        self._pg_write(db, key, normalized, task_type, model_name, embedding)

        # Populate LRU
        self._lru_put(key, embedding)

        elapsed = (time.monotonic() - start) * 1000
        logger.info(
            "query_cache event=miss source=api"
            " latency_ms=%.2f key=%s",
            elapsed,
            key[:12],
        )
        return embedding

    def invalidate_model(
        self,
        old_model: str,
        db: Session,
    ) -> int:
        """Delete all entries for a retired embedding model."""
        result = db.execute(
            delete(QueryEmbedding).where(
                QueryEmbedding.model_name == old_model,
            ),
        )
        db.commit()
        with self._lock:
            self._lru.clear()
        deleted: int = result.rowcount  # type: ignore[assignment]
        logger.info(
            "query_cache event=invalidate_model model=%s deleted=%d",
            old_model,
            deleted,
        )
        return deleted

    def cleanup_stale(
        self,
        db: Session,
        *,
        max_age_days: int = 30,
    ) -> int:
        """Remove entries unused for more than *max_age_days*."""
        cutoff = datetime.utcnow() - timedelta(days=max_age_days)
        result = db.execute(
            delete(QueryEmbedding).where(
                QueryEmbedding.last_used_at < cutoff,
            ),
        )
        db.commit()
        deleted: int = result.rowcount  # type: ignore[assignment]
        logger.info(
            "query_cache event=cleanup_stale cutoff=%s deleted=%d",
            cutoff.isoformat(),
            deleted,
        )
        return deleted

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _lru_put(self, key: str, embedding: list[float]) -> None:
        with self._lock:
            self._lru[key] = embedding
            self._lru.move_to_end(key)
            if len(self._lru) > self._max_size:
                self._lru.popitem(last=False)

    @staticmethod
    def _pg_write(
        db: Session,
        key: str,
        normalized: str,
        task_type: str,
        model_name: str,
        embedding: list[float],
    ) -> None:
        stmt = pg_insert(QueryEmbedding).values(
            query_hash=key,
            query_text=normalized,
            task_type=task_type,
            embedding=embedding,
            model_name=model_name,
        ).on_conflict_do_nothing(index_elements=["query_hash"])
        db.execute(stmt)
        db.commit()


query_cache = QueryEmbeddingCache()
