#!/usr/bin/env python3
"""
Prompt V4 Experiment: Structured category instructions with per-category examples.
Runs against the same 8 test papers for comparison with v1-v3.
"""

import requests, json, time
from datetime import datetime
from config import settings
from sqlalchemy import create_engine, text as sa_text
from sqlalchemy.orm import sessionmaker

MODEL = "gemma3:4b"
OLLAMA_URL = "http://localhost:11434/api/chat"

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
# V4: STRUCTURED CATEGORY INSTRUCTIONS
# ─────────────────────────────────────────────────────
V4_PROMPT = """You are a precise research paper classifier for AI/ML papers.

TASK: Classify the paper into the categories below. Follow these rules strictly:
1. ONLY use the exact category and pattern names listed below. Never invent new ones.
2. Only include patterns you are confident about (>= 0.7).
3. If NO category fits well, return an empty patterns list.
4. "is_agentic" = true ONLY if the paper builds a system where an AI agent autonomously decides and acts in a loop. Papers that merely discuss training, architecture, or evaluation are NOT agentic.
5. Evidence must be one specific sentence from the abstract, not a vague restatement.

═══════════════════════════════════════
CATEGORY DEFINITIONS (with examples)
═══════════════════════════════════════

### agent_memory
The paper proposes or uses a memory system for an AI agent to store and retrieve information.
Patterns: retrieval_augmented, persistent_memory, working_memory, episodic
Example: "RAG-Agent uses a vector store to retrieve relevant documents before answering" → retrieval_augmented
NOT this: A paper about attention mechanisms or model weights is NOT agent_memory.

### agent_planning
The paper proposes a method for an AI agent to plan, reason, or decompose goals.
Patterns: reasoning_acting, tree_search, goal_decomposition, chain_of_thought
Example: "Our agent decomposes complex tasks into subtasks and executes them sequentially" → goal_decomposition
NOT this: A paper about CoT prompting for benchmarking is NOT agent_planning unless the agent acts on its reasoning.

### agent_tool_use
The paper describes an AI agent that calls external tools, APIs, or executes code.
Patterns: function_calling, code_execution, api_orchestration, browser_use
Example: "The agent generates Python code and executes it to solve math problems" → code_execution
NOT this: A model that generates text or makes predictions is NOT tool_use. The agent must invoke an external system.

### multi_agent
The paper involves multiple AI agents interacting — collaborating, debating, or organized hierarchically.
Patterns: collaboration, debate, hierarchical_control, role_specialization
Example: "Three LLM agents with different roles discuss and vote on the final answer" → debate, role_specialization
NOT this: Multi-task learning or ensemble methods are NOT multi_agent.

### agent_evaluation
The paper evaluates or benchmarks AI agent capabilities, safety, or performance.
Patterns: benchmarking, safety, capability_measurement
Example: "We introduce AgentBench, a benchmark suite testing LLM agents across 8 environments" → benchmarking
NOT this: Standard model accuracy benchmarks (MMLU, etc.) are NOT agent_evaluation unless they specifically test agent behavior.

### training
The paper proposes or improves a method for training or fine-tuning models.
Patterns: rlhf, dpo, supervised_finetuning, reward_modeling, synthetic_data
- rlhf: Reinforcement Learning from Human Feedback specifically. NOT general RL.
- dpo: Direct Preference Optimization.
- supervised_finetuning: Fine-tuning on labeled data.
- reward_modeling: Training a reward model for preference learning.
- synthetic_data: Generating artificial training data.
Example: "We fine-tune Llama-2 on 50k instruction-response pairs" → supervised_finetuning
NOT this: A paper using RL to control a robot is NOT training/rlhf. RLHF is specifically about human preference alignment.

### inference
The paper optimizes how models generate outputs at inference time.
Patterns: speculative_decoding, quantization, distillation, efficient_attention
Example: "We compress BERT to 4-bit weights with minimal accuracy loss" → quantization
NOT this: A paper that merely uses a model for inference is NOT this category. The paper must improve the inference process itself.

### architecture
The paper proposes or modifies a neural network architecture.
Patterns: attention_mechanism, mixture_of_experts, hybrid_architecture, transformers
Example: "We replace standard attention with linear attention for O(n) complexity" → attention_mechanism
NOT this: A paper that uses transformers as a tool is NOT architecture. The paper must modify or propose architecture changes.

### world_models
The paper builds a learned model of environment dynamics for planning or simulation.
Patterns: learned_dynamics, model_based_rl, environment_simulation, predictive_modeling
- model_based_rl: RL that learns a model of the environment to plan ahead (e.g., Dreamer, MuZero, Dyna).
- learned_dynamics: Learning transition functions or physics from data.
Example: "Our agent learns a dynamics model of the environment and uses it to plan via imagination" → model_based_rl, learned_dynamics
NOT this: A standard RL algorithm (Q-learning, PPO, TD3) without a learned world model is NOT this category.

### state_space_models
The paper proposes or uses structured state space models as an alternative to transformers.
Patterns: mamba, s4, linear_recurrence, selective_state_spaces
Example: "Mamba achieves transformer-level performance with linear-time inference" → mamba
NOT this: The term "state space" in control theory or RL is NOT this category. This is specifically about SSM architectures (S4, Mamba, etc.).

═══════════════════════════════════════
PAPER TO CLASSIFY
═══════════════════════════════════════
Title: {title}
Abstract: {abstract}

Respond with valid JSON only:
{{"patterns": [{{"category": "...", "name": "...", "confidence": 0.9, "evidence": "exact quote from abstract"}}], "is_agentic": true/false, "primary_category": "..."}}"""


TEST_PAPER_IDS = [
    ('2512.21066v1', True,  'agent'),         # Agentic XAI
    ('2512.21039v1', True,  'agent'),         # Multi-Persona Fake News Detection
    ('2512.21024v1', True,  'agent'),         # Policy-Conditioned Multi-Agent
    ('2512.21323v1', False, 'inference'),     # Parallel Token Prediction
    ('2512.21017v1', False, 'training'),      # Rethinking SFT
    ('2512.21081v1', False, 'world_models'),  # Dyna-Style RL
    ('2512.21153v1', False, 'architecture'),  # ElfCore Neural Processor
    ('2512.21329v1', False, 'agent_evaluation'), # Reasoning Benchmark
]


def run_prompt(title, abstract):
    prompt = V4_PROMPT.format(title=title, abstract=abstract)
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "format": "json",
        "options": {"num_ctx": 8192, "temperature": 0.1}
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

    ids = [t[0] for t in TEST_PAPER_IDS]
    rows = db.execute(sa_text(
        "SELECT arxiv_id, title, COALESCE(extracted_abstract, summary) as abstract "
        "FROM papers WHERE arxiv_id IN :ids"
    ), {"ids": tuple(ids)}).fetchall()
    paper_map = {r[0]: (r[1], (r[2] or "")[:800]) for r in rows}

    print(f"{'='*70}")
    print(f"  PROMPT V4 EXPERIMENT — {MODEL}")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*70}\n")

    results = []
    total_time = 0

    for arxiv_id, exp_agentic, exp_domain in TEST_PAPER_IDS:
        if arxiv_id not in paper_map:
            print(f"  SKIP {arxiv_id}")
            continue
        title, abstract = paper_map[arxiv_id]
        elapsed, parsed, error = run_prompt(title, abstract)
        issues = validate_output(parsed)
        got_agentic = parsed.get("is_agentic") if parsed else None
        got_primary = parsed.get("primary_category") if parsed else None
        patterns = parsed.get("patterns", []) if parsed else []
        total_time += elapsed

        # Print real-time
        agentic_icon = "✅" if got_agentic == exp_agentic else "❌"
        primary_icon = "✅" if got_primary == exp_domain or (exp_domain == "agent" and got_primary and got_primary.startswith("agent")) or (exp_domain == "agent" and got_primary == "multi_agent") else "⚠️"
        print(f"{'─'*70}")
        print(f"📄 {title[:65]}")
        print(f"   Time: {elapsed:.1f}s | is_agentic: {got_agentic} (exp: {exp_agentic}) {agentic_icon}")
        print(f"   primary: {got_primary} (exp: {exp_domain}) {primary_icon}")
        if issues:
            print(f"   ⚠️  VIOLATIONS: {issues}")
        for p in patterns:
            print(f"   → {p.get('category','?')}/{p.get('name','?')} (conf={p.get('confidence','?')}) — {str(p.get('evidence',''))[:65]}")
        if not patterns:
            print(f"   → (no patterns matched)")

        results.append({
            "prompt": "v4_structured",
            "arxiv_id": arxiv_id,
            "title": title[:70],
            "elapsed": elapsed,
            "expected_agentic": exp_agentic,
            "got_agentic": got_agentic,
            "expected_domain": exp_domain,
            "got_primary": got_primary,
            "patterns": patterns,
            "issues": issues,
            "error": error,
        })

    n = len(results)
    avg = total_time / n if n else 0
    agentic_acc = sum(1 for r in results if r["got_agentic"] == r["expected_agentic"]) / n * 100
    violations = sum(len(r["issues"]) for r in results)
    patterns_avg = sum(len(r["patterns"]) for r in results) / n

    print(f"\n{'='*70}")
    print(f"  SUMMARY")
    print(f"{'='*70}")
    print(f"  Avg time/paper:       {avg:.1f}s")
    print(f"  is_agentic accuracy:  {agentic_acc:.0f}%")
    print(f"  Taxonomy violations:  {violations}")
    print(f"  Patterns/paper avg:   {patterns_avg:.1f}")
    print(f"  Est. 63k papers:      {avg * 63000 / 3600:.0f} hours")
    print(f"\n  Comparison (from v1-v3 experiment):")
    print(f"  {'Prompt':<20} {'Time':>6} {'Accuracy':>10} {'Violations':>12} {'Patterns':>10}")
    print(f"  {'─'*58}")
    print(f"  {'v1_baseline':<20} {'4.4s':>6} {'38%':>10} {'1':>12} {'3.4':>10}")
    print(f"  {'v2_strict':<20} {'3.7s':>6} {'100%':>10} {'1':>12} {'2.2':>10}")
    print(f"  {'v3_oneshot':<20} {'3.4s':>6} {'100%':>10} {'0':>12} {'2.2':>10}")
    print(f"  {'v4_structured':<20} {f'{avg:.1f}s':>6} {f'{agentic_acc:.0f}%':>10} {str(violations):>12} {f'{patterns_avg:.1f}':>10}")

    # Write detailed results
    output_file = "prompt_v4_results.md"
    with open(output_file, "w") as f:
        f.write(f"# Prompt V4 Experiment Results\n\n")
        f.write(f"**Model:** {MODEL}  \n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}  \n")
        f.write(f"**Papers tested:** {n}  \n\n")

        f.write("## Summary vs Previous Prompts\n\n")
        f.write("| Metric | v1_baseline | v2_strict | v3_oneshot | **v4_structured** |\n")
        f.write("|---|---|---|---|---|\n")
        f.write(f"| Avg time/paper | 4.4s | 3.7s | 3.4s | **{avg:.1f}s** |\n")
        f.write(f"| is_agentic accuracy | 38% | 100% | 100% | **{agentic_acc:.0f}%** |\n")
        f.write(f"| Taxonomy violations | 1 | 1 | 0 | **{violations}** |\n")
        f.write(f"| Patterns/paper avg | 3.4 | 2.2 | 2.2 | **{patterns_avg:.1f}** |\n")
        f.write(f"| Est. 63k backfill | 77h | 65h | 60h | **{avg * 63000 / 3600:.0f}h** |\n\n")

        f.write("---\n\n")

        f.write("## V4 Prompt Template\n\n")
        f.write("<details>\n<summary>View full prompt (click to expand)</summary>\n\n")
        f.write(f"```\n{V4_PROMPT}\n```\n</details>\n\n")

        f.write("---\n\n")

        f.write("## Detailed Results — Paper by Paper\n\n")
        for r in results:
            agentic_match = "✅" if r["got_agentic"] == r["expected_agentic"] else "❌"
            f.write(f"### {r['arxiv_id']}: {r['title']}\n\n")
            f.write(f"| Field | Value |\n")
            f.write(f"|---|---|\n")
            f.write(f"| Time | {r['elapsed']:.1f}s |\n")
            f.write(f"| is_agentic | {r['got_agentic']} (expected: {r['expected_agentic']}) {agentic_match} |\n")
            f.write(f"| primary_category | `{r['got_primary']}` (expected: `{r['expected_domain']}`) |\n")
            if r["issues"]:
                f.write(f"| ⚠️ violations | {', '.join(r['issues'])} |\n")
            f.write(f"\n**Patterns:**\n")
            if r["patterns"]:
                f.write("| Category | Pattern | Confidence | Evidence |\n")
                f.write("|---|---|---|---|\n")
                for p in r["patterns"]:
                    f.write(f"| `{p.get('category','')}` | `{p.get('name','')}` | {p.get('confidence','')} | {str(p.get('evidence',''))[:80]} |\n")
            else:
                f.write("*(no patterns matched — correctly returned empty list)*\n")
            f.write("\n---\n\n")

        # Qualitative analysis section
        f.write("## Qualitative Analysis\n\n")
        f.write("### What V4 improved over V3:\n\n")

        # Auto-generate some analysis
        v4_correct = sum(1 for r in results if r["got_agentic"] == r["expected_agentic"])
        f.write(f"- **is_agentic accuracy:** {v4_correct}/{n}\n")
        f.write(f"- **Taxonomy violations:** {violations}\n")

        force_fit_papers = [r for r in results if r["expected_domain"] == "architecture" and r["got_primary"] != "architecture"]
        if force_fit_papers:
            f.write(f"- **Force-fitting issue:** ElfCore still classified as `{force_fit_papers[0]['got_primary']}` instead of `architecture`\n")

        dyna_results = [r for r in results if r["arxiv_id"] == "2512.21081v1"]
        if dyna_results:
            dr = dyna_results[0]
            pattern_names = [f"{p['category']}/{p['name']}" for p in dr["patterns"]]
            has_world_model = any("world_models" in pn for pn in pattern_names)
            has_rlhf = any("rlhf" in pn for pn in pattern_names)
            f.write(f"- **Dyna-Style RL:** {'✅ Correctly identified world_models' if has_world_model else '❌ Missed world_models'}. {'❌ Incorrectly tagged rlhf' if has_rlhf else '✅ Did not confuse RL with RLHF'}.\n")

        f.write("\n")

        # Raw JSON
        f.write("## Raw JSON\n\n")
        f.write("<details>\n<summary>Click to expand</summary>\n\n")
        f.write("```json\n")
        f.write(json.dumps(results, indent=2, default=str))
        f.write("\n```\n</details>\n")

    print(f"\n📝 Detailed results written to {output_file}")

    db.close()


if __name__ == "__main__":
    main()
