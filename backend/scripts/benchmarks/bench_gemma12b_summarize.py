#!/usr/bin/env python3
"""
Benchmark Gemma 3 12B token generation speed for summarization tasks.
Pulls paper text from the arxiv_assistant database on Khadas.

Usage:
    python scripts/benchmarks/bench_gemma12b_summarize.py
"""

import json
import os
import sys
import time

import psycopg2
import requests

OLLAMA_BASE = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
MODEL = os.environ.get("MODEL", "gemma3:12b")
NUM_CTX = int(os.environ.get("NUM_CTX", "32768"))

DB_HOST = os.environ.get("DB_HOST", "192.168.1.49")
DB_PORT = int(os.environ.get("DB_PORT", "5434"))
DB_NAME = os.environ.get("DB_NAME", "arxiv_db")
DB_USER = os.environ.get("DB_USER", "user")
DB_PASS = os.environ.get("DB_PASS", "password")

SUMMARIZATION_PROMPT = """Please provide a structured and detailed summary of the following research paper.
Format the response with the following clearly labeled sections:

1. **Core Problem**: What specific problem is this paper trying to solve?
2. **Key Innovation**: What is the main novelty or contribution (the "aha!" moment)?
3. **Methodology**: Briefly explain the technical approach.
4. **Key Results**: What were the quantitative or qualitative findings?

Text:
{text}"""


def get_papers_from_db(n=2):
    """Fetch papers with full text sections from Khadas DB."""
    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
    cur = conn.cursor()
    # Pick papers with substantial extracted text, varied sizes
    cur.execute("""
        SELECT arxiv_id, title, full_text_sections, extracted_abstract
        FROM papers
        WHERE full_text_sections IS NOT NULL
          AND jsonb_array_length(full_text_sections) > 5
        ORDER BY published_date DESC
        LIMIT %s
    """, (n,))
    papers = []
    for row in cur.fetchall():
        arxiv_id, title, sections_json, abstract = row
        # Reconstruct full text from sections
        if isinstance(sections_json, str):
            sections = json.loads(sections_json)
        else:
            sections = sections_json
        full_text = "\n\n".join(
            f"{s.get('title', '')}\n{s.get('content', '')}" for s in sections
        )
        papers.append({
            "arxiv_id": arxiv_id,
            "title": title,
            "full_text": full_text,
            "abstract": abstract or "",
            "num_sections": len(sections),
        })
    conn.close()
    return papers


def run_summarization(text: str, run_label: str) -> dict:
    """Call Ollama native API and return timing metrics."""
    prompt = SUMMARIZATION_PROMPT.format(text=text[:30000])

    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"num_ctx": NUM_CTX},
    }

    print(f"\n{'='*70}")
    print(f"  {run_label}")
    print(f"  Model: {MODEL} | num_ctx: {NUM_CTX}")
    print(f"  Input text: {len(text):,} chars (truncated to {min(len(text), 30000):,})")
    print(f"{'='*70}")

    wall_start = time.time()
    resp = requests.post(f"{OLLAMA_BASE}/api/chat", json=payload, timeout=900)
    wall_elapsed = time.time() - wall_start
    resp.raise_for_status()
    data = resp.json()

    content = data.get("message", {}).get("content", "")

    # Ollama native API timing fields (nanoseconds)
    prompt_eval_count = data.get("prompt_eval_count", 0)
    eval_count = data.get("eval_count", 0)
    prompt_eval_duration_ns = data.get("prompt_eval_duration", 0)
    eval_duration_ns = data.get("eval_duration", 0)
    total_duration_ns = data.get("total_duration", 0)
    load_duration_ns = data.get("load_duration", 0)

    prompt_eval_s = prompt_eval_duration_ns / 1e9
    eval_s = eval_duration_ns / 1e9
    total_s = total_duration_ns / 1e9
    load_s = load_duration_ns / 1e9

    prompt_tps = prompt_eval_count / prompt_eval_s if prompt_eval_s > 0 else 0
    gen_tps = eval_count / eval_s if eval_s > 0 else 0

    result = {
        "prompt_tokens": prompt_eval_count,
        "completion_tokens": eval_count,
        "prompt_eval_sec": round(prompt_eval_s, 2),
        "generation_sec": round(eval_s, 2),
        "total_sec": round(total_s, 2),
        "load_sec": round(load_s, 2),
        "wall_sec": round(wall_elapsed, 2),
        "prompt_tokens_per_sec": round(prompt_tps, 1),
        "generation_tokens_per_sec": round(gen_tps, 1),
        "output_chars": len(content),
    }

    print(f"\n  Results:")
    print(f"  ├─ Prompt eval:    {prompt_eval_count:,} tokens in {prompt_eval_s:.1f}s → {prompt_tps:.1f} tok/s")
    print(f"  ├─ Generation:     {eval_count:,} tokens in {eval_s:.1f}s → {gen_tps:.1f} tok/s")
    print(f"  ├─ Model load:     {load_s:.2f}s")
    print(f"  ├─ Total (Ollama): {total_s:.1f}s")
    print(f"  ├─ Wall clock:     {wall_elapsed:.1f}s")
    print(f"  └─ Output:         {len(content):,} chars")

    print(f"\n  --- Summary Preview (first 500 chars) ---")
    print(f"  {content[:500]}...")

    return result


def main():
    # Verify Ollama is reachable
    try:
        r = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=5)
        models = [m["name"] for m in r.json().get("models", [])]
        print(f"Ollama models available: {', '.join(models)}")
        if MODEL not in models:
            print(f"WARNING: {MODEL} not found in Ollama. Available: {models}")
            sys.exit(1)
    except Exception as e:
        print(f"Cannot reach Ollama at {OLLAMA_BASE}: {e}")
        sys.exit(1)

    # Fetch papers from DB
    print(f"\nFetching papers from {DB_HOST}:{DB_PORT}/{DB_NAME}...")
    papers = get_papers_from_db(n=2)
    print(f"Got {len(papers)} papers:")
    for p in papers:
        print(f"  - {p['arxiv_id']}: {p['title'][:70]} ({len(p['full_text']):,} chars, {p['num_sections']} sections)")

    results = []
    for p in papers:
        print(f"\n{'#'*70}")
        print(f"# Paper: {p['title']}")
        print(f"# arXiv: {p['arxiv_id']} | {p['num_sections']} sections | {len(p['full_text']):,} chars")
        print(f"{'#'*70}")

        metrics = run_summarization(p["full_text"], f"Summarize: {p['title'][:60]}")
        metrics["arxiv_id"] = p["arxiv_id"]
        metrics["title"] = p["title"]
        metrics["full_text_chars"] = len(p["full_text"])
        metrics["num_sections"] = p["num_sections"]
        results.append(metrics)

    # Summary table
    print(f"\n\n{'='*70}")
    print(f"  BENCHMARK SUMMARY — {MODEL}")
    print(f"{'='*70}")
    print(f"  {'Paper':<45} {'Prompt tok/s':>12} {'Gen tok/s':>12} {'Gen tokens':>10} {'Wall(s)':>8}")
    print(f"  {'-'*45} {'-'*12} {'-'*12} {'-'*10} {'-'*8}")
    for r in results:
        short_title = r["title"][:45]
        print(f"  {short_title:<45} {r['prompt_tokens_per_sec']:>12.1f} {r['generation_tokens_per_sec']:>12.1f} {r['completion_tokens']:>10,} {r['wall_sec']:>8.1f}")

    avg_gen_tps = sum(r["generation_tokens_per_sec"] for r in results) / len(results)
    avg_prompt_tps = sum(r["prompt_tokens_per_sec"] for r in results) / len(results)
    print(f"\n  Average prompt throughput:     {avg_prompt_tps:.1f} tok/s")
    print(f"  Average generation throughput: {avg_gen_tps:.1f} tok/s")

    # Save results
    out_path = os.path.join(os.path.dirname(__file__), "gemma12b_summarize_results.json")
    with open(out_path, "w") as f:
        json.dump({"model": MODEL, "num_ctx": NUM_CTX, "results": results}, f, indent=2)
    print(f"\n  Results saved to {out_path}")


if __name__ == "__main__":
    main()
