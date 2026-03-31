# Gemma Prompt Research: Multi-Class Classification

This document outlines the optimal prompt engineering strategies for using Gemma 4B/27B for high-accuracy multi-class (and multi-label) architectural classification of research papers.

## 1. Core Principles for Small Models (4B)
- **Extreme Precision**: Small models are sensitive to "instruction drift." Be terse and use high-signal keywords (e.g., "Extract," "Identify," "Classify").
- **Constraint Anchoring**: Place the most critical constraints (e.g., "ONLY respond with valid JSON") at the very end of the prompt to take advantage of recency effects.
- **Negative Constraints**: Clearly state what NOT to do (e.g., "Do not provide explanations outside the JSON object").

## 2. Multi-Class Strategy
- **Enumerated Taxonomy**: Provide the full list of category names and 1-sentence definitions directly in the prompt.
- **Mutual Exclusivity Logic**: If the system expects a single `primary_category`, explicitly instruct the model to "Choose the single most significant architectural contribution."
- **Confidence Scoring**: Ask the model to provide a numeric confidence score (0.0 - 1.0). This is useful for flagging low-confidence results for Gemini review.

## 3. Recommended Prompt Structure
Use standard control tokens for instruction-tuned Gemma:

```text
<start_of_turn>user
### Context
You are a senior AI research engineer specializing in Agentic Architectures, State Space Models (SSM), and World Models.

### Taxonomy
[Finalized list from patterns_table.md]

### Task
Analyze the provided Title and Abstract. 
1. Think step-by-step: Identify the core technical mechanism.
2. Search for evidence: Quote specific technical terms.
3. Classify: Map to the closest pattern in the taxonomy.

### Input
TITLE: {{title}}
ABSTRACT: {{abstract}}

### Output Requirements
Respond only with a valid JSON object. No preamble.
{
  "is_agentic": boolean,
  "reasoning": "Step 1... Step 2...",
  "primary_category": "pattern_name",
  "evidence": "quoted text",
  "confidence": 0.95
}
<end_of_turn>
<start_of_turn>model
<ctrl94>thought
```

## 4. Hyperparameter Tuning (Ollama)
- **Temperature**: `0.0` or `0.1` is mandatory for deterministic classification.
- **Num_ctx**: `8192` (minimum) to handle the 1000-word abstracts.
- **Format**: `json` (Enables Ollama's constrained decoding).

## 5. Few-Shot Examples (Crucial for 4B)
Include at least one "Positive" (Agentic/SSM) and one "Negative" (Generic Training/Eval) example to define the boundary.

**Example Positive**:
Input: "Mamba: Linear-Time Sequence Modeling..." -> Category: `input_selective_state_compression`.

**Example Negative**:
Input: "Measuring safety of LLMs..." -> Category: `agent_evaluation` (non-agentic).
