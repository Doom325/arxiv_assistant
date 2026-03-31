from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    UniqueConstraint,
)
from datetime import datetime

try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    from sqlalchemy import JSON

    def Vector(dim):
        return JSON

from .base import Base


class ReadingQueue(Base):
    __tablename__ = "reading_queue"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    paper_id = Column(Integer, ForeignKey("papers.id"), nullable=False)

    # Combined priority score (normalized 0-1)
    priority_score = Column(Float, default=0.0)

    # Individual signal scores
    interest_similarity = Column(Float, default=0.0)
    citation_impact = Column(Float, default=0.0)
    freshness_score = Column(Float, default=0.0)
    category_score = Column(Float, default=0.0)
    entity_overlap = Column(Float, default=0.0)
    peer_reads_score = Column(Float, default=0.0)

    # Status: unread, reading, read, skipped
    read_status = Column(String, default="unread", nullable=False)

    # How this paper entered the queue
    source = Column(String, default="bookmark", nullable=False)

    # For discovery papers: which engaged paper triggered the match
    best_match_paper_id = Column(
        Integer, ForeignKey("papers.id"), nullable=True
    )
    best_match_score = Column(Float, nullable=True)

    # Manual override (1=low, 2=medium, 3=high, None=auto)
    manual_priority = Column(Integer, nullable=True)

    added_at = Column(DateTime, default=datetime.utcnow)
    scored_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "paper_id", name="uq_user_paper"),
        Index(
            "idx_queue_user_status_score",
            "user_id",
            "read_status",
            priority_score.desc(),
        ),
    )


class UserInterestProfile(Base):
    __tablename__ = "user_interest_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id"), unique=True, nullable=False
    )
    interest_vector = Column(Vector(768), nullable=True)
    top_categories = Column(JSON, nullable=True)
    top_entities = Column(JSON, nullable=True)
    papers_used = Column(Integer, default=0)
    computed_at = Column(DateTime, default=datetime.utcnow)
