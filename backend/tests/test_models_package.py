"""Tests for models/ package — verify backward-compatible re-exports."""

from models import (
    Base,
    Paper,
    PaperEmbedding,
    User,
    UserConfig,
    UserLibrary,
    JobLog,
    SummarizationMetric,
    BatchQueue,
    CitationLink,
    PromptTemplate,
    PatternExperimentResult,
    ReadingQueue,
    UserInterestProfile,
)


class TestModelsPackage:
    def test_import_from_models(self):
        """All 12 model classes + Base should be importable from models."""
        assert Base is not None
        assert Paper is not None
        assert PaperEmbedding is not None
        assert User is not None
        assert UserConfig is not None
        assert UserLibrary is not None
        assert JobLog is not None
        assert SummarizationMetric is not None
        assert BatchQueue is not None
        assert CitationLink is not None
        assert PromptTemplate is not None
        assert PatternExperimentResult is not None
        assert ReadingQueue is not None
        assert UserInterestProfile is not None

    def test_all_models_importable(self):
        """Verify __all__ lists every expected export."""
        import models
        expected = {
            "Base", "Paper", "PaperEmbedding", "User", "UserConfig",
            "UserLibrary", "JobLog", "SummarizationMetric", "BatchQueue",
            "CitationLink", "PromptTemplate", "PatternExperimentResult",
            "ReadingQueue", "UserInterestProfile",
        }
        assert set(models.__all__) == expected

    def test_base_shared(self):
        """All models should share the same Base.metadata."""
        assert Paper.metadata is Base.metadata
        assert User.metadata is Base.metadata
        assert JobLog.metadata is Base.metadata
        assert CitationLink.metadata is Base.metadata
        assert PatternExperimentResult.metadata is Base.metadata

    def test_paper_embedding_relationship(self):
        """Paper.embeddings relationship should be configured."""
        assert hasattr(Paper, "embeddings")

    def test_all_tables_registered(self):
        """All 13 tables should be in Base.metadata."""
        table_names = sorted(Base.metadata.tables.keys())
        expected = [
            "batch_queue", "citation_links", "job_logs", "paper_embeddings",
            "papers", "pattern_experiment_results", "prompt_templates",
            "reading_queue", "summarization_metrics", "user_configs",
            "user_interest_profiles", "user_library", "users",
        ]
        assert table_names == expected
