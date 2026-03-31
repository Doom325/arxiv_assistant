"""QueryEmbedding ORM model for the two-tier query embedding cache."""

from datetime import datetime

from sqlalchemy import Column, DateTime, Index, Integer, String, Text

from .base import Base

try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    from sqlalchemy import JSON

    def Vector(dim: int) -> type:  # noqa: N802
        return JSON


class QueryEmbedding(Base):
    """Cached embedding for a search/chat/timeline query.

    Keyed by SHA-256 of ``normalized_query|task_type|model_name`` so
    identical queries always resolve to the same row regardless of
    casing or whitespace.
    """

    __tablename__ = "query_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    query_hash = Column(String(64), unique=True, nullable=False, index=True)
    query_text = Column(Text, nullable=False)
    task_type = Column(String, nullable=False, default="retrieval_query")
    embedding = Column(Vector(768), nullable=False)
    model_name = Column(String, nullable=False)
    hit_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_query_cache_lookup", "query_hash"),
    )
