from pydantic import BaseModel, field_serializer
from typing import List, Optional, Union, Any
from datetime import date, datetime, timezone

class Citation(BaseModel):
    title: Any = None
    authors: Any = None
    url: Any = None
    raw: Any = ""
    resolved_id: Any = None

class PaperResponse(BaseModel):
    id: int
    arxiv_id: str
    title: str
    authors: Any = None
    summary: Any = None
    generated_summary: Any = None
    published_date: datetime
    category: str
    pdf_url: str
    citations: Any = None
    entities: Any = None
    summary_status: Optional[str] = None
    summary_error: Optional[Any] = None
    summary_attempted_at: Optional[datetime] = None

    @field_serializer("summary_attempted_at")
    def serialize_summary_attempted_at(self, dt: Optional[datetime]) -> Optional[str]:
        if dt is None:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()

class PaperSection(BaseModel):
    title: str
    level: int = 1
    content: str
    order: int

class PaperImage(BaseModel):
    filename: str
    page: int
    width: int
    height: int

class PaperFullTextResponse(BaseModel):
    arxiv_id: str
    title: str
    sections: List[PaperSection]
    images: List[PaperImage] = []
    word_count: int
    estimated_reading_minutes: int

class LibraryPaperResponse(PaperResponse):
    added_at: datetime
    list_name: str

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────────────
# Pattern Library Schemas
# ─────────────────────────────────────────────────────

class PatternDetail(BaseModel):
    """A single detected pattern within a paper."""
    category: str
    name: str
    confidence: float
    evidence: Optional[str] = None

class PaperPatternResponse(BaseModel):
    """A paper with its detected architectural patterns."""
    arxiv_id: str
    title: str
    published_date: Optional[datetime] = None
    category: Optional[str] = None          # arXiv category (e.g., cs.AI)
    is_agentic: Optional[bool] = None
    primary_pattern_category: Optional[str] = None
    patterns: List[PatternDetail] = []
    reasoning: Optional[str] = None

    class Config:
        from_attributes = True

class PatternCount(BaseModel):
    """Count of papers for a specific pattern."""
    name: str
    label: str
    paper_count: int

class CategoryOverview(BaseModel):
    """Overview of a taxonomy category with sub-pattern counts."""
    category: str
    label: str
    paper_count: int
    is_agentic_category: bool
    patterns: List[PatternCount] = []

class PatternOverviewResponse(BaseModel):
    """Full taxonomy overview with aggregate statistics."""
    total_classified: int
    total_agentic: int
    categories: List[CategoryOverview] = []
