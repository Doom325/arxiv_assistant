#!/usr/bin/env python3
"""
500-Paper Pattern Extraction Experiment
Uses V6 CoT prompt on Gemma 3 4B. Saves all results to the
`pattern_experiment_results` table for large-scale analysis.

Usage:
  cd backend && PYTHONPATH=. python3 -u run_pattern_experiment.py [--limit 500] [--offset 0]
"""

import requests, json, time, sys, argparse
from datetime import datetime
from config import settings
from sqlalchemy import create_engine, text as sa_text
from sqlalchemy.orm import sessionmaker
from models import Base, PatternExperimentResult
from taxonomy import (
    V6_COT_PROMPT, VALID_CATEGORIES, VALID_PATTERNS, PROMPT_VERSION,
    validate_classification_output,
)

# ─────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────
MODEL = "gemma3:4b"
OLLAMA_URL = "http://localhost:11434/api/chat"
BATCH_COMMIT_SIZE = 10  # Commit to DB every N papers


# Alias for backward compatibility within this script
validate_output = validate_classification_output


def run_single_paper(title, abstract):
    """Run the CoT prompt on one paper. Returns (elapsed, parsed_json, error)."""
    prompt = V6_COT_PROMPT.format(title=title, abstract=abstract)
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "format": "json",
        "options": {"num_ctx": 8192, "temperature": 0.1}
    }
    start = time.time()
    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=300)
        elapsed = time.time() - start
        content = resp.json().get("message", {}).get("content", "")
        parsed = json.loads(content)
        return elapsed, parsed, None
    except Exception as e:
        elapsed = time.time() - start
        return elapsed, None, str(e)


def main():
    parser = argparse.ArgumentParser(description="Run pattern experiment on N papers")
    parser.add_argument("--limit", type=int, default=500, help="Number of papers to process")
    parser.add_argument("--offset", type=int, default=0, help="Offset for paper selection")
    args = parser.parse_args()

    engine = create_engine(settings.DATABASE_URL)

    # Create table if not exists
    PatternExperimentResult.__table__.create(engine, checkfirst=True)

    Session = sessionmaker(bind=engine)
    db = Session()

    # Check how many results already exist for this prompt version
    existing = db.execute(sa_text(
        "SELECT arxiv_id FROM pattern_experiment_results WHERE prompt_version = :pv"
    ), {"pv": PROMPT_VERSION}).fetchall()
    existing_ids = {r[0] for r in existing}
    print(f"Found {len(existing_ids)} existing results for {PROMPT_VERSION}", flush=True)

    # Fetch papers that have abstracts (prefer extracted_abstract, fall back to summary)
    # Order by published_date DESC to get recent papers first
    rows = db.execute(sa_text("""
        SELECT arxiv_id, title, COALESCE(extracted_abstract, summary) as abstract
        FROM papers
        WHERE COALESCE(extracted_abstract, summary) IS NOT NULL
          AND LENGTH(COALESCE(extracted_abstract, summary)) > 100
        ORDER BY published_date DESC
        LIMIT :limit OFFSET :offset
    """), {"limit": args.limit + len(existing_ids), "offset": args.offset}).fetchall()

    # Filter out already-processed papers
    papers = [(r[0], r[1], (r[2] or "")[:800]) for r in rows if r[0] not in existing_ids]
    papers = papers[:args.limit]

    print(f"\n{'═'*70}", flush=True)
    print(f"  PATTERN EXPERIMENT: {PROMPT_VERSION} on {MODEL}", flush=True)
    print(f"  Papers to process: {len(papers)}", flush=True)
    print(f"  Already processed: {len(existing_ids)}", flush=True)
    print(f"  Estimated time: {len(papers) * 8.5 / 60:.0f} minutes", flush=True)
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print(f"{'═'*70}\n", flush=True)

    processed = 0
    errors = 0
    total_time = 0
    batch_results = []

    for i, (arxiv_id, title, abstract) in enumerate(papers):
        elapsed, parsed, error = run_single_paper(title, abstract)
        total_time += elapsed

        if error or parsed is None:
            errors += 1
            result = PatternExperimentResult(
                arxiv_id=arxiv_id,
                paper_title=title[:200] if title else None,
                prompt_version=PROMPT_VERSION,
                model_name=MODEL,
                is_agentic=None,
                primary_category=None,
                reasoning=None,
                patterns=None,
                raw_json=None,
                num_patterns=0,
                taxonomy_violations=["PARSE_FAILED"],
                num_violations=1,
                elapsed_seconds=elapsed,
                error=error,
            )
            icon = "💥"
        else:
            issues = validate_output(parsed)
            got_agentic = parsed.get("is_agentic")
            got_primary = parsed.get("primary_category")
            patterns = parsed.get("patterns", [])
            reasoning = parsed.get("reasoning", "")

            result = PatternExperimentResult(
                arxiv_id=arxiv_id,
                paper_title=title[:200] if title else None,
                prompt_version=PROMPT_VERSION,
                model_name=MODEL,
                is_agentic=got_agentic,
                primary_category=got_primary,
                reasoning=reasoning,
                patterns=patterns,
                raw_json=parsed,
                num_patterns=len(patterns),
                taxonomy_violations=issues if issues else None,
                num_violations=len(issues),
                elapsed_seconds=elapsed,
                error=None,
            )
            icon = "✅" if not issues else "⚠️"

        batch_results.append(result)
        processed += 1

        # Progress log — compact single line
        agentic_str = str(result.is_agentic)[:5] if result.is_agentic is not None else "err"
        print(f"  [{processed:>4}/{len(papers)}] {icon} {elapsed:>5.1f}s | {agentic_str:<5} | {result.primary_category or 'err':<18} | viols={result.num_violations} | {(title or '')[:45]}", flush=True)

        # Batch commit
        if len(batch_results) >= BATCH_COMMIT_SIZE:
            try:
                db.add_all(batch_results)
                db.commit()
                batch_results = []
            except Exception as e:
                db.rollback()
                print(f"  ❌ DB COMMIT ERROR: {e}", flush=True)
                # Try one at a time
                for r in batch_results:
                    try:
                        db.add(r)
                        db.commit()
                    except:
                        db.rollback()
                batch_results = []

        # Periodic stats every 50 papers
        if processed % 50 == 0 and processed > 0:
            avg = total_time / processed
            eta = avg * (len(papers) - processed) / 60
            agentic_count = db.execute(sa_text(
                "SELECT COUNT(*) FROM pattern_experiment_results WHERE prompt_version = :pv AND is_agentic = true"
            ), {"pv": PROMPT_VERSION}).scalar() or 0
            total_saved = db.execute(sa_text(
                "SELECT COUNT(*) FROM pattern_experiment_results WHERE prompt_version = :pv"
            ), {"pv": PROMPT_VERSION}).scalar() or 0
            print(f"\n  ── CHECKPOINT ({processed}/{len(papers)}) ──", flush=True)
            print(f"     Avg: {avg:.1f}s/paper | ETA: {eta:.0f}min | Errors: {errors}", flush=True)
            print(f"     DB rows: {total_saved} | Agentic: {agentic_count}", flush=True)
            print(f"     Time elapsed: {total_time/60:.1f}min\n", flush=True)

    # Final commit
    if batch_results:
        try:
            db.add_all(batch_results)
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"  ❌ Final commit error: {e}", flush=True)

    # ── Final Summary ──
    avg = total_time / processed if processed else 0
    total_rows = db.execute(sa_text(
        "SELECT COUNT(*) FROM pattern_experiment_results WHERE prompt_version = :pv"
    ), {"pv": PROMPT_VERSION}).scalar() or 0
    agentic_count = db.execute(sa_text(
        "SELECT COUNT(*) FROM pattern_experiment_results WHERE prompt_version = :pv AND is_agentic = true"
    ), {"pv": PROMPT_VERSION}).scalar() or 0
    violation_count = db.execute(sa_text(
        "SELECT COUNT(*) FROM pattern_experiment_results WHERE prompt_version = :pv AND num_violations > 0"
    ), {"pv": PROMPT_VERSION}).scalar() or 0

    # Category distribution
    cat_dist = db.execute(sa_text("""
        SELECT primary_category, COUNT(*) as cnt
        FROM pattern_experiment_results
        WHERE prompt_version = :pv AND primary_category IS NOT NULL
        GROUP BY primary_category
        ORDER BY cnt DESC
    """), {"pv": PROMPT_VERSION}).fetchall()

    print(f"\n{'═'*70}", flush=True)
    print(f"  EXPERIMENT COMPLETE", flush=True)
    print(f"{'═'*70}", flush=True)
    print(f"  Processed:            {processed}", flush=True)
    print(f"  Total DB rows:        {total_rows}", flush=True)
    print(f"  Errors:               {errors}", flush=True)
    print(f"  Avg time/paper:       {avg:.1f}s", flush=True)
    print(f"  Total time:           {total_time/60:.1f} minutes", flush=True)
    print(f"", flush=True)
    print(f"  Agentic papers:       {agentic_count} ({agentic_count/total_rows*100:.1f}%)", flush=True)
    print(f"  Papers with viols:    {violation_count} ({violation_count/total_rows*100:.1f}%)", flush=True)
    print(f"", flush=True)
    print(f"  Category Distribution:", flush=True)
    for cat, cnt in cat_dist:
        bar = "█" * (cnt * 40 // total_rows) if total_rows else ""
        print(f"    {cat:<22} {cnt:>4} ({cnt/total_rows*100:>5.1f}%) {bar}", flush=True)
    print(f"{'═'*70}", flush=True)

    db.close()


if __name__ == "__main__":
    main()
