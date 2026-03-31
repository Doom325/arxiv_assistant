#!/usr/bin/env python3
"""
Direct Comparison: Gemma 3 4B vs Gemini 3 Flash Preview (V6 CoT)
Target: 30 papers already classified by Gemini.
"""

import requests, json, time, sys
from config import settings
from sqlalchemy import create_engine, text as sa_text
from sqlalchemy.orm import Session
from models import PatternExperimentResult
from taxonomy import (
    V6_COT_PROMPT, PROMPT_VERSION, validate_classification_output
)

MODEL = "gemma3:4b"
OLLAMA_URL = "http://localhost:11434/api/chat"
GEMINI_MODEL = "gemini-3-flash-preview"

def run_ollama(title, abstract):
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
        return time.time() - start, None, str(e)

def main():
    engine = create_engine(settings.DATABASE_URL)
    with Session(engine) as session:
        # 1. Get Gemini results
        gemini_results = session.query(PatternExperimentResult).filter(
            PatternExperimentResult.model_name == GEMINI_MODEL,
            PatternExperimentResult.prompt_version == PROMPT_VERSION
        ).all()
        
        print(f"--- Comparison Experiment: {MODEL} vs {GEMINI_MODEL} ---")
        print(f"Target Papers: {len(gemini_results)}\n")
        
        matches = 0
        total = 0
        
        for g_res in gemini_results:
            # Check if gemma already has it (skip if yes)
            existing = session.query(PatternExperimentResult).filter(
                PatternExperimentResult.model_name == MODEL,
                PatternExperimentResult.arxiv_id == g_res.arxiv_id,
                PatternExperimentResult.prompt_version == PROMPT_VERSION
            ).first()
            
            # Fetch abstract from main papers table
            paper_data = session.execute(sa_text(
                "SELECT title, COALESCE(extracted_abstract, summary) as abstract FROM papers WHERE arxiv_id = :aid"
            ), {"aid": g_res.arxiv_id}).fetchone()
            
            if not paper_data:
                print(f"Skipping {g_res.arxiv_id} (missing in papers table)")
                continue

            title, abstract = paper_data
            abstract = (abstract or "")[:800]

            if not existing:
                print(f"Running {MODEL} on {g_res.arxiv_id}...", end="", flush=True)
                elapsed, parsed, error = run_ollama(title, abstract)
                
                if error:
                    print(f" ❌ {error}")
                    continue
                
                issues = validate_classification_output(parsed)
                existing = PatternExperimentResult(
                    arxiv_id=g_res.arxiv_id,
                    paper_title=title[:200],
                    prompt_version=PROMPT_VERSION,
                    model_name=MODEL,
                    is_agentic=parsed.get("is_agentic"),
                    primary_category=parsed.get("primary_category"),
                    reasoning=parsed.get("reasoning"),
                    patterns=parsed.get("patterns"),
                    raw_json=parsed,
                    num_patterns=len(parsed.get("patterns", [])),
                    taxonomy_violations=issues if issues else None,
                    num_violations=len(issues),
                    elapsed_seconds=elapsed
                )
                session.add(existing)
                session.commit()
                print(f" ✅ {elapsed:.1f}s")
            
            # Comparison
            total += 1
            if existing.is_agentic == g_res.is_agentic:
                matches += 1
                status = "MATCH"
            else:
                status = "MISMATCH"
            
            print(f"  [{status}] {g_res.arxiv_id}: Gemini={g_res.is_agentic} vs Gemma={existing.is_agentic}")
            if status == "MISMATCH":
                print(f"    Gemma Reason: {(existing.reasoning or '')[:100]}...")
                print(f"    Gemini Reason: {(g_res.reasoning or '')[:100]}...")

        if total > 0:
            print(f"\nSummary:")
            print(f"  Agentic Agreement: {matches}/{total} ({matches/total*100:.1f}%)")

if __name__ == "__main__":
    main()
