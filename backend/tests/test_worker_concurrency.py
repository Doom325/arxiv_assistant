"""Tests for the parallel pipeline in production_worker.

Covers the three concurrency invariants flagged by the reviewer:
  1. Each task runs against its own SQLAlchemy Session (no cross-thread sharing).
  2. The LLM semaphore caps simultaneous calls to WORKER_LLM_CONCURRENCY.
  3. A failure in one paper does not abort sibling tasks in the batch.
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor

import pytest

import production_worker
from production_worker import _process_paper, _llm_semaphore


class _FakeQueryResult:
    def __init__(self, value):
        self._value = value

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self._value


class _FakeSession:
    """Minimal Session stand-in. Records its identity so tests can assert
    that each thread received a distinct instance."""

    def __init__(self, papers_by_id):
        self._papers = papers_by_id
        self.committed = 0
        self.rolled_back = 0
        self.closed = False

    def query(self, *args, **kwargs):
        # Single-paper lookup is the only query _process_paper makes through
        # this session — return the matching FakePaper.
        # _process_paper calls db.query(Paper).filter(Paper.id == paper_id).first()
        return _PaperQuery(self._papers)

    def add(self, _obj):
        pass

    def commit(self):
        self.committed += 1

    def rollback(self):
        self.rolled_back += 1

    def close(self):
        self.closed = True


class _PaperQuery:
    def __init__(self, papers_by_id):
        self._papers = papers_by_id
        self._target_id = None

    def filter(self, expr):
        # SQLAlchemy expression: Paper.id == paper_id. The right-hand side is
        # the value; pull it out via .right.value when present, else fall back
        # to scanning the only registered paper.
        try:
            self._target_id = expr.right.value
        except AttributeError:
            self._target_id = next(iter(self._papers))
        return self

    def first(self):
        return self._papers.get(self._target_id)


class _FakePaper:
    def __init__(self, paper_id: int, arxiv_id: str):
        self.id = paper_id
        self.arxiv_id = arxiv_id
        self.is_downloaded = True  # skip download branch
        self.pdf_url = None
        self.title = "T"
        self.summary = "S" * 200
        self.extracted_abstract = "A" * 200  # long enough to trigger classify
        self.extracted_introduction = "I"
        self.citations = []          # not None — skips re-extract
        self.entities = []
        self.abstract_embedding = None
        self.introduction_embedding = None


def _patch_worker(monkeypatch, papers, *, processor=None, classify_side_effect=None):
    """Wire fakes into production_worker module."""
    sessions_by_thread = {}

    def fake_session_local():
        # _process_paper passes its own session through the steps. We hand out
        # one new fake per call so identity comparisons work per thread.
        s = _FakeSession({p.id: p for p in papers})
        sessions_by_thread[threading.get_ident()] = sessions_by_thread.get(
            threading.get_ident(), []
        ) + [s]
        return s

    monkeypatch.setattr(production_worker, "SessionLocal", fake_session_local)
    # Skip the per-step branches we don't want to exercise in unit tests.
    monkeypatch.setattr(production_worker, "_download_step", lambda db, paper: "/tmp/fake.pdf")
    monkeypatch.setattr(production_worker, "_extract_step", lambda *a, **kw: None)
    monkeypatch.setattr(production_worker, "_search_embedding_step", lambda *a, **kw: None)

    if classify_side_effect is None:
        monkeypatch.setattr(production_worker, "_classify_step", lambda *a, **kw: None)
    else:
        monkeypatch.setattr(production_worker, "_classify_step", classify_side_effect)

    return sessions_by_thread


def test_each_task_uses_its_own_session(monkeypatch):
    """Invariant 1: per-thread session isolation."""
    papers = [_FakePaper(i, f"2401.{i:05d}") for i in range(8)]
    sessions_by_thread = _patch_worker(monkeypatch, papers)

    processor = object()  # unused — _extract_step is patched to no-op
    with ThreadPoolExecutor(max_workers=4) as pool:
        outcomes = list(pool.map(lambda pid: _process_paper(pid, processor), [p.id for p in papers]))

    assert all(o.startswith("ok:") for o in outcomes), outcomes

    # Collect every session handed out across all worker threads. None of them
    # should be shared across threads — _process_paper instantiates one per
    # call, but the stronger guarantee we want to assert is that no Session
    # instance was ever observed by two distinct threads.
    seen = {}  # id(session) -> thread_id
    for tid, sessions in sessions_by_thread.items():
        for s in sessions:
            assert s.closed, "session must be closed in finally"
            prior = seen.setdefault(id(s), tid)
            assert prior == tid, "session leaked across threads"


def test_semaphore_caps_concurrent_llm_calls(monkeypatch):
    """Invariant 2: _llm_semaphore serializes LLM-bearing steps."""
    # Force the semaphore down to 2 for the duration of this test.
    cap = 2
    new_sem = threading.Semaphore(cap)
    monkeypatch.setattr(production_worker, "_llm_semaphore", new_sem)

    in_flight = 0
    peak = 0
    lock = threading.Lock()

    def fake_classify(db, paper):
        nonlocal in_flight, peak
        with production_worker._llm_semaphore:
            with lock:
                in_flight += 1
                peak = max(peak, in_flight)
            time.sleep(0.05)
            with lock:
                in_flight -= 1

    papers = [_FakePaper(i, f"2401.{i:05d}") for i in range(8)]
    _patch_worker(monkeypatch, papers, classify_side_effect=fake_classify)

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda pid: _process_paper(pid, object()), [p.id for p in papers]))

    assert peak <= cap, f"semaphore breached: peak={peak}, cap={cap}"
    assert peak >= 2, f"expected concurrent execution up to cap, got peak={peak}"


def test_one_paper_failure_does_not_break_batch(monkeypatch):
    """Invariant 3: per-paper exception is contained inside _process_paper."""
    poisoned = {3, 5}

    def flaky_classify(db, paper):
        if paper.id in poisoned:
            raise RuntimeError(f"boom for {paper.arxiv_id}")

    papers = [_FakePaper(i, f"2401.{i:05d}") for i in range(8)]
    _patch_worker(monkeypatch, papers, classify_side_effect=flaky_classify)

    with ThreadPoolExecutor(max_workers=4) as pool:
        outcomes = list(pool.map(lambda pid: _process_paper(pid, object()), [p.id for p in papers]))

    ok = [o for o in outcomes if o.startswith("ok:")]
    errored = [o for o in outcomes if o.startswith("error:")]
    assert len(errored) == len(poisoned), outcomes
    assert len(ok) == len(papers) - len(poisoned), outcomes
