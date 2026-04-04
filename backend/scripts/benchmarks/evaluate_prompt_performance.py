#!/usr/bin/env python3
"""
Evaluate Prompt Performance (V6 CoT) on Gemma 3 27B
Selects 10 random papers from each category based on previous baseline runs,
re-runs the classification with Gemma 3 27B, and compares results.
"""

import requests
import json
import time
import sys
from datetime import datetime
from config import settings
from sqlalchemy import create_engine, text as sa_text
from sqlalchemy.orm import sessionmaker

# Ensure paths align if running from backend root
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from taxonomy import (
    V6_DIRECT_PROMPT, VALID_CATEGORIES, VALID_PATTERNS, PROMPT_VERSION,
    validate_classification_output
)

MODEL = "gemma3:27b"
OLLAMA_URL = "http://192.168.1.32:11434/api/chat"
OUTPUT_FILE = "prompt_evaluation_results_direct.md"
PROMPT_VERSION = "v6_direct"

def run_single_paper(title, abstract):
    """Run the V6 Direct prompt on one paper."""
    prompt = V6_DIRECT_PROMPT.format(title=title, abstract=abstract)
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
        if resp.status_code != 200:
            return elapsed, None, f"HTTP {resp.status_code}: {resp.text}"
        
        content = resp.json().get("message", {}).get("content", "")
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as e:
            return elapsed, None, f"JSON Error: {e} | Raw Content: {content} | Raw Resp: {resp.text}"
            
        return elapsed, parsed, None
    except Exception as e:
        elapsed = time.time() - start
        return elapsed, None, str(e)

def main():
    print(f"Connecting to DB: {settings.DATABASE_URL}")
    engine = create_engine(settings.DATABASE_URL)
    db = sessionmaker(bind=engine)()

    print("Fetching 10 random papers per category...")
    papers_to_test = []
    
    for cat in VALID_CATEGORIES:
        # We need to look up papers that already have this category assigned
        # Order by RANDOM() to get a fresh sample across runs
        query = sa_text("""
            SELECT p.arxiv_id, p.title, COALESCE(p.extracted_abstract, p.summary) as abstract, r.primary_category, r.is_agentic
            FROM papers p
            JOIN pattern_experiment_results r ON p.arxiv_id = r.arxiv_id
            WHERE r.primary_category = :cat
            ORDER BY RANDOM()
            LIMIT 10
        """)
        rows = db.execute(query, {"cat": cat}).fetchall()
        for r in rows:
            papers_to_test.append({
                "arxiv_id": r[0],
                "title": r[1] or "",
                "abstract": (r[2] or "")[:800],
                "baseline_category": r[3],
                "baseline_is_agentic": r[4]
            })

    db.close()
    
    total_papers = len(papers_to_test)
    print(f"Sampled {total_papers} papers in total.")
    if total_papers == 0:
        print("No papers found in the database with a prior classification. Aborting.")
        return

    results = []
    total_time = 0
    errors = 0

    print(f"\n{'═'*70}")
    print(f"  EVALUATING PROMPT: {PROMPT_VERSION} on {MODEL}")
    print(f"  Total papers: {total_papers}")
    print(f"{'═'*70}\n")

    for i, paper in enumerate(papers_to_test):
        elapsed, parsed, error = run_single_paper(paper['title'], paper['abstract'])
        total_time += elapsed

        got_agentic = None
        got_primary = None
        issues = []
        reasoning = ""

        if error or parsed is None:
            errors += 1
            issues = ["PARSE_FAILED"]
        else:
            issues = validate_classification_output(parsed)
            got_agentic = parsed.get("is_agentic")
            got_primary = parsed.get("primary_category")
            reasoning = parsed.get("reasoning", "")
        
        match_cat = (got_primary == paper['baseline_category'])
        match_agentic = (got_agentic == paper['baseline_is_agentic'])

        results.append({
            "arxiv_id": paper['arxiv_id'],
            "title": paper['title'][:70],
            "baseline_category": paper['baseline_category'],
            "got_primary": got_primary,
            "match_cat": match_cat,
            "baseline_is_agentic": paper['baseline_is_agentic'],
            "got_agentic": got_agentic,
            "match_agentic": match_agentic,
            "reasoning": reasoning,
            "issues": issues,
            "elapsed": elapsed,
            "error": error
        })

        status_str = "✅" if (match_cat and match_agentic) else "⚠️"
        if issues:
            status_str = "❌"
            
        print(f"  [{i+1:>3}/{total_papers}] {status_str} {elapsed:>5.1f}s | {paper['arxiv_id']} | Base: {paper['baseline_category']} -> Got: {got_primary}")

        # Iteratively write results
        cat_accuracy = sum(1 for r in results if r['match_cat']) / len(results) * 100
        agentic_accuracy = sum(1 for r in results if r['match_agentic']) / len(results) * 100
        violation_count = sum(len(r['issues']) for r in results)
        avg_time = sum(r['elapsed'] for r in results) / len(results) if len(results) else 0

        with open(OUTPUT_FILE, "w") as f:
            f.write(f"# Prompt Evaluation Results\n\n")
            f.write(f"**Model:** {MODEL}  \n")
            f.write(f"**Prompt Pattern Version:** {PROMPT_VERSION}  \n")
            f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}  \n")
            f.write(f"**Papers tested:** {len(results)} of {total_papers}  \n\n")

            f.write("## Overview Metrics\n\n")
            f.write("| Metric | Result |\n")
            f.write("|---|---|\n")
            f.write(f"| Average Time/Paper | {avg_time:.1f}s |\n")
            f.write(f"| Total Taxonomy Violations | {violation_count} |\n")
            f.write(f"| Parse / Network Errors | {errors} |\n")
            f.write(f"| `primary_category` Match Rate vs Baseline | {cat_accuracy:.1f}% |\n")
            f.write(f"| `is_agentic` Match Rate vs Baseline | {agentic_accuracy:.1f}% |\n")
            
            f.write("\n## Detailed Results\n\n")
            for cat in sorted(VALID_CATEGORIES):
                cat_results = [r for r in results if r['baseline_category'] == cat]
                if not cat_results:
                    continue
                cat_match_rate = sum(1 for r in cat_results if r['match_cat']) / len(cat_results) * 100
                f.write(f"### Baseline Category: `{cat}` (Match: {cat_match_rate:.1f}%)\n\n")
                for r in cat_results:
                    match_icon = "✅" if r['match_cat'] else "⚠️"
                    f.write(f"#### {match_icon} {r['arxiv_id']}: {r['title']}\n")
                    f.write(f"- **Time:** {r['elapsed']:.1f}s\n")
                    f.write(f"- **Category:** Got `{r['got_primary']}` (Expected: `{r['baseline_category']}`)\n")
                    f.write(f"- **Agentic:** Got `{r['got_agentic']}` (Expected: `{r['baseline_is_agentic']}`)\n")
                    if r['error']:
                        f.write(f"- **Error:** {r['error']}\n")
                    if r['issues']:
                        f.write(f"- **Violations:** {', '.join(r['issues'])}\n")
                    if r['reasoning']:
                        f.write(f"- **CoT Reasoning:**\n  > {r['reasoning'].replace(chr(10), chr(10)+'  > ')}\n")
                    f.write("\n")
                f.write("---\n\n")
    
    print(f"\n{'='*70}")
    print(f"Done! Results entirely written to {OUTPUT_FILE}")
    print(f"Final Category Match Rate: {cat_accuracy:.1f}%")
    print(f"Final Agentic Match Rate: {agentic_accuracy:.1f}%")

if __name__ == "__main__":
    main()
