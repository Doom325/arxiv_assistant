#!/usr/bin/env python3
"""
Pattern Extraction Prompt Experiment
Runs multiple prompt variants against the same papers on Gemma 3 4B,
writes structured results to prompt_experiment_results.md
"""

import requests, json, time, sys
from datetime import datetime
from config import settings
from sqlalchemy import create_engine, text as sa_text
from sqlalchemy.orm import sessionmaker

MODEL = "gemma3:4b"
OLLAMA_URL = "http://localhost:11434/api/chat"

# ─────────────────────────────────────────────────────
# TAXONOMY (shared across all prompts)
# ─────────────────────────────────────────────────────
TAXONOMY_BLOCK = """- agent_memory: [retrieval_augmented, persistent_memory, working_memory, episodic]
- agent_planning: [reasoning_acting, tree_search, goal_decomposition, chain_of_thought]
- agent_tool_use: [function_calling, code_execution, api_orchestration, browser_use]
- multi_agent: [collaboration, debate, hierarchical_control, role_specialization]
- agent_evaluation: [benchmarking, safety, capability_measurement]
- training: [rlhf, dpo, supervised_finetuning, reward_modeling, synthetic_data]
- inference: [speculative_decoding, quantization, distillation, efficient_attention]
- architecture: [attention_mechanism, mixture_of_experts, hybrid_architecture, transformers]
- world_models: [learned_dynamics, model_based_rl, environment_simulation, predictive_modeling]
- state_space_models: [mamba, s4, linear_recurrence, selective_state_spaces]"""

VALID_CATEGORIES = {
    "agent_memory", "agent_planning", "agent_tool_use", "multi_agent",
    "agent_evaluation", "training", "inference", "architecture",
    "world_models", "state_space_models"
}
VALID_PATTERNS = {
    "agent_memory": {"retrieval_augmented", "persistent_memory", "working_memory", "episodic"},
    "agent_planning": {"reasoning_acting", "tree_search", "goal_decomposition", "chain_of_thought"},
    "agent_tool_use": {"function_calling", "code_execution", "api_orchestration", "browser_use"},
    "multi_agent": {"collaboration", "debate", "hierarchical_control", "role_specialization"},
    "agent_evaluation": {"benchmarking", "safety", "capability_measurement"},
    "training": {"rlhf", "dpo", "supervised_finetuning", "reward_modeling", "synthetic_data"},
    "inference": {"speculative_decoding", "quantization", "distillation", "efficient_attention"},
    "architecture": {"attention_mechanism", "mixture_of_experts", "hybrid_architecture", "transformers"},
    "world_models": {"learned_dynamics", "model_based_rl", "environment_simulation", "predictive_modeling"},
    "state_space_models": {"mamba", "s4", "linear_recurrence", "selective_state_spaces"},
}

# ─────────────────────────────────────────────────────
# PROMPT VARIANTS
# ─────────────────────────────────────────────────────

PROMPTS = {}

# V1: BASELINE (minimal, what we tested before)
PROMPTS["v1_baseline"] = """You are a research paper classifier. Classify this paper against the taxonomy. Only include patterns clearly present. Respond in valid JSON only.

TAXONOMY:
{taxonomy}

Title: {title}
Abstract: {abstract}

Respond with JSON: {{"patterns": [{{"category": "...", "name": "...", "confidence": 0.9, "evidence": "..."}}], "is_agentic": true/false, "primary_category": "..."}}"""

# V2: STRICT DEFINITION + GUARDRAILS
PROMPTS["v2_strict"] = """You are a research paper classifier for AI/ML papers.

TASK: Classify the paper against the taxonomy below. Follow these rules:
1. ONLY use category and name values from the taxonomy. Do not invent new ones.
2. Only include patterns with confidence >= 0.6.
3. "is_agentic" means the paper describes a system where an LLM or AI model AUTONOMOUSLY makes decisions, takes actions, and interacts with tools or environments. Papers about training methods, model architecture, or benchmarks alone are NOT agentic.

TAXONOMY:
{taxonomy}

PAPER:
Title: {title}
Abstract: {abstract}

Respond with valid JSON only:
{{"patterns": [{{"category": "...", "name": "...", "confidence": 0.9, "evidence": "one sentence"}}], "is_agentic": true/false, "primary_category": "..."}}"""

# V3: ONE-SHOT EXAMPLE + STRICT
PROMPTS["v3_oneshot"] = """You are a research paper classifier for AI/ML papers.

RULES:
1. ONLY use category and name values listed in the taxonomy below. Do not invent new ones.
2. Only include patterns with confidence >= 0.6.
3. "is_agentic" = true ONLY if the paper describes a system where an LLM autonomously makes decisions, takes actions, and interacts with tools or environments. Training methods, model architecture improvements, and benchmarks are NOT agentic.
4. Keep evidence to one short sentence.

TAXONOMY:
{taxonomy}

EXAMPLE INPUT:
Title: "ReAct: Synergizing Reasoning and Acting in Language Models"
Abstract: "We propose ReAct, a method that prompts LLMs to generate both reasoning traces and task-specific actions in an interleaved manner, allowing for greater synergy between reasoning and acting."

EXAMPLE OUTPUT:
{{"patterns": [{{"category": "agent_planning", "name": "reasoning_acting", "confidence": 0.95, "evidence": "Proposes interleaved reasoning and acting loop."}}, {{"category": "agent_tool_use", "name": "api_orchestration", "confidence": 0.7, "evidence": "Actions include API calls to external knowledge bases."}}], "is_agentic": true, "primary_category": "agent_planning"}}

NOW CLASSIFY:
Title: {title}
Abstract: {abstract}

Output JSON:"""

# ─────────────────────────────────────────────────────
# TEST PAPERS (with expected labels for evaluation)
# ─────────────────────────────────────────────────────
TEST_PAPER_IDS = [
    ('2512.21066v1', True,  'agent'),     # Agentic XAI
    ('2512.21039v1', True,  'agent'),     # Multi-Persona Fake News Detection
    ('2512.21024v1', True,  'agent'),     # Policy-Conditioned Multi-Agent
    ('2512.21323v1', False, 'inference'), # Parallel Token Prediction
    ('2512.21017v1', False, 'training'),  # Rethinking SFT
    ('2512.21081v1', False, 'world_models'),  # Dyna-Style RL
    ('2512.21153v1', False, 'architecture'),  # ElfCore Neural Processor
    ('2512.21329v1', False, 'agent_evaluation'), # Reasoning Benchmark
]

def run_prompt(prompt_name, prompt_template, title, abstract, taxonomy):
    prompt = prompt_template.format(title=title, abstract=abstract, taxonomy=taxonomy)
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "format": "json",
        "options": {"num_ctx": 4096, "temperature": 0.1}
    }
    start = time.time()
    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=180)
        elapsed = time.time() - start
        content = resp.json().get("message", {}).get("content", "")
        parsed = json.loads(content)
        return elapsed, parsed, None
    except Exception as e:
        elapsed = time.time() - start
        return elapsed, None, str(e)

def validate_output(parsed):
    """Check if output adheres to taxonomy."""
    issues = []
    if parsed is None:
        return ["PARSE_FAILED"]
    for p in parsed.get("patterns", []):
        cat = p.get("category", "")
        name = p.get("name", "")
        if cat not in VALID_CATEGORIES:
            issues.append(f"invalid_category:{cat}")
        elif name not in VALID_PATTERNS.get(cat, set()):
            issues.append(f"invented_pattern:{cat}/{name}")
    return issues

def main():
    engine = create_engine(settings.DATABASE_URL)
    db = sessionmaker(bind=engine)()

    # Fetch test papers
    ids = [t[0] for t in TEST_PAPER_IDS]
    rows = db.execute(sa_text(
        "SELECT arxiv_id, title, COALESCE(extracted_abstract, summary) as abstract "
        "FROM papers WHERE arxiv_id IN :ids"
    ), {"ids": tuple(ids)}).fetchall()
    paper_map = {r[0]: (r[1], (r[2] or "")[:800]) for r in rows}

    expected = {t[0]: {"is_agentic": t[1], "domain": t[2]} for t in TEST_PAPER_IDS}

    results = []  # (prompt_name, paper_id, elapsed, parsed, error, issues, expected_agentic, got_agentic)

    for prompt_name, prompt_template in PROMPTS.items():
        print(f"\n{'='*60}")
        print(f"RUNNING: {prompt_name}")
        print(f"{'='*60}", flush=True)

        for arxiv_id, exp_agentic, exp_domain in TEST_PAPER_IDS:
            if arxiv_id not in paper_map:
                print(f"  SKIP {arxiv_id} (not in DB)")
                continue
            title, abstract = paper_map[arxiv_id]
            elapsed, parsed, error = run_prompt(prompt_name, prompt_template, title, abstract, TAXONOMY_BLOCK)
            issues = validate_output(parsed)
            got_agentic = parsed.get("is_agentic") if parsed else None

            print(f"  {arxiv_id} | {elapsed:.1f}s | agentic={got_agentic} (expected={exp_agentic}) | issues={issues or 'none'}", flush=True)

            results.append({
                "prompt": prompt_name,
                "arxiv_id": arxiv_id,
                "title": title[:70],
                "elapsed": elapsed,
                "expected_agentic": exp_agentic,
                "got_agentic": got_agentic,
                "expected_domain": exp_domain,
                "got_primary": parsed.get("primary_category") if parsed else None,
                "patterns": parsed.get("patterns", []) if parsed else [],
                "issues": issues,
                "error": error,
            })

    db.close()

    # ── Write results to markdown ──
    with open("prompt_experiment_results.md", "w") as f:
        f.write(f"# Prompt Experiment Results\n\n")
        f.write(f"**Model:** {MODEL}  \n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}  \n")
        f.write(f"**Papers tested:** {len(TEST_PAPER_IDS)}  \n")
        f.write(f"**Prompt variants:** {len(PROMPTS)}  \n\n")

        f.write("---\n\n")

        # Summary table
        f.write("## Summary Comparison\n\n")
        f.write("| Metric | " + " | ".join(PROMPTS.keys()) + " |\n")
        f.write("|---|" + "|".join(["---"] * len(PROMPTS)) + "|\n")

        for metric_name, metric_fn in [
            ("Avg time/paper", lambda rs: f"{sum(r['elapsed'] for r in rs)/len(rs):.1f}s"),
            ("is_agentic accuracy", lambda rs: f"{sum(1 for r in rs if r['got_agentic'] == r['expected_agentic'])/len(rs)*100:.0f}%"),
            ("Taxonomy violations", lambda rs: f"{sum(len(r['issues']) for r in rs)}"),
            ("Patterns/paper avg", lambda rs: f"{sum(len(r['patterns']) for r in rs)/len(rs):.1f}"),
        ]:
            vals = []
            for pname in PROMPTS:
                prompt_results = [r for r in results if r["prompt"] == pname]
                vals.append(metric_fn(prompt_results))
            f.write(f"| {metric_name} | " + " | ".join(vals) + " |\n")

        f.write("\n---\n\n")

        # Detailed results per prompt
        for prompt_name in PROMPTS:
            prompt_results = [r for r in results if r["prompt"] == prompt_name]
            f.write(f"## Prompt: `{prompt_name}`\n\n")

            # The actual prompt (collapsed)
            f.write("<details>\n<summary>View prompt template</summary>\n\n")
            f.write(f"```\n{PROMPTS[prompt_name]}\n```\n</details>\n\n")

            for r in prompt_results:
                agentic_match = "✅" if r["got_agentic"] == r["expected_agentic"] else "❌"
                f.write(f"### {r['arxiv_id']}: {r['title']}\n\n")
                f.write(f"- **Time:** {r['elapsed']:.1f}s\n")
                f.write(f"- **is_agentic:** {r['got_agentic']} (expected: {r['expected_agentic']}) {agentic_match}\n")
                f.write(f"- **primary_category:** {r['got_primary']} (expected domain: {r['expected_domain']})\n")
                if r["issues"]:
                    f.write(f"- **⚠️ Taxonomy violations:** {', '.join(r['issues'])}\n")
                f.write(f"- **Patterns:**\n")
                for p in r["patterns"]:
                    f.write(f"  - `{p.get('category','?')}/{p.get('name','?')}` (conf={p.get('confidence','?')}) — {str(p.get('evidence',''))[:80]}\n")
                f.write("\n")

            f.write("---\n\n")

        # Raw JSON dump for programmatic access
        f.write("## Raw Data (JSON)\n\n")
        f.write("<details>\n<summary>Click to expand raw JSON</summary>\n\n")
        f.write("```json\n")
        f.write(json.dumps(results, indent=2, default=str))
        f.write("\n```\n</details>\n")

    print(f"\n\n{'='*60}")
    print(f"Results written to prompt_experiment_results.md")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
