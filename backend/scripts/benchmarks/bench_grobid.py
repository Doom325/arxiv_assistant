#!/usr/bin/env python3
"""
Benchmark GROBID citation extraction against the existing DB baseline.

Sends PDFs to a running GROBID instance (Docker service), parses the TEI-XML
references, then scores the output against papers.citations stored in the DB
(treated as ground truth — same caveat as bench_citation_model.py).

Usage:
    GROBID_URL=http://localhost:8070 \
    DB_HOST=192.168.86.26 \
    PDF_SAVE_DIR=/path/to/pdfs \
    python3 backend/scripts/benchmarks/bench_grobid.py

Env vars:
    GROBID_URL         GROBID service base URL (default: http://localhost:8070)
    N_PAPERS           Sample size (default: 25)
    DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASS  Postgres connection
    PDF_SAVE_DIR       Directory containing downloaded PDFs (default: data)
    OUTPUT_DIR         Where to write JSON results (default: script dir)
"""

import json
import os
import re
import sys
import time

import psycopg2

# ---------------------------------------------------------------------------
# Config — read env vars BEFORE importing backend modules so Pydantic
# Settings picks up our overrides at import time.
# ---------------------------------------------------------------------------
GROBID_URL = os.environ.get("GROBID_URL", "http://localhost:8070")
N_PAPERS = int(os.environ.get("N_PAPERS", "25"))

DB_HOST = os.environ.get("DB_HOST", "192.168.86.26")
DB_PORT = int(os.environ.get("DB_PORT", "5434"))
DB_NAME = os.environ.get("DB_NAME", "arxiv_db")
DB_USER = os.environ.get("DB_USER", "user")
DB_PASS = os.environ.get("DB_PASS", "password")

PDF_SAVE_DIR = os.environ.get("PDF_SAVE_DIR", "data")
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", os.path.dirname(__file__))

# Propagate into env so config.Settings() sees them at import time.
os.environ.setdefault("GROBID_URL", GROBID_URL)
os.environ.setdefault("PDF_SAVE_DIR", PDF_SAVE_DIR)

_BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

# Import after env is set so Settings() picks up our overrides.
from services.grobid_service import extract_references_from_pdf, is_alive  # noqa: E402
from core.pdf_utils import get_local_pdf_path  # noqa: E402

# ---------------------------------------------------------------------------
# Scoring helpers — inlined from bench_citation_model.py so this script is
# fully self-contained (the old bench may be deleted).
# ---------------------------------------------------------------------------
ARXIV_ID_PATTERN = re.compile(r'(?:arXiv:)?(\d{2})(\d{2})\.(\d{4,5})(?:v\d+)?')


def extract_arxiv_ids(citations: list[dict]) -> set[str]:
    """Pull canonical YYMM.NNNNN IDs from the `raw` field of each citation."""
    ids: set[str] = set()
    for cit in citations or []:
        raw = (cit.get("raw") or "") if isinstance(cit, dict) else ""
        for m in ARXIV_ID_PATTERN.finditer(raw):
            ids.add(f"{m.group(1)}{m.group(2)}.{m.group(3)}")
    return ids


_TOKEN_RE = re.compile(r"[a-z0-9]+")


def title_tokens(title: str) -> set[str]:
    if not title:
        return set()
    return set(_TOKEN_RE.findall(title.lower()))


def jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def title_match_stats(model_cits: list[dict], db_cits: list[dict], threshold: float = 0.5) -> dict:
    """Per-title best-Jaccard matching. A model title 'hits' if any DB title
    has token-Jaccard >= threshold (and vice versa for recall)."""
    model_titles = [(c.get("title") or "") if isinstance(c, dict) else "" for c in model_cits or []]
    db_titles = [(c.get("title") or "") if isinstance(c, dict) else "" for c in db_cits or []]
    model_tok = [title_tokens(t) for t in model_titles if t]
    db_tok = [title_tokens(t) for t in db_titles if t]

    if not model_tok or not db_tok:
        return {
            "title_precision": None,
            "title_recall": None,
            "title_f1": None,
            "n_model_titles": len(model_tok),
            "n_db_titles": len(db_tok),
        }

    model_hits = sum(1 for mt in model_tok if any(jaccard(mt, dt) >= threshold for dt in db_tok))
    db_hits = sum(1 for dt in db_tok if any(jaccard(dt, mt) >= threshold for mt in model_tok))

    precision = model_hits / len(model_tok)
    recall = db_hits / len(db_tok)
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    return {
        "title_precision": round(precision, 3),
        "title_recall": round(recall, 3),
        "title_f1": round(f1, 3),
        "n_model_titles": len(model_tok),
        "n_db_titles": len(db_tok),
    }


def arxiv_match_stats(model_ids: set[str], db_ids: set[str]) -> dict:
    if not db_ids and not model_ids:
        return {"arxiv_precision": None, "arxiv_recall": None, "arxiv_f1": None,
                "n_model_arxiv": 0, "n_db_arxiv": 0, "n_overlap": 0}
    overlap = model_ids & db_ids
    precision = (len(overlap) / len(model_ids)) if model_ids else None
    recall = (len(overlap) / len(db_ids)) if db_ids else None
    if precision is not None and recall is not None and (precision + recall) > 0:
        f1 = 2 * precision * recall / (precision + recall)
    else:
        f1 = None
    return {
        "arxiv_precision": round(precision, 3) if precision is not None else None,
        "arxiv_recall": round(recall, 3) if recall is not None else None,
        "arxiv_f1": round(f1, 3) if f1 is not None else None,
        "n_model_arxiv": len(model_ids),
        "n_db_arxiv": len(db_ids),
        "n_overlap": len(overlap),
    }


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def db_connect():
    return psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
                            user=DB_USER, password=DB_PASS)


def fetch_papers(n: int) -> list[dict]:
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("""
        SELECT arxiv_id, title, citations
        FROM papers
        WHERE citations IS NOT NULL
          AND jsonb_array_length(citations) >= 3
          AND full_text_sections IS NOT NULL
          AND jsonb_array_length(full_text_sections) > 5
        ORDER BY published_date DESC
        LIMIT %s
    """, (n,))
    out: list[dict] = []
    for arxiv_id, title, citations_json in cur.fetchall():
        cits = json.loads(citations_json) if isinstance(citations_json, str) else citations_json
        out.append({
            "arxiv_id": arxiv_id,
            "title": title,
            "db_citations": cits or [],
        })
    conn.close()
    return out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print(f"GROBID URL:       {GROBID_URL}")
    print(f"PDF_SAVE_DIR:     {PDF_SAVE_DIR}")
    print(f"DB:               {DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    print(f"Sample size:      {N_PAPERS}")
    print()

    # Health check — fail fast if GROBID is unreachable
    print(f"Health check → {GROBID_URL}/api/isalive")
    if not is_alive():
        print(f"FATAL: GROBID is unreachable at {GROBID_URL}")
        sys.exit(2)
    print("  → OK\n")

    print(f"Fetching up to {N_PAPERS} papers with citations from DB...")
    papers = fetch_papers(N_PAPERS)
    print(f"  → got {len(papers)} papers\n")
    if not papers:
        print("No qualifying papers in DB (need full_text_sections + citations >= 3). Exiting.")
        sys.exit(1)

    per_paper: list[dict] = []
    skipped_no_pdf = 0

    for i, p in enumerate(papers, 1):
        pdf_path = get_local_pdf_path(p["arxiv_id"], PDF_SAVE_DIR)
        if not pdf_path:
            skipped_no_pdf += 1
            print(f"[{i}/{len(papers)}] {p['arxiv_id']}  SKIP — PDF not found")
            continue

        print(f"[{i}/{len(papers)}] {p['arxiv_id']}  "
              f"db_cits={len(p['db_citations']):>2}  ", end="", flush=True)

        wall_start = time.time()
        grobid_cits = extract_references_from_pdf(pdf_path)
        wall_sec = time.time() - wall_start

        db_arxiv = extract_arxiv_ids(p["db_citations"])
        grobid_arxiv = extract_arxiv_ids(grobid_cits)
        arxiv_stats = arxiv_match_stats(grobid_arxiv, db_arxiv)
        title_stats = title_match_stats(grobid_cits, p["db_citations"])

        count_ratio = (len(grobid_cits) / len(p["db_citations"])) if p["db_citations"] else None

        row = {
            "arxiv_id": p["arxiv_id"],
            "title": p["title"],
            "db_n_citations": len(p["db_citations"]),
            "grobid_n_citations": len(grobid_cits),
            "citation_count_ratio": round(count_ratio, 3) if count_ratio is not None else None,
            "wall_sec": round(wall_sec, 2),
            **arxiv_stats,
            **title_stats,
            # Raw outputs for spot-checking worst papers
            "_db_titles": [(c.get("title") or "")[:120] for c in p["db_citations"][:30] if isinstance(c, dict)],
            "_grobid_titles": [(c.get("title") or "")[:120] for c in grobid_cits[:30] if isinstance(c, dict)],
        }
        per_paper.append(row)

        ax_f1 = arxiv_stats.get("arxiv_f1")
        ti_f1 = title_stats.get("title_f1")
        print(f"grobid_cits={len(grobid_cits):>2}  "
              f"axF1={ax_f1 if ax_f1 is not None else '  --'}  "
              f"tiF1={ti_f1 if ti_f1 is not None else '  --'}  "
              f"{wall_sec:>5.1f}s")

    if not per_paper:
        print("\nAll papers skipped — no PDFs found.")
        sys.exit(1)

    # ----- aggregate -----
    def mean(xs):
        xs = [x for x in xs if x is not None]
        return round(sum(xs) / len(xs), 3) if xs else None

    summary = {
        "method": "grobid",
        "grobid_url": GROBID_URL,
        "n_papers_attempted": len(per_paper),
        "n_papers_skipped_no_pdf": skipped_no_pdf,
        "mean_arxiv_precision": mean([r["arxiv_precision"] for r in per_paper]),
        "mean_arxiv_recall": mean([r["arxiv_recall"] for r in per_paper]),
        "mean_arxiv_f1": mean([r["arxiv_f1"] for r in per_paper]),
        "mean_title_precision": mean([r["title_precision"] for r in per_paper]),
        "mean_title_recall": mean([r["title_recall"] for r in per_paper]),
        "mean_title_f1": mean([r["title_f1"] for r in per_paper]),
        "mean_citation_count_ratio": mean([r["citation_count_ratio"] for r in per_paper]),
        "mean_wall_sec": mean([r["wall_sec"] for r in per_paper]),
        "total_wall_sec": round(sum(r["wall_sec"] for r in per_paper), 1),
    }

    # ----- report -----
    print(f"\n{'=' * 70}")
    print(f"  SUMMARY — GROBID  vs  DB baseline")
    print(f"{'=' * 70}")
    print(f"  Papers attempted:         {summary['n_papers_attempted']}")
    print(f"  Papers skipped (no PDF):  {summary['n_papers_skipped_no_pdf']}")
    print()
    print(f"  arXiv-ID overlap with DB (most objective signal):")
    print(f"    precision: {summary['mean_arxiv_precision']}")
    print(f"    recall:    {summary['mean_arxiv_recall']}")
    print(f"    F1:        {summary['mean_arxiv_f1']}")
    print()
    print(f"  Title overlap with DB (Jaccard >= 0.5):")
    print(f"    precision: {summary['mean_title_precision']}")
    print(f"    recall:    {summary['mean_title_recall']}")
    print(f"    F1:        {summary['mean_title_f1']}")
    print()
    print(f"  Volume:")
    print(f"    mean count ratio (grobid/db): {summary['mean_citation_count_ratio']}")
    print()
    print(f"  Latency:")
    print(f"    mean wall:  {summary['mean_wall_sec']}s / paper")
    print(f"    total wall: {summary['total_wall_sec']}s")

    # Worst 3 papers (by arxiv_f1, then title_f1)
    def worst_key(r):
        ax = r["arxiv_f1"] if r["arxiv_f1"] is not None else 1.0
        ti = r["title_f1"] if r["title_f1"] is not None else 1.0
        return (ax, ti)
    worst = sorted(per_paper, key=worst_key)[:3]

    print(f"\n  Worst 3 papers (lowest arxiv_f1, then title_f1):")
    for r in worst:
        print(f"  - {r['arxiv_id']}: axF1={r['arxiv_f1']}  tiF1={r['title_f1']}  "
              f"db_cits={r['db_n_citations']}  grobid_cits={r['grobid_n_citations']}")
        print(f"    DB titles     : {r['_db_titles'][:5]}")
        print(f"    GROBID titles : {r['_grobid_titles'][:5]}")

    # ----- save -----
    json_path = os.path.join(OUTPUT_DIR, "bench_grobid_results.json")
    with open(json_path, "w") as f:
        json.dump({"summary": summary, "per_paper": per_paper}, f, indent=2)
    print(f"\n  Raw results → {json_path}")


if __name__ == "__main__":
    main()
