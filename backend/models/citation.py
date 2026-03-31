from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class CitationLink(Base):
    __tablename__ = "citation_links"

    id = Column(Integer, primary_key=True, index=True)
    source_paper_id = Column(Integer, ForeignKey("papers.id"), nullable=False, index=True)
    target_arxiv_id = Column(String, nullable=True, index=True)
    target_title = Column(String, nullable=True, index=True)
    target_url = Column(String, nullable=True)
    resolved_paper_id = Column(Integer, ForeignKey("papers.id"), nullable=True, index=True)
    is_arxiv = Column(Boolean, default=True)
    published_year = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    source_paper = relationship("Paper", foreign_keys=[source_paper_id], backref="outbound_citations")
    resolved_paper = relationship("Paper", foreign_keys=[resolved_paper_id], backref="referenced_by")
