from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean, Float
from datetime import datetime
from .base import Base


class PromptTemplate(Base):
    __tablename__ = "prompt_templates"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    template_text = Column(Text, nullable=False)
    version_tag = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class PatternExperimentResult(Base):
    """Stores pattern classification results for papers.

    Each row represents one paper's classification against the V6 CoT taxonomy.
    Originally populated by run_pattern_experiment.py batch jobs, now also
    populated by the production worker for auto-classification of new papers.
    """
    __tablename__ = "pattern_experiment_results"

    id = Column(Integer, primary_key=True, index=True)
    arxiv_id = Column(String, index=True, nullable=False)
    paper_title = Column(String, nullable=True)
    prompt_version = Column(String, index=True, nullable=False)
    model_name = Column(String, nullable=False)

    # Classification outputs
    is_agentic = Column(Boolean, nullable=True)
    primary_category = Column(String, nullable=True)
    reasoning = Column(Text, nullable=True)           # CoT reasoning trace
    patterns = Column(JSON, nullable=True)             # [{category, name, confidence, evidence}]
    raw_json = Column(JSON, nullable=True)             # Complete model output

    # Quality metrics
    num_patterns = Column(Integer, nullable=True)
    taxonomy_violations = Column(JSON, nullable=True)  # List of violation strings
    num_violations = Column(Integer, default=0)

    # Performance
    elapsed_seconds = Column(Float, nullable=True)
    error = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
