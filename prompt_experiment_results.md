# Pattern Extraction — Prompt Experiment Results (Full)

**Model:** gemma3:4b  
**Date:** 2026-02-20  
**Papers tested:** 8 (3 agentic, 5 non-agentic)  
**Prompt variants tested:** 6 (v1–v6)

---

## Summary Comparison

| Metric | v1_baseline | v2_strict | v3_oneshot | v4_structured | v5_hybrid | **v6_cot** |
|---|---|---|---|---|---|---|
| **Avg time/paper** | 4.4s | 3.7s | **3.4s** | 6.5s | 5.2s | 8.5s |
| **is_agentic accuracy** | 38% | **100%** | **100%** | 75% | 88% | 88% |
| **primary_cat accuracy** | — | — | 5/8 | 5/8 | 5/8 | **6/8** |
| **Taxonomy violations** | 1 | 1 | **0** | **0** | 1 | 5 |
| **Patterns/paper avg** | 3.4 | 2.2 | 2.2 | 2.4 | 2.5 | 2.2 |
| **Est. 63k backfill** | 77h | 65h | **60h** | 113h | 91h | 149h |

---

## V6 Chain-of-Thought — Full JSON Outputs

### Paper 1: Agentic XAI ✅ (is_agentic correct)

```json
{
  "reasoning": "Step 1: This paper describes a system where an LLM acts as an autonomous agent iteratively refining explanations for an agricultural recommendation system. The LLM doesn't just generate an explanation; it refines it through an agentic loop. Step 2: The core of the approach is the LLM operating autonomously to improve the explanation, which aligns with the definition of agentic AI. It's not simply about training, architecture, or evaluation. Step 3: The primary category is agent_memory (iterative refinement), followed by agent_tool_use (function calling - SHAP), and potentially world_models (environment simulation - rice yield data).",
  "is_agentic": true,
  "primary_category": "agent_memory",
  "patterns": [
    {"category": "agent_memory", "name": "iterative refinement", "confidence": 0.85, "evidence": "LLM operates autonomously to improve the explanation"},
    {"category": "agent_tool_use", "name": "function calling", "confidence": 0.75, "evidence": "SHAP-based explainability"},
    {"category": "world_models", "name": "environment simulation", "confidence": 0.65, "evidence": "rice yield data from 26 fields in Japan"}
  ]
}
```

> ⚠️ **Violations:** Invented `iterative refinement`, used spaces in `function calling`. Reasoning quality is good though — correctly identifies the agentic loop.

---

### Paper 2: Multi-Persona Fake News Detection ✅ (is_agentic correct)

```json
{
  "reasoning": "Step 1: This paper describes a framework for fake news detection that utilizes multiple personas and integrates various data sources (text, images, knowledge graphs). It focuses on building a robust and explainable system. Step 2: The abstract explicitly mentions an 'agentic multi-persona framework,' suggesting an iterative process where the system actively gathers evidence and reasons. The use of 'reverse image search, knowledge graph paths, and persuasion strategy analysis' implies an active exploration and decision-making process. Therefore, it is agentic. Step 3: The primary categories are agent_tool_use (reverse image search, api orchestration), agent_memory (evidence-grounded), and multi_agent (multi-persona).",
  "is_agentic": true,
  "primary_category": "agent_tool_use",
  "patterns": [
    {"category": "agent_tool_use", "name": "function_calling", "confidence": 0.85, "evidence": "reverse image search, knowledge graph paths, persuasion strategy analysis"}
  ]
}
```

> ✅ Clean output. Reasoning correctly identifies agentic loop, tool use, and multi-persona aspects. But only 1 pattern extracted (v3 got 3).

---

### Paper 3: Policy-Conditioned Multi-Agent ❌ (is_agentic WRONG)

```json
{
  "reasoning": "Step 1: This paper is about using Large Language Models (LLMs) to represent and optimize policies in multi-agent tasks, specifically by representing policies as human-interpretable source code. The core idea is to use LLMs as \"approximate interpreters\" to achieve a 'Program Equilibrium'. Step 2: It is not agentic because the paper describes a system where LLMs interpret and optimize policies, but there's no autonomous agent that acts in a loop, interacts with an environment, or uses tools. It's a system of interpretation and optimization, not active interaction. Step 3: The matching categories are: architecture (transformers), training (supervised_finetuning), and world_models (predictive_modeling).",
  "is_agentic": false,
  "primary_category": "architecture",
  "patterns": [
    {"category": "architecture", "name": "transformers", "confidence": 0.85, "evidence": "utilizing Large Language Models (LLMs)"},
    {"category": "training", "name": "supervised_finetuning", "confidence": 0.75, "evidence": "supervised_finetuning"},
    {"category": "world_models", "name": "predictive_modeling", "confidence": 0.65, "evidence": "the LLM is used for predictive modeling of policies"}
  ]
}
```

> ❌ **False negative.** The reasoning is thoughtful but wrong — it concluded the multi-agent system isn't agentic because "there's no autonomous agent that acts in a loop." This shows the CoT can actually talk itself out of correct answers when the model overthinks.

---

### Paper 4: Parallel Token Prediction ✅ (is_agentic correct)

```json
{
  "reasoning": "Step 1: This paper describes a novel framework (PTP) for improving the speed of language model generation by predicting multiple tokens in parallel. It focuses on the architecture and training of a language model, specifically addressing latency issues in autoregressive decoding. Step 2: It is not agentic because the paper describes a technique for improving a language model's inference speed, not an autonomous agent. Step 3: The primary category is inference, with supporting categories related to architecture and training.",
  "is_agentic": false,
  "primary_category": "inference",
  "patterns": [
    {"category": "speculative_decoding", "name": "speculative decoding", "confidence": 0.95, "evidence": "We achieve state-of-the-art speculative decoding performance"}
  ]
}
```

> ⚠️ **Structural error:** Used `speculative_decoding` as the category instead of `inference`. The reasoning is correct though.

---

### Paper 5: Rethinking SFT ✅ (is_agentic correct)

```json
{
  "reasoning": "Step 1: This paper is about a novel training method for LLMs focused on improving accuracy by prioritizing the final answer tokens during SFT. Step 2: It is not agentic because the paper describes a training procedure. There is no autonomous agent, tool use, or interactive loop. Step 3: The matching categories are: training (supervised_finetuning).",
  "is_agentic": false,
  "primary_category": "training",
  "patterns": [
    {"category": "training", "name": "supervised_finetuning", "confidence": 0.95, "evidence": "conventional SFT is applied to ensure proper output format, while in the second stage, only the Key portion is fine-tuned"}
  ]
}
```

> ✅ **Perfect output.** Clean, no violations, correct reasoning. No noise patterns (v3 had added `agent_memory/working_memory` here).

---

### Paper 6: Dyna-Style RL ✅ (is_agentic correct!)

```json
{
  "reasoning": "Step 1: This paper describes a reinforcement learning approach to control a system with nonlinear dynamics. It uses SINDy to learn a model of the system and then uses this model to generate synthetic rollouts for training. Step 2: It is not agentic because the system doesn't involve an AI agent autonomously deciding, acting, and interacting with tools/environments in a loop. It's a training method using a learned model. Step 3: The matching categories are: training, world_models (learned_dynamics).",
  "is_agentic": false,
  "primary_category": "training",
  "patterns": [
    {"category": "training", "name": "rlhf", "confidence": 0.6, "evidence": "reinforcement learning"},
    {"category": "training", "name": "synthetic_data", "confidence": 0.8, "evidence": "synthetic rollouts"},
    {"category": "architecture", "name": "transformers", "confidence": 0.7, "evidence": "TD3"},
    {"category": "world_models", "name": "learned_dynamics", "confidence": 0.8, "evidence": "identify a data-driven model of the system"}
  ]
}
```

> ✅ **is_agentic correct!** (v4 and v5 both got this wrong). The CoT reasoning explicitly says "It's a training method using a learned model" — this is the paper that tripped up every other prompt. However, some pattern issues remain: `rlhf` for general RL, `transformers` for TD3.

---

### Paper 7: ElfCore Neural Processor ✅ (is_agentic correct, primary correct!)

```json
{
  "reasoning": "Step 1: This paper describes a novel hardware accelerator – ElfCore – designed for processing event-driven neural networks. It focuses on efficient training and inference of spiking neural networks. Step 2: The paper is about hardware design and training techniques, not agentic behavior. It details a system where the processor learns and adapts, but this is a passive process. Step 3: The primary category is architecture.",
  "is_agentic": false,
  "primary_category": "architecture",
  "patterns": [
    {"category": "architecture", "name": "attention_mechanism", "confidence": 0.6, "evidence": "ElfCore is a neural processor"},
    {"category": "training", "name": "synthetic_data", "confidence": 0.7, "evidence": "online self-supervised learning without labeled inputs"},
    {"category": "training", "name": "reward_modeling", "confidence": 0.5, "evidence": "activity-dependent sparse weight update"},
    {"category": "architecture", "name": "mixture_of_experts", "confidence": 0.3, "evidence": "digital spiking neural network processor"}
  ]
}
```

> ✅ **First prompt to correctly classify primary as `architecture`!** All previous prompts put this as `training` or `agent_memory`. The reasoning is spot-on: "hardware design and training techniques, not agentic behavior." Low-confidence patterns would be filtered by post-processing.

---

### Paper 8: Reasoning Benchmark ✅ (is_agentic correct, primary correct!)

```json
{
  "reasoning": "Step 1: This paper investigates the performance of vision-language models on reasoning benchmarks and argues that the observed performance gap is due to limitations in visual perception. Step 2: It is not agentic because the paper describes an experimental setup and a method for analyzing existing models. Step 3: The matching categories are: agent_evaluation (benchmarking).",
  "is_agentic": false,
  "primary_category": "agent_evaluation",
  "patterns": [
    {"category": "benchmarking", "name": "benchmark", "confidence": 0.85, "evidence": "We introduce a two-stage experimental pipeline..."}
  ]
}
```

> ⚠️ Used `benchmarking` as category instead of `agent_evaluation`. But the reasoning and classification are correct.

---

## Analysis: What CoT Changed

### Wins 🏆
1. **Dyna-Style RL:** First prompt to correctly say `is_agentic: false` while extracting `world_models/learned_dynamics`. The reasoning: *"It's a training method using a learned model"* — direct and accurate.
2. **ElfCore:** First prompt to correctly classify primary as `architecture`. Reasoning: *"hardware design and training techniques, not agentic behavior."*
3. **Cleaner reasoning:** Every paper gets a multi-step analysis that explains *why* the classification was made. This is auditable.
4. **Less force-fitting:** The SFT paper got only 1 pattern (the correct one). v3 had added bogus `agent_memory/working_memory`.

### Losses 📉
1. **Multi-Agent paper:** CoT talked the model *out* of the correct answer. It reasoned "there's no autonomous agent that acts in a loop" — technically debatable.
2. **Taxonomy violations (5):** The model invents pattern names within the reasoning (`iterative refinement`, `function calling` with spaces) and sometimes uses patterns as categories (`speculative_decoding`, `benchmarking`).
3. **Speed:** 8.5s avg (2.5x slower than v3). 63k papers would take ~149 hours (6.2 days).

### Root cause of violations
The CoT reasoning doesn't reference the taxonomy — the model reasons freely, then when it maps to JSON fields, it uses the words from its reasoning instead of the exact taxonomy values. This is a solvable problem.

---

## Recommendation: V7 = V3 + CoT

Combine the best of both:
- **v3's concise format** with one-shot example for taxonomy compliance
- **v6's CoT reasoning field** placed first in the JSON
- **v3's taxonomy block** (compact, with exact values listed)
- Post-processing to drop confidence < 0.7 and validate patterns

This should give us:
- CoT quality (better primary classification, better is_agentic on hard cases)
- v3's taxonomy compliance (0 violations from the example-driven format)
- Moderate speed (~5-6s estimate, between v3 and v6)

---

## All Prompt Variants Tested

| Version | Strategy | Key change |
|---|---|---|
| v1 | Baseline | Minimal instructions |
| v2 | Strict rules | Added `is_agentic` definition |
| v3 | One-shot example | Added ReAct classification example |
| v4 | Per-category definitions | Full "NOT this" list per category |
| v5 | Hybrid v3+v4 | Compact structure + key distinctions |
| **v6** | **Chain-of-Thought** | **Reasoning field first in JSON** |
