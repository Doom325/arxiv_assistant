from sqlalchemy import Column, Integer, String, Text, DateTime, Date, JSON, Float, ForeignKey
from datetime import datetime
from .base import Base


class JobLog(Base):
    __tablename__ = "job_logs"

    id = Column(Integer, primary_key=True, index=True)
    job_name = Column(String, index=True)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    status = Column(String) # SUCCESS, FAILED, WARNING, RUNNING
    # Rename to job_details to avoid any potential confusion with Base.metadata
    job_details = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)


class SummarizationMetric(Base):
    __tablename__ = "summarization_metrics"

    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(String, index=True) # arxiv_id
    num_chars = Column(Integer) # Length of extracted text
    num_input_tokens = Column(Integer)
    num_output_tokens = Column(Integer)
    peak_memory_mb = Column(Float) # MB or GB? processing usually in GB but let's store MB for precision
    model_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    # New fields for Failure Analysis
    file_size_bytes = Column(Integer, nullable=True)
    status = Column(String, default="SUCCESS") # SUCCESS, FAILED
    error_message = Column(Text, nullable=True)


class BatchQueue(Base):
    __tablename__ = "batch_queue"

    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id"), nullable=False)
    status = Column(String, default="PENDING") # PENDING, PROCESSING, COMPLETED, FAILED
    created_at = Column(DateTime, default=datetime.utcnow)


class CategoryPollState(Base):
    """Per-category high-water mark for the arXiv daily poller.

    Tracks the most recent ``submittedDate`` we have successfully ingested for
    each category. The next poll re-queries arXiv for everything from one day
    before the high-water mark onwards, which guarantees self-healing backfill
    if a run is missed (e.g. the host was offline for several days).
    """

    __tablename__ = "category_poll_state"

    category = Column(String, primary_key=True)
    last_successful_submitted_date = Column(Date, nullable=True)
    last_run_at = Column(DateTime, nullable=True)
    last_success_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
