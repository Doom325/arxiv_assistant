"""
Shared taxonomy constants and prompt template for paper pattern classification.
Used by: production_worker.py, run_pattern_experiment.py, routers/patterns.py
"""

# ─────────────────────────────────────────────────────
# TAXONOMY DEFINITION
# ─────────────────────────────────────────────────────

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

# Agentic categories (agent_* and multi_agent)
AGENTIC_CATEGORIES = {
    "agent_memory", "agent_planning", "agent_tool_use", "multi_agent", "agent_evaluation"
}

# ─────────────────────────────────────────────────────
# HUMAN-READABLE LABELS
# ─────────────────────────────────────────────────────

CATEGORY_LABELS = {
    "agent_memory": "Agent Memory",
    "agent_planning": "Agent Planning",
    "agent_tool_use": "Agent Tool Use",
    "multi_agent": "Multi-Agent Systems",
    "agent_evaluation": "Agent Evaluation",
    "training": "Training Methods",
    "inference": "Inference Optimization",
    "architecture": "Model Architecture",
    "world_models": "World Models",
    "state_space_models": "State Space Models",
}

PATTERN_LABELS = {
    # Agent Memory
    "retrieval_augmented": "Retrieval-Augmented",
    "persistent_memory": "Persistent Memory",
    "working_memory": "Working Memory",
    "episodic": "Episodic Memory",
    # Agent Planning
    "reasoning_acting": "Reasoning & Acting (ReAct)",
    "tree_search": "Tree Search",
    "goal_decomposition": "Goal Decomposition",
    "chain_of_thought": "Chain of Thought",
    # Agent Tool Use
    "function_calling": "Function Calling",
    "code_execution": "Code Execution",
    "api_orchestration": "API Orchestration",
    "browser_use": "Browser Use",
    # Multi-Agent
    "collaboration": "Collaboration",
    "debate": "Debate",
    "hierarchical_control": "Hierarchical Control",
    "role_specialization": "Role Specialization",
    # Agent Evaluation
    "benchmarking": "Benchmarking",
    "safety": "Safety",
    "capability_measurement": "Capability Measurement",
    # Training
    "rlhf": "RLHF",
    "dpo": "DPO",
    "supervised_finetuning": "Supervised Fine-Tuning",
    "reward_modeling": "Reward Modeling",
    "synthetic_data": "Synthetic Data",
    # Inference
    "speculative_decoding": "Speculative Decoding",
    "quantization": "Quantization",
    "distillation": "Distillation",
    "efficient_attention": "Efficient Attention",
    # Architecture
    "attention_mechanism": "Attention Mechanism",
    "mixture_of_experts": "Mixture of Experts",
    "hybrid_architecture": "Hybrid Architecture",
    "transformers": "Transformers",
    # World Models
    "learned_dynamics": "Learned Dynamics",
    "model_based_rl": "Model-Based RL",
    "environment_simulation": "Environment Simulation",
    "predictive_modeling": "Predictive Modeling",
    # State Space Models
    "mamba": "Mamba",
    "s4": "S4",
    "linear_recurrence": "Linear Recurrence",
    "selective_state_spaces": "Selective State Spaces",
}

# ─────────────────────────────────────────────────────
# CATEGORY ICONS (for frontend reference)
# ─────────────────────────────────────────────────────

CATEGORY_ICONS = {
    "agent_memory": "brain",
    "agent_planning": "route",
    "agent_tool_use": "wrench",
    "multi_agent": "users",
    "agent_evaluation": "clipboard-check",
    "training": "dumbbell",
    "inference": "zap",
    "architecture": "building",
    "world_models": "globe",
    "state_space_models": "activity",
}

# ─────────────────────────────────────────────────────
# V6 CoT PROMPT TEMPLATE
# ─────────────────────────────────────────────────────

PROMPT_VERSION = "v6_cot"

V6_COT_PROMPT = """You are a precise AI/ML research paper classifier.

TASK: Read the paper below and classify it. You MUST think step-by-step before classifying.

RULES:
1. ONLY use exact category/name values from the taxonomy. Never invent new ones.
2. Only include patterns with confidence >= 0.7.
3. If no category fits, return an empty patterns list.
4. "is_agentic" = true ONLY if the paper builds a system where an AI agent autonomously decides, acts, and interacts with tools/environments in a loop. Training methods, model architectures, benchmarks, hardware, and standard RL (TD3, PPO, Q-learning) are NOT agentic.

TAXONOMY:
- agent_memory: [retrieval_augmented, persistent_memory, working_memory, episodic]
- agent_planning: [reasoning_acting, tree_search, goal_decomposition, chain_of_thought]
- agent_tool_use: [function_calling, code_execution, api_orchestration, browser_use]
- multi_agent: [collaboration, debate, hierarchical_control, role_specialization]
- agent_evaluation: [benchmarking, safety, capability_measurement]
- training: [rlhf, dpo, supervised_finetuning, reward_modeling, synthetic_data]
  (rlhf = RL from Human Feedback ONLY, not general RL)
- inference: [speculative_decoding, quantization, distillation, efficient_attention]
- architecture: [attention_mechanism, mixture_of_experts, hybrid_architecture, transformers]
- world_models: [learned_dynamics, model_based_rl, environment_simulation, predictive_modeling]
- state_space_models: [mamba, s4, linear_recurrence, selective_state_spaces]

PAPER:
Title: {title}
Abstract: {abstract}

You must respond with a single JSON object. The FIRST field must be "reasoning" where you think step-by-step about:
- What is this paper actually about?
- Does it describe an autonomous AI agent that acts in a loop? Or is it about training/architecture/evaluation?
- Which taxonomy categories genuinely apply?

Then output the classification fields.

Output format:
{{"reasoning": "Step 1: This paper is about... Step 2: It is/is not agentic because... Step 3: The matching categories are...", "is_agentic": true/false, "primary_category": "...", "patterns": [{{"category": "...", "name": "...", "confidence": 0.9, "evidence": "quote from abstract"}}]}}"""


# ─────────────────────────────────────────────────────
# VALIDATION HELPERS
# ─────────────────────────────────────────────────────

def validate_classification_output(parsed: dict | None) -> list[str]:
    """Check if LLM output adheres to taxonomy. Returns list of violation strings."""
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
