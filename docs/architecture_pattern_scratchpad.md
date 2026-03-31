# Architecture Pattern Library — Scratchpad

*Brainstorming doc for the pattern extraction feature. Using Gemma 3 4B locally via Ollama.*

---

## Decisions Made ✅

| Decision | Choice | Rationale |
|---|---|---|
| Model | **Gemma 3 4B** via Ollama | Good accuracy for classification, 128k context, fast on Mac |
| Storage | **Separate `paper_patterns` table** | Better for querying/aggregation |
| Taxonomy source | **AI pattern categories + bookmark list integration** | Lists = user's mental model |

---

## Existing Infrastructure

- **Ollama already wired up**: `OllamaProvider` in `llm_service.py` → `http://localhost:11434/v1`
- **Paper text available**: `extracted_abstract`, `extracted_introduction`, `summary`, `generated_summary`
- **Current bookmark lists**: Just "Bookmarks" (3 papers) — lists are nascent
- **Worker pipeline**: new step slots in after summarization in `production_worker.py`

---

## Taxonomy Design (v1)

The idea: merge **technical pattern categories** with **user-facing list names**. The pattern extraction auto-tags papers, and those tags double as suggested lists for your library.

### Proposed Categories

```yaml
# === AGENTIC PATTERNS (your core interest) ===
agent_memory:
  - short_term_buffer
  - episodic_memory
  - rag_retrieval
  - working_memory
  - long_term_persistent
  - scratchpad

agent_planning:
  - react_loop
  - tree_of_thought
  - hierarchical_planning
  - goal_decomposition
  - chain_of_thought
  - monte_carlo_search

agent_tool_use:
  - function_calling
  - code_execution
  - api_orchestration
  - browser_use
  - multi_tool_routing

multi_agent:
  - debate
  - delegation
  - voting_consensus
  - hierarchical_control
  - swarm_intelligence
  - role_specialization

agent_evaluation:
  - benchmark_design
  - safety_testing
  - capability_measurement
  - red_teaming

# === LLM EFFICIENCY (your other core interest) ===
training_methods:
  - rlhf
  - dpo
  - sft
  - constitutional_ai
  - reward_modeling
  - synthetic_data

inference_optimization:
  - speculative_decoding
  - kv_cache_optimization
  - quantization
  - distillation
  - moe_routing
  - batch_optimization

architecture_innovation:
  - attention_mechanism
  - positional_encoding
  - mixture_of_experts
  - state_space_models
  - hybrid_architectures

# === META ===
domain:
  - nlp
  - vision
  - multimodal
  - robotics
  - code_generation
  - scientific_reasoning
```

### How This Connects to Bookmark Lists

The extraction output includes a `primary_category` field. The frontend can then offer:
- **Auto-suggest lists**: "This paper is about `agent_planning` → Add to your 'Planning Patterns' list?"
- **Smart filtering**: Browse all papers tagged `agent_tool_use/function_calling`
- **List auto-population**: "Create a list from all papers matching `multi_agent`"

This means your bookmark lists evolve from manual curation to **LLM-assisted organization**.

---

## Prompt Design (for Gemma 3 4B)

### Key Principles for Small Models
1. **Fixed taxonomy, not open-ended** — the model picks from a list, not invents categories
2. **Short input** — abstract + summary only (~1-2k tokens), skip full introduction
3. **Structured JSON output** — Ollama's `format: "json"` mode
4. **One-shot example** — small models benefit enormously from one example

### Draft Prompt

```
You are a research paper classifier for AI/ML papers. Classify the paper below against the provided taxonomy.

TAXONOMY:
- agent_memory: [short_term_buffer, episodic_memory, rag_retrieval, working_memory, long_term_persistent, scratchpad]
- agent_planning: [react_loop, tree_of_thought, hierarchical_planning, goal_decomposition, chain_of_thought, monte_carlo_search]
- agent_tool_use: [function_calling, code_execution, api_orchestration, browser_use, multi_tool_routing]
- multi_agent: [debate, delegation, voting_consensus, hierarchical_control, swarm_intelligence, role_specialization]
- agent_evaluation: [benchmark_design, safety_testing, capability_measurement, red_teaming]
- training_methods: [rlhf, dpo, sft, constitutional_ai, reward_modeling, synthetic_data]
- inference_optimization: [speculative_decoding, kv_cache_optimization, quantization, distillation, moe_routing, batch_optimization]
- architecture_innovation: [attention_mechanism, positional_encoding, mixture_of_experts, state_space_models, hybrid_architectures]

EXAMPLE:
Title: "ReAct: Synergizing Reasoning and Acting in Language Models"
Abstract: "We propose ReAct, a method that prompts LLMs to generate both reasoning traces and task-specific actions in an interleaved manner..."

Output:
{"patterns": [{"category": "agent_planning", "name": "react_loop", "confidence": 0.95, "evidence": "proposes interleaved reasoning and acting"}, {"category": "agent_tool_use", "name": "api_orchestration", "confidence": 0.7, "evidence": "actions include API calls to external knowledge bases"}], "is_agentic": true, "primary_category": "agent_planning"}

NOW CLASSIFY THIS PAPER:
Title: {title}
Abstract: {abstract}

Output:
```

### Why This Should Work Well on 4B

- The task is **classification, not generation** — picking from a fixed list
- One-shot example **anchors the format** — critical for small models
- Short input (~300 tokens of prompt + ~500 tokens of paper) = well within 4B's sweet spot
- JSON output mode prevents rambling

---

## Backfill Estimate (Gemma 3 4B)

| Metric | Estimate |
|---|---|
| Input per paper | ~800 tokens (prompt + abstract + summary) |
| Output per paper | ~150 tokens (JSON) |
| Gemma 3 4B speed on Mac (M-series) | ~40-60 tok/s |
| Time per paper | ~3-4 seconds |
| 63k papers total | ~55-70 hours (2.5-3 days) |
| Recent papers only (last 6 months, ~10k) | ~10-12 hours |

**Recommendation**: Start with recent 6 months, run overnight. Backfill older papers passively over the next week.

---

## Open Questions Remaining

1. **Confidence threshold**: Store all patterns, or only ≥0.7? (I lean toward storing everything and filtering at query time)
2. **Taxonomy evolution**: When the model consistently suggests something outside the taxonomy, how do we add new patterns? Manual review? Auto-suggest?
3. **Frontend priority**: Pattern browser page, or just tags on existing paper cards first?

---

## Next Steps

- [ ] Pull Gemma 3 4B via Ollama: `ollama pull gemma3:4b`
- [ ] Test the prompt against 5-10 papers manually (copy-paste into Ollama)
- [ ] Tune taxonomy based on real output quality
- [ ] Build DB table + worker integration
- [ ] Build API endpoint + frontend
- [ ] Run backfill on recent papers
