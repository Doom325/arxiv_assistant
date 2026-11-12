"""Unit tests for on-demand similar papers API and worker pipeline safeguards."""

from datetime import datetime
import time
from typing import List

from models import JobLog, Paper, PaperEmbedding, PatternExperimentResult
import production_worker
import routers.papers as papers_router
import services.llm_service as llm_module


def _vec(x: float, y: float, dim: int = 8) -> List[float]:
    base = [0.0] * dim
    base[0] = x
    base[1] = y
    return base


def _seed_paper(
    db_session,
    arxiv_id: str,
    title: str,
    summary: str | None = "Default abstract text for testing.",
    category: str = "cs.LG",
) -> Paper:
    paper = Paper(
        arxiv_id=arxiv_id,
        title=title,
        authors=["Author One"],
        summary=summary,
        published_date=datetime(2025, 9, 11),
        category=category,
        pdf_url=f"https://arxiv.org/pdf/{arxiv_id}.pdf",
        is_downloaded=False,
    )
    db_session.add(paper)
    db_session.commit()
    db_session.refresh(paper)
    return paper


def _seed_embedding(db_session, paper_id: int, vector: List[float]) -> PaperEmbedding:
    emb = PaperEmbedding(
        paper_id=paper_id,
        embedding=vector,
        embedding_config={"purpose": "search", "dimension": len(vector)},
        embedding_metadata={"source_model": "test-embed"},
    )
    db_session.add(emb)
    db_session.commit()
    return emb


def test_similar_endpoints_return_404_for_missing_paper(client) -> None:
    assert client.get("/papers/9999.99999/similar").status_code == 404
    assert client.post("/papers/9999.99999/similar").status_code == 404
    assert client.post("/papers/999999/similar").status_code == 404


def test_get_similar_papers_returns_empty_when_unembedded(client, db_session) -> None:
    ref = _seed_paper(
        db_session,
        "2509.14252v2",
        "LLM-JEPA: Large Language Models Meet Joint Embedding Predictive Architectures",
    )
    other = _seed_paper(db_session, "2501.00001v1", "I-JEPA Vision Backbone")
    _seed_embedding(db_session, other.id, _vec(1.0, 0.0))

    resp = client.get(f"/papers/{ref.arxiv_id}/similar")
    assert resp.status_code == 200
    assert resp.json() == []


def test_post_similar_generates_caches_and_ranks_neighbors(
    client, db_session, monkeypatch
) -> None:
    ref = _seed_paper(
        db_session,
        "2509.14252v2",
        "LLM-JEPA: Large Language Models Meet Joint Embedding Predictive Architectures",
        summary="Joint Embedding Predictive Architectures for language models.",
    )
    close_paper = _seed_paper(db_session, "2502.00001v1", "Predictive Joint Embeddings")
    far_paper = _seed_paper(db_session, "2502.00002v1", "Compiler Register Allocation")
    _seed_embedding(db_session, close_paper.id, _vec(0.98, 0.02))
    _seed_embedding(db_session, far_paper.id, _vec(0.0, 1.0))

    calls: list[str] = []

    class FakeEmbedder:
        embedding_model = "gemini-embedding-001"

        def sanitize_text(self, text: str) -> str:
            return text

        def generate_embedding(self, text: str) -> List[float]:
            calls.append(text)
            return _vec(1.0, 0.0)

    monkeypatch.setattr(llm_module, "embedding_service", FakeEmbedder())

    post_resp = client.post(f"/papers/{ref.arxiv_id}/similar?limit=6")
    assert post_resp.status_code == 200
    returned_ids = [item["arxiv_id"] for item in post_resp.json()]
    assert returned_ids == ["2502.00001v1", "2502.00002v1"]
    assert len(calls) == 1

    stored = (
        db_session.query(PaperEmbedding)
        .filter(PaperEmbedding.paper_id == ref.id)
        .first()
    )
    assert stored is not None
    assert stored.embedding_metadata.get("trigger") == "on_demand"

    # Subsequent GET now uses the persisted embedding without calling the provider.
    get_resp = client.get(f"/papers/{ref.arxiv_id}/similar")
    assert get_resp.status_code == 200
    assert [item["arxiv_id"] for item in get_resp.json()] == [
        "2502.00001v1",
        "2502.00002v1",
    ]
    assert len(calls) == 1


def test_post_similar_skips_recompute_unless_forced(
    client, db_session, monkeypatch
) -> None:
    ref = _seed_paper(db_session, "2509.14252v2", "Cached Paper")
    neighbor = _seed_paper(db_session, "2503.00001v1", "Neighbor Paper")
    _seed_embedding(db_session, ref.id, _vec(1.0, 0.0))
    _seed_embedding(db_session, neighbor.id, _vec(0.9, 0.1))

    calls: list[str] = []

    class FakeEmbedder:
        embedding_model = "gemini-embedding-001"

        def sanitize_text(self, text: str) -> str:
            return text

        def generate_embedding(self, text: str) -> List[float]:
            calls.append(text)
            return _vec(0.0, 1.0)

    monkeypatch.setattr(llm_module, "embedding_service", FakeEmbedder())

    cached_resp = client.post(f"/papers/{ref.id}/similar")
    assert cached_resp.status_code == 200
    assert len(calls) == 0

    forced_resp = client.post(f"/papers/{ref.id}/similar?force=true")
    assert forced_resp.status_code == 200
    assert len(calls) == 1
    assert (
        db_session.query(PaperEmbedding).filter(PaperEmbedding.paper_id == ref.id).count()
        == 1
    )


def test_post_similar_falls_back_to_keywords_when_embedder_fails(
    client, db_session, monkeypatch
) -> None:
    ref = _seed_paper(
        db_session,
        "2509.14252v2",
        "Joint Embedding Predictive Architectures for Transformers",
        summary="Training transformers in representation space.",
    )
    relevant = _seed_paper(
        db_session,
        "2504.00010v1",
        "Joint Embedding Predictive Architectures in Vision",
        summary="Self-supervised predictive architectures.",
    )
    _seed_paper(
        db_session,
        "2504.00011v1",
        "Quantum Error Correction Surface Codes",
        summary="Topological qubits on superconducting lattices.",
    )

    class FailingEmbedder:
        embedding_model = "offline-local"

        def sanitize_text(self, text: str) -> str:
            return text

        def generate_embedding(self, text: str) -> List[float]:
            raise RuntimeError("LiteLLM upstream offline")

    monkeypatch.setattr(llm_module, "embedding_service", FailingEmbedder())

    resp = client.post(f"/papers/{ref.arxiv_id}/similar")
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 1
    assert results[0]["arxiv_id"] == relevant.arxiv_id
    assert (
        db_session.query(PaperEmbedding).filter(PaperEmbedding.paper_id == ref.id).count()
        == 0
    )


def test_similar_validates_limit_bounds(client, db_session) -> None:
    ref = _seed_paper(db_session, "2509.14252v2", "Bounds Check Paper")
    assert client.get(f"/papers/{ref.id}/similar?limit=0").status_code == 422
    assert client.post(f"/papers/{ref.id}/similar?limit=51").status_code == 422


def test_post_similar_times_out_cleanly_and_deduplicates_neighbors(
    client, db_session, monkeypatch
) -> None:
    ref = _seed_paper(
        db_session,
        "2509.14252v2",
        "Joint Embedding Predictive Architectures",
        summary="Representation prediction for language models.",
    )
    neighbor = _seed_paper(
        db_session,
        "2505.00001v1",
        "Joint Embedding Predictive Backbones",
        summary="Representation prediction in latent space.",
    )
    _seed_embedding(db_session, neighbor.id, _vec(0.95, 0.05))
    _seed_embedding(db_session, neighbor.id, _vec(0.94, 0.06))

    class SlowEmbedder:
        embedding_model = "slow-local"

        def sanitize_text(self, text: str) -> str:
            return text

        def generate_embedding(self, _text: str) -> List[float]:
            time.sleep(0.15)
            return _vec(1.0, 0.0)

    monkeypatch.setattr(papers_router, "_EMBED_TIMEOUT_SECONDS", 0.02)
    monkeypatch.setattr(llm_module, "embedding_service", SlowEmbedder())

    timeout_resp = client.post(f"/papers/{ref.arxiv_id}/similar")
    assert timeout_resp.status_code == 200
    assert [item["arxiv_id"] for item in timeout_resp.json()] == [neighbor.arxiv_id]

    _seed_embedding(db_session, ref.id, _vec(1.0, 0.0))
    dedup_resp = client.get(f"/papers/{ref.arxiv_id}/similar?limit=6")
    assert dedup_resp.status_code == 200
    assert [item["arxiv_id"] for item in dedup_resp.json()] == [neighbor.arxiv_id]


def test_worker_extract_step_prevents_null_abstract_loop(
    db_session, monkeypatch
) -> None:
    paper_with_summary = _seed_paper(
        db_session,
        "2611.08286v1",
        "Headerless PDF Paper",
        summary="Canonical arXiv abstract from metadata.",
    )
    paper_with_summary.is_downloaded = True
    paper_without_summary = _seed_paper(
        db_session,
        "2611.08287v1",
        "No Metadata Summary Paper",
        summary=None,
    )
    paper_without_summary.is_downloaded = True
    db_session.commit()

    class StubProcessor:
        def process_pdf(self, _pdf_path: str) -> dict:
            return {
                "sections": {"abstract": "", "introduction": "Intro body"},
                "citations": [],
                "entities": [],
                "embeddings": {"abstract": [], "introduction": []},
            }

    monkeypatch.setattr(production_worker, "resolve_citations", lambda *a, **kw: None)

    production_worker._extract_step(
        db_session, paper_with_summary, StubProcessor(), "/tmp/a.pdf"
    )
    production_worker._extract_step(
        db_session, paper_without_summary, StubProcessor(), "/tmp/b.pdf"
    )

    assert paper_with_summary.extracted_abstract == "Canonical arXiv abstract from metadata."
    assert paper_without_summary.extracted_abstract == production_worker.NO_ABSTRACT_EXTRACTED
    assert (
        production_worker._first_usable_text(
            paper_without_summary.summary,
            paper_without_summary.extracted_abstract,
            paper_without_summary.title,
        )
        == "No Metadata Summary Paper"
    )

    # Once embeddings exist, neither paper remains trapped in _fetch_pending_paper_ids.
    _seed_embedding(db_session, paper_with_summary.id, _vec(1.0, 0.0))
    _seed_embedding(db_session, paper_without_summary.id, _vec(0.0, 1.0))
    pending = production_worker._fetch_pending_paper_ids(db_session, batch_size=20)
    assert paper_with_summary.id not in pending
    assert paper_without_summary.id not in pending


def test_worker_classify_step_defers_when_local_llm_returns_none(
    db_session, monkeypatch
) -> None:
    paper = _seed_paper(
        db_session,
        "2611.08082v1",
        "Agentic Orchestration Study",
        summary="A" * 120,
    )
    paper.extracted_abstract = "A" * 120
    db_session.commit()

    class OfflineLLM:
        chat_model = "nemotron3:nano"

        def classify_paper(self, _title: str, _abstract: str):
            return None

    monkeypatch.setattr(production_worker, "llm_service", OfflineLLM())
    production_worker._classify_step(db_session, paper)

    assert (
        db_session.query(PatternExperimentResult)
        .filter(PatternExperimentResult.arxiv_id == paper.arxiv_id)
        .count()
        == 0
    )
    failed_log = (
        db_session.query(JobLog)
        .filter(JobLog.job_name == "worker_classify")
        .order_by(JobLog.id.desc())
        .first()
    )
    assert failed_log is not None
    assert failed_log.status == "FAILED"

    class OnlineLLM:
        chat_model = "nemotron3:nano"

        def classify_paper(self, _title: str, _abstract: str) -> dict:
            return {
                "is_agentic": True,
                "primary_category": "TOOL_USE",
                "reasoning": "Uses external tools iteratively.",
                "patterns": [],
            }

    monkeypatch.setattr(production_worker, "llm_service", OnlineLLM())
    production_worker._classify_step(db_session, paper)

    assert (
        db_session.query(PatternExperimentResult)
        .filter(PatternExperimentResult.arxiv_id == paper.arxiv_id)
        .count()
        == 1
    )
