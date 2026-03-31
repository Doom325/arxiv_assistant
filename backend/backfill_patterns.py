#!/usr/bin/env python3
"""
Specialized Backfill Script for Pattern Extraction.
Targets a specific date range and category.

Usage:
  PYTHONPATH=. python3 backfill_patterns.py --category cs.AI --start 2025-12-17 --end 2025-12-24
"""

import requests, json, time, sys, argparse
from datetime import datetime
from config import settings
from sqlalchemy import create_engine, text as sa_text
from sqlalchemy.orm import sessionmaker
from models import Base, PatternExperimentResult
from taxonomy import (
    VALID_CATEGORIES, VALID_PATTERNS, PROMPT_VERSION,
    validate_classification_output,
)
from services.llm_service import llm_service

# CONFIG
BATCH_COMMIT_SIZE = 5

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--category", type=str, default="cs.AI")
    parser.add_argument("--start", type=str, required=True)
    parser.add_argument("--end", type=str, required=True)
    parser.add_argument("--force", action="store_true", help="Overwrite existing results")
    args = parser.parse_args()

    engine = create_engine(settings.DATABASE_URL)
    PatternExperimentResult.__table__.create(engine, checkfirst=True)
    Session = sessionmaker(bind=engine)
    db = Session()

    # Find papers in range/cat. If not force, only those lacking results.
    if args.force:
        # Delete existing in range first to avoid unique constraint if any (arxiv_id lookup is common)
        # Actually PatternExperimentResult doesn't have a unique constraint on arxiv_id (multiple prompt versions allowed)
        # But for backfill, we want to replace the latest for this PV.
        where_clause = """
            p.category = :cat
            AND p.published_date >= :start
            AND p.published_date <= :end
        """
        print(f"  FORCE MODE: Will re-process all {args.category} papers in range.")
    else:
        where_clause = """
            p.category = :cat
            AND p.published_date >= :start
            AND p.published_date <= :end
            AND r.id IS NULL
        """

    rows = db.execute(sa_text(f"""
        SELECT p.arxiv_id, p.title, COALESCE(p.extracted_abstract, p.summary) as abstract
        FROM papers p
        LEFT JOIN pattern_experiment_results r ON p.arxiv_id = r.arxiv_id AND r.prompt_version = :pv
        WHERE {where_clause}
          AND COALESCE(p.extracted_abstract, p.summary) IS NOT NULL
        ORDER BY p.published_date DESC
    """), {"pv": PROMPT_VERSION, "cat": args.category, "start": args.start, "end": args.end}).fetchall()

    papers = [(r[0], r[1], (r[2] or "")[:800]) for r in rows]
    
    # Deduplicate arxiv_id in the processing list (in case multiple prompt versions existed)
    seen = set()
    deduped = []
    for p in papers:
        if p[0] not in seen:
            deduped.append(p)
            seen.add(p[0])
    papers = deduped

    print(f"\n{'═'*70}")
    print(f"  BACKFILL: {args.category} | {args.start} to {args.end}")
    print(f"  Papers to process: {len(papers)}")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'═'*70}\n")

    processed = 0
    batch_results = []

    for arxiv_id, title, abstract in papers:
        start_time = time.time()
        parsed = llm_service.classify_paper(title, abstract)
        elapsed = time.time() - start_time
        
        error = None if parsed else "Classification failed (no output)"
        
        # If force, delete OLD records for this arxiv_id and pv before saving new
        if args.force:
            db.execute(sa_text(
                "DELETE FROM pattern_experiment_results WHERE arxiv_id = :aid AND prompt_version = :pv"
            ), {"aid": arxiv_id, "pv": PROMPT_VERSION})
            
        if not parsed:
            result = PatternExperimentResult(
                arxiv_id=arxiv_id,
                paper_title=title[:200] if title else None,
                prompt_version=PROMPT_VERSION,
                model_name=getattr(llm_service, 'model_name', 'gemini'),
                num_violations=1,
                taxonomy_violations=["PARSE_FAILED"],
                elapsed_seconds=elapsed,
                error=error,
            )
            icon = "💥"
        else:
            issues = validate_classification_output(parsed)
            result = PatternExperimentResult(
                arxiv_id=arxiv_id,
                paper_title=title[:200] if title else None,
                prompt_version=PROMPT_VERSION,
                model_name=getattr(llm_service, 'model_name', 'gemini'),
                is_agentic=parsed.get("is_agentic"),
                primary_category=parsed.get("primary_category"),
                reasoning=parsed.get("reasoning"),
                patterns=parsed.get("patterns"),
                raw_json=parsed,
                num_patterns=len(parsed.get("patterns", [])),
                taxonomy_violations=issues if issues else None,
                num_violations=len(issues),
                elapsed_seconds=elapsed,
            )
            icon = "✅" if not issues else "⚠️"

        batch_results.append(result)
        processed += 1
        print(f"  [{processed:>3}/{len(papers)}] {icon} {elapsed:>4.1f}s | {arxiv_id} | {title[:40]}")

        if len(batch_results) >= BATCH_COMMIT_SIZE:
            db.add_all(batch_results)
            db.commit()
            batch_results = []

    if batch_results:
        db.add_all(batch_results)
        db.commit()

    print(f"\n{'═'*70}")
    print(f"  BACKFILL COMPLETE. Processed: {processed}")
    print(f"{'═'*70}\n")
    db.close()

if __name__ == "__main__":
    main()
