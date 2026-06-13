#!/usr/bin/env python3
"""
Resumable backfill for pattern CLASSIFICATION and citation EXTRACTION via the
local LLM (nemotron3:nano), for papers from the last N months.

Context: classification used to fail on the dead gemma3:27b route and citations
were never captured (GROBID is disabled on the ARM Khadas deploy). Now that
nemotron3:nano handles both (with reasoning disabled -> fast, bounded JSON),
this script captures what was missed.

Design:
  - Processes papers in REVERSE chronological order (newest first).
  - Updates the database DIRECTLY (PatternExperimentResult, Paper.citations,
    CitationLink) and commits per paper.
  - RESTART-SAFE: progress lives in the DB, so re-running skips finished work:
      * classification done  = a PatternExperimentResult row with is_agentic
        IS NOT NULL for prompt_version=v6_cot (failed/None rows are redone).
      * citation done        = a JobLog(job_name='citation_backfill',
        status='SUCCESS') row for that arxiv_id (so 0-reference papers aren't
        retried forever).
  - Safe to Ctrl-C / kill at any time; the next run continues where it stopped.

Run (on the host with DB + PDFs, i.e. inside the Khadas backend container):
  PYTHONPATH=. python3 scripts/backfill_nemotron.py --months 6
  PYTHONPATH=. python3 scripts/backfill_nemotron.py --months 6 --task classify
  PYTHONPATH=. python3 scripts/backfill_nemotron.py --months 6 --task citations --download
"""
import argparse
import os
import sys
import time
from datetime import datetime, timedelta

# Make the backend package importable regardless of CWD.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text as sa_text
from sqlalchemy.orm import sessionmaker

from config import settings
from models import Base, Paper, PatternExperimentResult, JobLog
from taxonomy import PROMPT_VERSION, validate_classification_output
from services.llm_service import llm_service
from services.citation_service import resolve_citations
from core.pdf_utils import get_local_pdf_path, download_pdf, extract_text_from_pdf

CITATION_JOB = "citation_backfill"
MIN_ABSTRACT_CHARS = 50
# References live at the end of a paper; cap how much text we feed the LLM.
REF_TAIL_CHARS = 16000


def model_name() -> str:
    return getattr(llm_service, "classification_model", None) or \
        getattr(llm_service, "model_name", None) or \
        getattr(llm_service, "chat_model", "unknown")


def extract_references_text(full_text: str) -> str:
    """Heuristically isolate the references/bibliography section (end of paper)."""
    if not full_text:
        return ""
    low = full_text.lower()
    idx = -1
    for kw in ("\nreferences", "\nbibliography", "references\n", "bibliography\n"):
        j = low.rfind(kw)
        if j > idx:
            idx = j
    section = full_text[idx:] if idx != -1 else full_text
    # Bound the prompt: keep the tail (where refs are).
    if len(section) > REF_TAIL_CHARS:
        section = section[-REF_TAIL_CHARS:]
    return section


def log(db, status, arxiv_id, n=None, err=None):
    db.add(JobLog(
        job_name=CITATION_JOB, status=status, end_time=datetime.utcnow(),
        job_details={"arxiv_id": arxiv_id, "n": n}, error_message=err,
    ))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--months", type=int, default=6, help="Look back this many months")
    ap.add_argument("--task", choices=["both", "classify", "citations"], default="both")
    ap.add_argument("--pdf-dir", default=settings.PDF_SAVE_DIR)
    ap.add_argument("--download", action="store_true",
                    help="Download missing PDFs for citation extraction (slow; arXiv rate-limited)")
    ap.add_argument("--limit", type=int, default=0, help="Stop after N papers (0 = all)")
    args = ap.parse_args()

    cutoff = datetime.utcnow() - timedelta(days=30 * args.months)
    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(engine, checkfirst=True)
    db = sessionmaker(bind=engine)()

    # Candidate papers (reverse chronological).
    papers = db.execute(sa_text("""
        SELECT id, arxiv_id, title,
               COALESCE(extracted_abstract, summary) AS abstract,
               citations, pdf_url
        FROM papers
        WHERE published_date >= :cutoff
        ORDER BY published_date DESC
    """), {"cutoff": cutoff}).fetchall()

    # Resume sets (DB-state).
    done_classify = {r[0] for r in db.execute(sa_text("""
        SELECT DISTINCT arxiv_id FROM pattern_experiment_results
        WHERE prompt_version = :pv AND is_agentic IS NOT NULL
    """), {"pv": PROMPT_VERSION}).fetchall()}
    done_citations = set()
    for (jd,) in db.execute(sa_text(
        "SELECT job_details FROM job_logs WHERE job_name = :j AND status = 'SUCCESS'"
    ), {"j": CITATION_JOB}).fetchall():
        if isinstance(jd, dict) and jd.get("arxiv_id"):
            done_citations.add(jd["arxiv_id"])

    print(f"{'='*72}\n  NEMOTRON BACKFILL  task={args.task}  since={cutoff:%Y-%m-%d}  "
          f"candidates={len(papers)}\n  already done: classify={len(done_classify)} "
          f"citations={len(done_citations)}\n  started {datetime.now():%Y-%m-%d %H:%M:%S}\n{'='*72}")

    n_clf = n_cit = n_skip = n_err = processed = 0
    for row in papers:
        pid, arxiv_id, title, abstract, citations, pdf_url = row
        did_work = False

        # ---- Classification ----
        if args.task in ("both", "classify") and arxiv_id not in done_classify:
            if abstract and len(abstract) > MIN_ABSTRACT_CHARS:
                try:
                    t0 = time.time()
                    parsed = llm_service.classify_paper(title or "", abstract)
                    elapsed = time.time() - t0
                    # Replace any prior (failed) row for this version.
                    db.execute(sa_text(
                        "DELETE FROM pattern_experiment_results WHERE arxiv_id=:a AND prompt_version=:pv"
                    ), {"a": arxiv_id, "pv": PROMPT_VERSION})
                    if parsed:
                        issues = validate_classification_output(parsed)
                        db.add(PatternExperimentResult(
                            arxiv_id=arxiv_id, paper_title=(title or "")[:200],
                            prompt_version=PROMPT_VERSION, model_name=model_name(),
                            is_agentic=parsed.get("is_agentic"),
                            primary_category=parsed.get("primary_category"),
                            reasoning=parsed.get("reasoning", ""), patterns=parsed.get("patterns", []),
                            raw_json=parsed, num_patterns=len(parsed.get("patterns", [])),
                            taxonomy_violations=issues or None, num_violations=len(issues),
                            elapsed_seconds=elapsed, error=None,
                        ))
                        db.commit()
                        done_classify.add(arxiv_id)
                        n_clf += 1
                        did_work = True
                    else:
                        db.commit()  # cleared the old row; leave unmarked so it retries
                        n_err += 1
                except Exception as e:
                    db.rollback(); n_err += 1
                    print(f"  ! classify {arxiv_id}: {e}")

        # ---- Citations ----
        if args.task in ("both", "citations") and arxiv_id not in done_citations:
            has_cites = bool(citations) and len(citations) > 0
            if not has_cites:
                pdf = get_local_pdf_path(arxiv_id, args.pdf_dir)
                if not pdf and args.download and pdf_url:
                    pdf = download_pdf(pdf_url, arxiv_id, args.pdf_dir)
                    time.sleep(3)  # arXiv rate limit
                if not pdf:
                    n_skip += 1  # no PDF -> leave unmarked, retry later with --download
                else:
                    try:
                        refs = extract_references_text(extract_text_from_pdf(pdf))
                        cites = llm_service.parse_citations(refs) if refs else []
                        paper = db.query(Paper).filter(Paper.id == pid).first()
                        if paper is not None:
                            paper.citations = cites
                            resolve_citations(paper, cites, db)  # commits + creates CitationLink
                        log(db, "SUCCESS", arxiv_id, n=len(cites))
                        db.commit()
                        done_citations.add(arxiv_id)
                        n_cit += 1
                        did_work = True
                    except Exception as e:
                        db.rollback()
                        try:
                            log(db, "FAILED", arxiv_id, err=str(e)[:500]); db.commit()
                        except Exception:
                            db.rollback()
                        n_err += 1
                        print(f"  ! citations {arxiv_id}: {e}")
            else:
                # already had citations from before -> mark done so we don't re-check
                log(db, "SUCCESS", arxiv_id, n=len(citations)); db.commit()
                done_citations.add(arxiv_id)

        if did_work:
            processed += 1
            if processed % 10 == 0 or processed <= 5:
                print(f"  [{processed}] {arxiv_id} | clf={n_clf} cit={n_cit} skip={n_skip} err={n_err}")
            if args.limit and processed >= args.limit:
                print("  reached --limit, stopping")
                break

    print(f"{'='*72}\n  DONE  classified={n_clf}  citations={n_cit}  "
          f"skipped_no_pdf={n_skip}  errors={n_err}\n  finished {datetime.now():%Y-%m-%d %H:%M:%S}\n{'='*72}")
    db.close()


if __name__ == "__main__":
    main()
