"""models package — backward-compatible re-exports.

All 12 model classes plus Base are re-exported here so that every existing
``from models import X`` statement continues to work unchanged.
"""

from .base import Base
from .paper import Paper, PaperEmbedding
from .user import User, UserConfig, UserLibrary
from .jobs import JobLog, SummarizationMetric, BatchQueue
from .citation import CitationLink
from .pattern import PromptTemplate, PatternExperimentResult
from .queue import ReadingQueue, UserInterestProfile
from .query_cache import QueryEmbedding

__all__ = [
    "Base",
    "Paper",
    "PaperEmbedding",
    "User",
    "UserConfig",
    "UserLibrary",
    "JobLog",
    "SummarizationMetric",
    "BatchQueue",
    "CitationLink",
    "PromptTemplate",
    "PatternExperimentResult",
    "ReadingQueue",
    "UserInterestProfile",
    "QueryEmbedding",
]
