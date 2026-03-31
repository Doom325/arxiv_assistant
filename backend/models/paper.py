from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Date, Boolean, ForeignKey, Float, Index, Computed
from sqlalchemy.orm import relationship
from datetime import datetime

try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    from sqlalchemy import JSON
    def Vector(dim):
        return JSON

from config import settings
from sqlalchemy.dialects.postgresql import TSVECTOR
from .base import Base


class Paper(Base):
    __tablename__ = "papers"

    id = Column(Integer, primary_key=True, index=True)
    arxiv_id = Column(String, unique=True, index=True)
    title = Column(String)
    authors = Column(JSON)  # List of strings
    summary = Column(Text)
    generated_summary = Column(Text, nullable=True)
    published_date = Column(DateTime)
    updated_date = Column(DateTime)
    category = Column(String)
    pdf_url = Column(String)
    is_downloaded = Column(Boolean, default=False)

    # Embedding for the summary/content (assuming 768 dim for Gemini)
    if "sqlite" in settings.DATABASE_URL:
         embedding = Column(JSON)
    else:
         embedding = Column(Vector(768))

    # Smart Extraction Fields
    extracted_abstract = Column(Text, nullable=True)
    extracted_introduction = Column(Text, nullable=True)
    citations = Column(JSON, nullable=True) # List of Dicts [{"title": ..., "authors": [...], "url": ..., "raw": ...}]
    entities = Column(JSON, nullable=True) # List of Dicts [{"type": ..., "value": ...}]
    full_text_sections = Column(JSON, nullable=True)  # Structured sections from full PDF text
    extracted_images = Column(JSON, nullable=True)  # List of image metadata dicts from PDF extraction
    in_drive_details = Column(JSON, nullable=True) # Dict of {list_name: bool}

    if "sqlite" in settings.DATABASE_URL:
        abstract_embedding = Column(JSON, nullable=True)
        introduction_embedding = Column(JSON, nullable=True)
    else:
        abstract_embedding = Column(Vector(768), nullable=True)
        introduction_embedding = Column(Vector(768), nullable=True)

    # Full-Text Search Vector
    if "sqlite" not in settings.DATABASE_URL:
        # Update search vector to include entities (weighted)
        search_vector = Column(TSVECTOR, Computed(
            "setweight(to_tsvector('english', coalesce(title, '')), 'A') || "
            "setweight(to_tsvector('english', coalesce(summary, '')), 'B') || "
            "setweight(to_tsvector('english', coalesce(entities::text, '')), 'A')",
            persisted=True
        ))
    else:
        search_vector = Column(Text, nullable=True)

    __table_args__ = (
        Index("idx_papers_search", "search_vector", postgresql_using="gin"),
    )


class PaperEmbedding(Base):
    __tablename__ = "paper_embeddings"
    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id", ondelete="CASCADE"))
    prompt_template_id = Column(Integer, ForeignKey("prompt_templates.id"))
    embedding = Column(Vector(768), nullable=False)
    embedding_config = Column(JSON, nullable=False)
    embedding_metadata = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    modified_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    paper = relationship("Paper", back_populates="embeddings")
    prompt_template = relationship("PromptTemplate")


Paper.embeddings = relationship("PaperEmbedding", back_populates="paper", cascade="all, delete-orphan")
