# Prompt Evaluation Results

**Model:** gemma3:27b  
**Prompt Pattern Version:** v6_cot  
**Date:** 2026-04-03 20:43  
**Papers tested:** 71 of 71  

## Overview Metrics

| Metric | Result |
|---|---|
| Average Time/Paper | 40.4s |
| Total Taxonomy Violations | 6 |
| Parse / Network Errors | 0 |
| `primary_category` Match Rate vs Baseline | 49.3% |
| `is_agentic` Match Rate vs Baseline | 85.9% |

## Detailed Results

### Baseline Category: `agent_evaluation` (Match: 80.0%)

#### ⚠️ 2512.16279v1: QuadSentinel: Sequent Safety for Machine-Checkable Control in Multi-ag
- **Time:** 45.4s
- **Category:** Got `multi_agent` (Expected: `agent_evaluation`)
- **Agentic:** Got `False` (Expected: `False`)
- **CoT Reasoning:**
  > Step 1: This paper addresses safety concerns in multi-agent systems powered by LLMs, specifically focusing on the difficulty of translating natural language safety policies into machine-checkable rules for reliable runtime enforcement. It proposes QuadSentinel, a four-agent system designed to compile policies into these rules and enforce them. Step 2: The paper describes a system with multiple agents interacting to enforce safety, but it doesn't focus on the agents *learning* to act or improving their actions through a loop. It's more about a runtime safety *system* built on top of agents, rather than the agents themselves being the primary focus of learning or autonomous action. Therefore, it is not strongly agentic. Step 3: The core of the paper is about multi-agent systems and safety. The description of the four-agent guard (state tracker, policy verifier, threat watcher, and referee) clearly falls under multi-agent collaboration. The focus on safety and evaluation of the system on benchmarks also suggests a category related to agent evaluation.

#### ✅ 2512.21110v1: Beyond Context: Large Language Models Failure to Grasp Users Intent
- **Time:** 41.4s
- **Category:** Got `agent_evaluation` (Expected: `agent_evaluation`)
- **Agentic:** Got `False` (Expected: `False`)
- **CoT Reasoning:**
  > Step 1: This paper investigates the failure of Large Language Models (LLMs) to understand user intent, leading to vulnerabilities in safety mechanisms. It demonstrates how malicious users can bypass these mechanisms using techniques like emotional framing and progressive revelation. The study evaluates several LLMs and finds that even reasoning-enabled models don't necessarily improve safety regarding intent recognition. Step 2: The paper does *not* describe an autonomous AI agent that acts in a loop. It's an evaluation of existing LLMs and their vulnerabilities, focusing on safety and understanding user intent. Therefore, it is not agentic. Step 3: The primary focus is on evaluating the capability of LLMs to understand user intent and the effectiveness of safety mechanisms. This aligns with 'agent_evaluation', specifically 'capability_measurement'. The paper also touches on reasoning, which could relate to 'agent_planning', but the core is evaluation, not building a planning system.

#### ✅ 2512.21080v1: LLM Personas as a Substitute for Field Experiments in Method Benchmark
- **Time:** 28.5s
- **Category:** Got `agent_evaluation` (Expected: `agent_evaluation`)
- **Agentic:** Got `False` (Expected: `False`)
- **CoT Reasoning:**
  > Step 1: This paper investigates the use of LLM-based personas as a substitute for traditional field experiments (A/B tests) in method benchmarking, particularly in societal systems. It focuses on the conditions under which this substitution is valid, proving that it's equivalent to simply changing the evaluation population under specific circumstances (aggregate-only observation and algorithm-blind evaluation). Step 2: The paper does *not* describe an autonomous AI agent that acts in a loop. It's about a benchmarking methodology and the validity of using LLMs to *simulate* human behavior for evaluation purposes. It's a paper about evaluation, not about building an agent. Step 3: The primary category is 'agent_evaluation', specifically 'benchmarking'. The paper discusses the conditions for valid benchmarking using synthetic data (LLM personas).

#### ✅ 2512.20983v1: Automatic Replication of LLM Mistakes in Medical Conversations
- **Time:** 39.0s
- **Category:** Got `agent_evaluation` (Expected: `agent_evaluation`)
- **Agentic:** Got `False` (Expected: `False`)
- **CoT Reasoning:**
  > Step 1: This paper introduces a pipeline called MedMistake that automatically identifies mistakes made by LLMs in medical conversations and converts them into a QA benchmark. It involves simulating patient-doctor conversations with LLMs, evaluating the responses, and then distilling the errors into single-shot QA pairs. Step 2: The system doesn't describe an autonomous agent acting in a loop. It's a pipeline for *evaluating* and *creating* benchmarks, not an agent that interacts with an environment. Therefore, it is not agentic. Step 3: The primary focus is on evaluation and dataset creation. The paper describes a method for benchmarking LLMs on medical conversations, specifically focusing on replicating mistakes. The creation of a QA dataset also falls under benchmarking. The pipeline involves evaluation using LLM judges, which is a form of capability measurement.

#### ⚠️ 2512.16707v1: Dual Computational Horizons: Incompleteness and Unpredictability in In
- **Time:** 35.5s
- **Category:** Got `agent_planning` (Expected: `agent_evaluation`)
- **Agentic:** Got `False` (Expected: `False`)
- **CoT Reasoning:**
  > Step 1: This paper is about fundamental limitations of intelligent systems, specifically concerning reasoning and prediction. It formalizes concepts of incompleteness and unpredictability and their impact on an agent's ability to understand its own predictive limits. Step 2: It is not agentic. The paper presents a theoretical analysis of limitations, not a description of an agent that acts and interacts with an environment. It doesn't detail a system where an AI autonomously decides and acts. Step 3: The matching categories are primarily related to agent planning and reasoning, as it discusses the limits of reasoning and prediction within an intelligent system. It also touches upon world models as prediction is a core component of building world models.

#### ✅ 2512.16755v1: CitySeeker: How Do VLMS Explore Embodied Urban Navigation With Implici
- **Time:** 42.4s
- **Category:** Got `agent_evaluation` (Expected: `agent_evaluation`)
- **Agentic:** Got `False` (Expected: `False`)
- **CoT Reasoning:**
  > Step 1: This paper introduces a new benchmark, CitySeeker, to evaluate VLMs' ability to navigate urban environments based on *implicit* human needs (like thirst). It tests spatial reasoning and decision-making in long-horizon scenarios. The core focus is on evaluating existing models on this new benchmark, identifying bottlenecks in their performance. Step 2: The paper does *not* describe building an autonomous agent that acts in a loop. It's about evaluating existing VLMs on a new task. Therefore, it is not agentic. It's primarily an evaluation of existing models. Step 3: The primary category is agent_evaluation, specifically benchmarking. The paper also touches on reasoning and decision-making, which relates to agent_planning, but the focus is on *measuring* those capabilities, not developing new planning methods. The mention of long-horizon reasoning and spatial cognition supports the relevance of agent_planning.

#### ✅ 2512.21236v1: Casting a SPELL: Sentence Pairing Exploration for LLM Limitation-break
- **Time:** 38.7s
- **Category:** Got `agent_evaluation` (Expected: `agent_evaluation`)
- **Agentic:** Got `False` (Expected: `False`)
- **Violations:** invented_pattern:training/safety
- **CoT Reasoning:**
  > Step 1: This paper introduces SPELL, a framework for testing the security alignment of LLMs specifically when generating malicious code. It focuses on jailbreaking LLMs to produce harmful software and systematically constructs prompts to evaluate weaknesses. Step 2: The paper does *not* describe an autonomous AI agent that acts in a loop. It's a testing framework, meaning it's about evaluating existing models, not building a new agent. Therefore, it is not agentic. Step 3: The primary focus is on evaluating LLMs, specifically their vulnerability to malicious prompt injection. The framework is used for 'benchmarking' the security alignment of LLMs. The paper also touches on the 'training' aspect, as it aims to identify weaknesses in the alignment process (though it doesn't propose a new training method).

#### ✅ 2512.21127v1: A Real-World Evaluation of LLM Medication Safety Reviews in NHS Primar
- **Time:** 37.3s
- **Category:** Got `agent_evaluation` (Expected: `agent_evaluation`)
- **Agentic:** Got `False` (Expected: `False`)
- **CoT Reasoning:**
  > Step 1: This paper is about evaluating the performance of a Large Language Model (LLM) in a real-world clinical setting – specifically, reviewing medication safety in NHS primary care data. It focuses on identifying issues and proposed interventions. Step 2: It is not agentic. The paper describes a system that *identifies* issues, but doesn't describe an agent that autonomously decides and acts in a loop. It's an evaluation of a system, not the creation of an autonomous agent. Step 3: The matching categories are primarily related to evaluation, specifically benchmarking the LLM's performance on real clinical data. The paper also touches on safety as it's evaluating medication safety reviews.

#### ✅ 2512.21238v1: Assessing the Software Security Comprehension of Large Language Models
- **Time:** 34.4s
- **Category:** Got `agent_evaluation` (Expected: `agent_evaluation`)
- **Agentic:** Got `False` (Expected: `False`)
- **CoT Reasoning:**
  > Step 1: This paper is about evaluating the ability of Large Language Models (LLMs) to understand and apply software security principles. It uses Bloom's Taxonomy to assess their cognitive abilities across different levels, from remembering to creating, using a variety of datasets including multiple-choice questions, vulnerable code, and course assessments. Step 2: It is not agentic because the paper focuses on *evaluating* existing LLMs, not *building* an autonomous agent that acts and interacts with an environment. It's a benchmark study, not a system that learns and acts. Step 3: The matching categories are primarily related to evaluation, specifically benchmarking the capabilities of LLMs in a specific domain (software security).

#### ✅ 2512.16553v1: Needle in the Web: A Benchmark for Retrieving Targeted Web Pages in th
- **Time:** 42.5s
- **Category:** Got `agent_evaluation` (Expected: `agent_evaluation`)
- **Agentic:** Got `False` (Expected: `False`)
- **CoT Reasoning:**
  > Step 1: This paper introduces a new benchmark, 'Needle in the Web', designed to evaluate LLM-based systems (specifically 'search agents') on their ability to retrieve and reason over web content for ambiguous queries. The focus is on 'Fuzzy Exploratory Search' which differs from benchmarks that focus on complex reasoning requiring multi-hop synthesis. Step 2: The paper describes systems that *use* web browsing as a tool, but it doesn't describe a system where an agent autonomously decides and acts in a loop. It's about evaluating existing systems on a new benchmark. Therefore, it is not agentic. Step 3: The primary category is agent_evaluation, specifically benchmarking. The mention of 'search agents' and evaluating their ability to retrieve and reason over web content supports this. The paper also touches on agent_tool_use (browser_use) as the agents are using web browsing, but this is secondary to the evaluation aspect.

---

### Baseline Category: `agent_memory` (Match: 0.0%)

#### ⚠️ 2512.16171v1: Science Consultant Agent
- **Time:** 37.4s
- **Category:** Got `agent_tool_use` (Expected: `agent_memory`)
- **Agentic:** Got `False` (Expected: `False`)
- **CoT Reasoning:**
  > Step 1: This paper describes a web-based AI tool called the 'Science Consultant Agent' designed to help users choose and implement modeling strategies for AI solutions. It has four components: a questionnaire, smart fill, recommendation engine, and prototype builder. Step 2: While the tool *assists* users, it doesn't autonomously decide and act in a loop. It responds to user input (questionnaire) and provides recommendations/prototypes. It's a tool *for* agents (humans), not an agent itself. Therefore, it is not agentic. Step 3: The primary focus is on building a system that provides recommendations and generates prototypes, which aligns with the idea of function calling and orchestration. The 'Research-Guided Recommendation' component suggests it leverages external knowledge sources. Therefore, 'agent_tool_use' is the most appropriate category.

#### ⚠️ 2512.20985v1: A Blockchain-Monitored Agentic AI Architecture for Trusted Perception-
- **Time:** 39.2s
- **Category:** Got `agent_planning` (Expected: `agent_memory`)
- **Agentic:** Got `True` (Expected: `True`)
- **CoT Reasoning:**
  > Step 1: This paper proposes an architecture for agentic AI systems that integrates a blockchain for trust, monitoring, and auditability. It focuses on a perception-reasoning-action cycle within a multi-agent system. Step 2: It *is* agentic because it describes a system where agents perform actions and the blockchain layer provides oversight, suggesting a closed-loop system of perception, reasoning, and action. Step 3: The primary category is 'agent_planning' as it focuses on the perception-reasoning-action cycle. 'multi_agent' also applies due to the mention of a LangChain-based multi-agent system. 'agent_evaluation' is relevant because of the monitoring and auditability aspects.

#### ⚠️ 2512.20959v1: Can Agentic AI Match the Performance of Human Data Scientists?
- **Time:** 37.9s
- **Category:** Got `agent_evaluation` (Expected: `agent_memory`)
- **Agentic:** Got `False` (Expected: `True`)
- **CoT Reasoning:**
  > Step 1: This paper investigates whether agentic AI systems can perform at the level of human data scientists, specifically in a scenario where domain knowledge is crucial for identifying hidden variables in image data. The focus is on a prediction task designed to highlight the limitations of AI systems that rely on generic code for tabular data. Step 2: The paper describes an 'agentic AI system' but doesn't detail its internal loop of decision-making, action, and interaction with an environment. It's more about *evaluating* the capabilities of such systems rather than *building* one. Therefore, it's not strongly agentic in the defined sense. Step 3: The primary focus is on evaluating the capability of agentic AI, and the paper describes a specific task designed to test this. The mention of 'agentic AI' and the comparison to human performance strongly suggest 'agent_evaluation'.

#### ⚠️ 2512.20491v2: Step-DeepResearch Technical Report
- **Time:** 46.3s
- **Category:** Got `agent_planning` (Expected: `agent_memory`)
- **Agentic:** Got `True` (Expected: `True`)
- **CoT Reasoning:**
  > Step 1: This paper introduces Step-DeepResearch, an agent designed for performing 'deep research' tasks. It focuses on improving the agent's ability to handle open-ended research, including intent recognition, long-horizon planning, and cross-source verification. The paper details a training strategy involving data synthesis, progressive training (mid-training, SFT, RL), and a checklist-based evaluation method. Step 2: The paper describes an autonomous agent that performs research tasks end-to-end, implying a loop of decision-making and action. Therefore, it is agentic. Step 3: The primary focus is on building and training this agent, with specific emphasis on planning, training methodologies, and evaluation. The agent uses a data synthesis strategy to improve planning and report writing, and the training path includes SFT and RL. The paper also introduces a new benchmark for evaluation. Therefore, the matching categories are agent_planning, training, and agent_evaluation.

#### ⚠️ 2512.21039v1: Agentic Multi-Persona Framework for Evidence-Aware Fake News Detection
- **Time:** 44.9s
- **Category:** Got `agent_planning` (Expected: `agent_memory`)
- **Agentic:** Got `False` (Expected: `True`)
- **CoT Reasoning:**
  > Step 1: This paper proposes a framework (AMPEND-LS) for detecting fake news by integrating multimodal information and reasoning about evidence. It uses LLMs and SLMs in a pipeline to analyze text, images, and context. Step 2: The paper describes a system that *performs* a reasoning pipeline, but it doesn't describe an agent that autonomously decides and acts in a loop. It's a framework for detection, not an agent acting in an environment. Therefore, it is not agentic. Step 3: The key categories are related to agent-like behavior (reasoning, evidence gathering) but fall short of full agency. The framework uses reasoning and tool use (reverse image search, knowledge graph paths) but doesn't demonstrate autonomous action. The 'agentic' framing in the title is a bit misleading; it's more about a structured reasoning process than a true agent. The most relevant categories are agent_planning and agent_tool_use.

#### ⚠️ 2512.21220v1: RoboSafe: Safeguarding Embodied Agents via Executable Safety Logic
- **Time:** 43.9s
- **Category:** Got `agent_evaluation` (Expected: `agent_memory`)
- **Agentic:** Got `True` (Expected: `False`)
- **Violations:** invented_pattern:agent_memory/hybrid_architecture
- **CoT Reasoning:**
  > Step 1: This paper addresses the safety of embodied agents (robots) that use vision-language models. It proposes a runtime safeguard called RoboSafe to prevent unsafe behaviors triggered by hazardous instructions. The system uses executable safety logic and a hybrid memory to reason about safety during task execution. Step 2: The paper describes an autonomous agent (embodied robot) that acts in an environment and requires safety mechanisms during its operation. It's not solely about training, architecture, or evaluation, although evaluation would likely be part of validating the safety system. Therefore, it is agentic. Step 3: The core of the paper revolves around safeguarding an agent during execution, making 'agent_evaluation' relevant. The 'hybrid memory' component suggests 'agent_memory'. The use of 'reasoning' to determine safe actions points to 'agent_planning'.

#### ⚠️ 2512.20848v1: Nemotron 3 Nano: Open, Efficient Mixture-of-Experts Hybrid Mamba-Trans
- **Time:** 53.6s
- **Category:** Got `architecture` (Expected: `agent_memory`)
- **Agentic:** Got `False` (Expected: `True`)
- **CoT Reasoning:**
  > Step 1: This paper introduces Nemotron 3 Nano, a new language model that combines Mamba and Transformer architectures with a Mixture-of-Experts approach. It focuses on improving efficiency and performance in terms of throughput and accuracy. The model is pretrained and then fine-tuned with supervised learning and reinforcement learning. Step 2: The paper claims enhanced 'agentic' abilities, but the description focuses on training and model architecture. The RL is large-scale, but doesn't describe an agent autonomously acting in an environment in a loop. It's more about improving the model's capabilities through RL, not building an agent. Therefore, it is not truly agentic. Step 3: The primary category is architecture, as the paper details a novel model structure. Relevant patterns include the hybrid architecture, mixture of experts, and training via supervised finetuning and RL. The claim of 'agentic reasoning' is a capability demonstrated by the model, not the core focus of the paper.

#### ⚠️ 2512.20991v1: FinAgent: An Agentic AI Framework Integrating Personal Finance and Nut
- **Time:** 57.2s
- **Category:** Got `agent_planning` (Expected: `agent_memory`)
- **Agentic:** Got `True` (Expected: `True`)
- **CoT Reasoning:**
  > Step 1: This paper presents an agentic AI framework called FinAgent that integrates personal finance and nutrition planning. It aims to create meal plans that are both nutritionally sufficient and affordable, considering household income, expenses, health status, and real-time food prices. Step 2: The system is agentic because it describes a modular multi-agent architecture where agents (budgeting, nutrition, price monitoring, health personalization) interact and share knowledge to achieve a goal (nutritionally sufficient and affordable meal plans). The agents dynamically adjust to market changes, indicating a closed-loop autonomous decision-making process. Step 3: The primary category is 'agent_planning' as the system focuses on reasoning and acting to achieve a complex goal. The 'multi_agent' category also applies due to the modular architecture with specialized agents. 'agent_tool_use' applies because the system uses real-time price monitoring, which can be considered a tool. The description of knowledge sharing suggests 'agent_memory' is also relevant.

---

### Baseline Category: `agent_planning` (Match: 100.0%)

#### ✅ 2512.20586v1: Automated stereotactic radiosurgery planning using a human-in-the-loop
- **Time:** 39.4s
- **Category:** Got `agent_planning` (Expected: `agent_planning`)
- **Agentic:** Got `False` (Expected: `True`)
- **CoT Reasoning:**
  > Step 1: This paper presents SAGE, an LLM-based agent for automated stereotactic radiosurgery (SRS) treatment planning. The agent generates treatment plans and the paper compares plans generated with and without chain-of-thought reasoning. Step 2: The agent *plans* treatment, but the paper describes a retrospective study evaluating the plans. It doesn't describe the agent acting in a continuous loop, interacting with an environment, or using tools autonomously. Therefore, it is not fully agentic, despite the use of the word 'agent'. It's more about building a system and evaluating its planning capabilities. Step 3: The core of the paper is about the agent's planning process, specifically using chain-of-thought reasoning. The evaluation of the plans also fits a category.

#### ✅ 2512.21066v1: Agentic Explainable Artificial Intelligence (Agentic XAI) Approach To 
- **Time:** 43.6s
- **Category:** Got `agent_planning` (Expected: `agent_planning`)
- **Agentic:** Got `True` (Expected: `True`)
- **CoT Reasoning:**
  > Step 1: This paper proposes a framework called 'Agentic XAI' which combines SHAP explainability with LLMs to generate better explanations. The LLM iteratively refines explanations. The use case is an agricultural recommendation system. Step 2: The paper describes an LLM operating as an agent that iteratively refines explanations, which constitutes a loop of decision-making and action (explanation refinement). Therefore, it *is* agentic. Step 3: The primary category is agent_planning because the LLM is actively 'reasoning' and 'acting' to improve explanations. The 'agent_memory' category (specifically working_memory) also applies as the LLM refines explanations based on previous iterations. The paper also touches on 'agent_evaluation' as it tests the framework with real-world data.

#### ✅ 2512.21243v1: LookPlanGraph: Embodied Instruction Following Method with VLM Graph Au
- **Time:** 45.6s
- **Category:** Got `agent_planning` (Expected: `agent_planning`)
- **Agentic:** Got `True` (Expected: `False`)
- **CoT Reasoning:**
  > Step 1: This paper presents LookPlanGraph, a method for embodied instruction following using Large Language Models (LLMs) as planners. The key idea is to augment the LLM's planning process with a scene graph that is dynamically updated during task execution to account for environmental changes. Step 2: The paper describes a system where an LLM plans and acts (through a robot) based on the updated scene graph. The continuous updating of the graph and execution of the plan suggests a loop of perception, planning, and action, making it agentic. Step 3: The primary category is agent_planning, specifically reasoning_acting, as the system focuses on how the LLM reasons about the environment and acts accordingly. The use of a scene graph to ground the LLM in the environment also relates to agent_memory (specifically persistent_memory, as the graph represents a persistent understanding of the environment).

#### ✅ 2512.16301v1: Adaptation of Agentic AI
- **Time:** 45.5s
- **Category:** Got `agent_planning` (Expected: `agent_planning`)
- **Agentic:** Got `False` (Expected: `False`)
- **CoT Reasoning:**
  > Step 1: This paper is about the adaptation of agentic AI systems, focusing on how these systems can improve their performance, reliability, and generalization through adaptation mechanisms. It proposes a framework for understanding different types of adaptation, both for the agent itself and the tools it uses. Step 2: The paper discusses 'agentic AI systems' which implies autonomous agents that plan, reason, and interact with tools. However, the paper focuses on *how* to adapt these agents, not on building a new agent or a new training method. It's a high-level framework for understanding adaptation strategies, not an implementation of an agent acting in a loop. Therefore, it is not strongly agentic, but the topic is about agentic systems. Step 3: The primary category is likely related to agent planning or agent evaluation, as the paper discusses improving performance and generalization. The patterns that apply are related to agent planning, as adaptation is a key component of planning and reasoning, and potentially agent evaluation as it discusses improving performance and reliability.

---

### Baseline Category: `agent_tool_use` (Match: 57.1%)

#### ✅ 2512.20745v1: AgentMath: Empowering Mathematical Reasoning for Large Language Models
- **Time:** 52.8s
- **Category:** Got `agent_tool_use` (Expected: `agent_tool_use`)
- **Agentic:** Got `True` (Expected: `True`)
- **CoT Reasoning:**
  > Step 1: This paper introduces AgentMath, a framework that combines LLM reasoning with code interpreters to solve complex mathematical problems. It focuses on converting natural language reasoning into structured tool-augmented trajectories and uses this to generate training data. It also mentions agentic reinforcement learning. Step 2: The paper describes an agent framework that uses a loop of reasoning and tool use (code interpreter). The agent autonomously decides on actions (tool calls) based on the problem and reasoning steps. Therefore, it is agentic. Step 3: The key categories are agent_tool_use (function calling/code execution), training (supervised_finetuning, reward_modeling - due to the mention of reinforcement learning), and potentially agent_planning (reasoning_acting) as it involves chain-of-thought reasoning.

#### ⚠️ 2512.20856v1: NVIDIA Nemotron 3: Efficient and Open Intelligence
- **Time:** 57.6s
- **Category:** Got `architecture` (Expected: `agent_tool_use`)
- **Agentic:** Got `True` (Expected: `True`)
- **CoT Reasoning:**
  > Step 1: This paper introduces the Nemotron 3 family of language models, focusing on their architecture, training, and capabilities. The models are described as having strong agentic, reasoning, and conversational abilities. Step 2: The paper states the models are post-trained using multi-environment reinforcement learning to enable reasoning, tool use, and reasoning budget control. This suggests an agentic component, where the model can perform multi-step tool use. However, the core of the paper is about the model architecture and training process, not a fully autonomous agent acting in a continuous loop. The RL is used as a post-training step to *enable* capabilities, not as the primary focus of the research. Step 3: The key categories are architecture (Mixture-of-Experts, Mamba-Transformer), training (RL), and agent-related categories due to the described capabilities. The mention of tool use and reasoning also suggests relevant categories.

#### ⚠️ 2512.16301v1: Adaptation of Agentic AI
- **Time:** 49.3s
- **Category:** Got `agent_planning` (Expected: `agent_tool_use`)
- **Agentic:** Got `True` (Expected: `False`)
- **Violations:** invented_pattern:agent_memory/generalization
- **CoT Reasoning:**
  > Step 1: This paper is about the adaptation of agentic AI systems, focusing on how these systems can improve their performance, reliability, and generalization through adaptation mechanisms. It proposes a framework for understanding different types of adaptation, both for the agent itself and the tools it uses. Step 2: The paper discusses 'agentic AI systems' which implies autonomous agents that plan, reason, and interact with tools. However, the paper focuses on *how* to adapt these agents, not on building a new agent or a new training method. It's a high-level framework for understanding adaptation strategies. Therefore, it's agentic, but not in the sense of presenting a new agent implementation. Step 3: The primary category is agent_planning, as the paper centers around how agents plan and reason to adapt. The patterns include agent_memory (due to the discussion of improving generalization), and potentially agent_tool_use (since adaptation involves interaction with tools), but these are less central than the planning aspect.

#### ✅ 2512.20957v1: One Tool Is Enough: Reinforcement Learning for Repository-Level LLM Ag
- **Time:** 46.3s
- **Category:** Got `agent_tool_use` (Expected: `agent_tool_use`)
- **Agentic:** Got `True` (Expected: `True`)
- **Violations:** invented_pattern:training/rl
- **CoT Reasoning:**
  > Step 1: This paper introduces RepoNavigator, an LLM agent designed to navigate and modify large open-source software repositories. The core idea is to use a single tool that allows the agent to jump to the definition of a symbol, mimicking code execution. Step 2: The paper describes an agent that acts in a loop – it navigates the repository, uses a tool to find definitions, and presumably continues this process to locate and modify code. It's trained via RL, but the focus is on the agent's behavior and interaction with the repository, making it agentic. Step 3: The primary category is agent_tool_use, specifically function_calling as the agent uses a tool to 'jump to the definition'. The training method is RL, but it's not RLHF or DPO. The agent also exhibits agent_planning through reasoning about code execution.

#### ✅ 2512.20745v1: AgentMath: Empowering Mathematical Reasoning for Large Language Models
- **Time:** 46.1s
- **Category:** Got `agent_tool_use` (Expected: `agent_tool_use`)
- **Agentic:** Got `True` (Expected: `True`)
- **CoT Reasoning:**
  > Step 1: This paper introduces AgentMath, a framework that combines LLM reasoning with code interpreters to solve complex mathematical problems. It focuses on converting natural language reasoning into structured tool-augmented trajectories and uses this to generate training data. It also mentions agentic reinforcement learning. Step 2: The paper describes an agent framework that *integrates* reasoning and computation, but the abstract only mentions 'agentic reinforcement learning' without detailing a full autonomous loop of perception, decision, action, and interaction with an environment. The core seems to be about training the agent with generated data. Therefore, it's partially agentic but not fully. Step 3: The matching categories are agent_tool_use (function calling/code execution), training (supervised_finetuning, reward_modeling), and potentially agent_planning (reasoning_acting) given the chain-of-thought aspect.

#### ⚠️ 2512.20996v1: TrafficSimAgent: A Hierarchical Agent Framework for Autonomous Traffic
- **Time:** 45.4s
- **Category:** Got `agent_planning` (Expected: `agent_tool_use`)
- **Agentic:** Got `True` (Expected: `True`)
- **CoT Reasoning:**
  > Step 1: This paper introduces TrafficSimAgent, a framework that uses an LLM-based agent to simplify traffic simulation experiments. The agent framework is designed to understand instructions, plan experiments, and execute them. It uses a hierarchical structure with 'expert agents' collaborating at different levels. Step 2: The paper describes an autonomous agent that plans and executes experiments, indicating a loop of perception (instruction), planning, and action (experiment execution). Therefore, it is agentic. Step 3: The primary category is 'agent_planning' as the core contribution is the planning and orchestration of experiments. The hierarchical structure and collaboration between agents also suggest 'multi_agent'. The use of an LLM is a component of the agent, but not the primary focus. The mention of 'MCP control' suggests a control mechanism within the agent's actions, fitting within planning.

#### ✅ 2512.16171v1: Science Consultant Agent
- **Time:** 39.0s
- **Category:** Got `agent_tool_use` (Expected: `agent_tool_use`)
- **Agentic:** Got `False` (Expected: `False`)
- **CoT Reasoning:**
  > Step 1: This paper describes a web-based AI tool called the 'Science Consultant Agent' designed to help users choose and implement modeling strategies for AI solutions. It has four components: a questionnaire, smart fill, recommendation engine, and prototype builder. Step 2: While the tool *assists* users, it doesn't autonomously decide and act in a loop. It responds to user input (questionnaire) and provides recommendations/prototypes. It's a tool *for* agents (developers, researchers), not an agent itself. Therefore, it is not agentic. Step 3: The primary focus is on building a system that provides recommendations and generates prototypes, which aligns with the idea of tool use. The 'Research-Guided Recommendation' component is key. The system doesn't seem to focus on training, inference, architecture, or world models, but rather on *using* existing models and knowledge to assist users.

---

### Baseline Category: `architecture` (Match: 80.0%)

#### ✅ 2512.21118v1: STLDM: Spatio-Temporal Latent Diffusion Model for Precipitation Nowcas
- **Time:** 40.9s
- **Category:** Got `architecture` (Expected: `architecture`)
- **Agentic:** Got `False` (Expected: `False`)
- **CoT Reasoning:**
  > Step 1: This paper presents a new model, STLDM, for precipitation nowcasting, which is a spatio-temporal prediction task. It aims to improve upon existing deterministic and generative models by combining their strengths. The model uses a diffusion-based approach with a variational autoencoder and a conditioning network. Step 2: The paper describes a model architecture and training process, but it does *not* describe an autonomous agent that acts in a loop or interacts with an environment. It's a predictive model, not an agent. Therefore, it is not agentic. Step 3: The primary category is 'architecture' as the paper focuses on a novel model architecture. The diffusion model aspect and the use of a variational autoencoder are relevant. The mention of 'learning the latent representation' also points to architectural choices.

#### ✅ 2512.21135v1: TGC-Net: A Structure-Aware and Semantically-Aligned Framework for Text
- **Time:** 41.2s
- **Category:** Got `architecture` (Expected: `architecture`)
- **Agentic:** Got `False` (Expected: `False`)
- **CoT Reasoning:**
  > Step 1: This paper introduces TGC-Net, a framework for medical image segmentation that leverages text from clinical reports to improve accuracy. It addresses limitations of directly applying CLIP to medical images by focusing on preserving anatomical structures, modeling clinical descriptions, and aligning semantics. Step 2: The paper does *not* describe an autonomous AI agent acting in a loop. It's a method for improving segmentation, which is a supervised learning task. It's about model architecture and training adaptations. Step 3: The primary category is architecture, as the paper proposes a new framework (TGC-Net) and encoder (SSE). The use of CLIP and task-specific adaptations also fall under architecture. There's also a connection to training, as it's a parameter-efficient adaptation of a pre-trained model.

#### ✅ 2512.20963v1: Generalization of Diffusion Models Arises with a Balanced Representati
- **Time:** 44.7s
- **Category:** Got `architecture` (Expected: `architecture`)
- **Agentic:** Got `False` (Expected: `False`)
- **CoT Reasoning:**
  > Step 1: This paper investigates the difference between memorization and generalization in diffusion models, framing it as a representation learning problem. It uses a denoising autoencoder to theoretically analyze how 'spiky' vs. 'balanced' representations relate to these phenomena, and then validates these findings on real diffusion models. Step 2: The paper does *not* describe an autonomous AI agent that acts in a loop. It's a theoretical and empirical analysis of existing model behavior, not the creation of a new agent. Therefore, it is not agentic. Step 3: The core focus is on understanding the representations learned by diffusion models, which relates to the underlying architecture and how it affects generalization. The analysis of memorization and generalization can be seen as a form of capability measurement, but it's not a formal benchmark. The use of a denoising autoencoder is related to model architecture.

#### ✅ 2512.21083v1: Hierarchical Modeling Approach to Fast and Accurate Table Recognition
- **Time:** 36.4s
- **Category:** Got `architecture` (Expected: `architecture`)
- **Agentic:** Got `False` (Expected: `False`)
- **CoT Reasoning:**
  > Step 1: This paper focuses on improving the speed and accuracy of table recognition in documents. It proposes a new multi-task model with non-causal attention and a parallel inference algorithm. The core problem is document understanding, specifically table structure, cell position, and content recognition. Step 2: The paper does *not* describe an autonomous AI agent acting in a loop. It's a model architecture and inference optimization for a specific task. Therefore, it is not agentic. Step 3: The relevant categories are 'architecture' due to the novel model design with non-causal attention, and 'inference' because it introduces a parallel inference algorithm for faster processing. The mention of multi-task learning also hints at an architectural approach.

#### ✅ 2512.21000v1: CoSeNet: A Novel Approach for Optimal Segmentation of Correlation Matr
- **Time:** 33.8s
- **Category:** Got `architecture` (Expected: `architecture`)
- **Agentic:** Got `False` (Expected: `False`)
- **CoT Reasoning:**
  > Step 1: This paper presents a new model, CoSeNet, for identifying correlated segments within correlation matrices. It focuses on the algorithmic architecture of the model and a method for optimizing its parameters. Step 2: The paper does *not* describe an autonomous AI agent that acts in a loop. It's a model architecture focused on a specific data processing task. Therefore, it is not agentic. Step 3: The primary focus is on the model's architecture. The use of 'pre-trained Machine Learning algorithms' suggests a training component, but the paper doesn't detail a novel training method itself. The description of the four-layer architecture directly relates to the 'architecture' category.

#### ✅ 2512.20724v1: SA-DiffuSeq: Addressing Computational and Scalability Challenges in Lo
- **Time:** 35.7s
- **Category:** Got `architecture` (Expected: `architecture`)
- **Agentic:** Got `False` (Expected: `False`)
- **CoT Reasoning:**
  > Step 1: This paper addresses the computational challenges of using diffusion models for long-document text generation. It proposes a new framework, SA-DiffuSeq, that uses sparse attention to improve scalability and efficiency. The core idea is to reduce computational complexity during the diffusion process while maintaining text quality. Step 2: The paper does *not* describe an autonomous AI agent that acts in a loop. It focuses on a model architecture and optimization technique for text generation. Therefore, it is not agentic. Step 3: The primary category is 'architecture' as the paper introduces a new model framework. The use of 'sparse attention' directly falls under the 'attention_mechanism' subcategory. The paper also touches on improving efficiency, which could be loosely related to 'inference', but the core contribution is architectural.

#### ✅ 2512.20978v1: GenTSE: Enhancing Target Speaker Extraction via a Coarse-to-Fine Gener
- **Time:** 34.8s
- **Category:** Got `architecture` (Expected: `architecture`)
- **Agentic:** Got `False` (Expected: `False`)
- **CoT Reasoning:**
  > Step 1: This paper focuses on Target Speaker Extraction (TSE) using a generative language model approach. It proposes a two-stage decoder-only model (GenTSE) that first predicts semantic tokens and then generates acoustic tokens. The core idea is to separate semantic and acoustic information for better speech synthesis. Step 2: The paper does *not* describe an autonomous AI agent that acts in a loop. It's a model architecture and training method for a specific speech task. It's about improving the quality of generated speech, not about an agent interacting with an environment. Step 3: The relevant categories are 'architecture' because it proposes a new model structure, and 'training' because it uses techniques like Frozen-LM Conditioning and DPO (Direct Preference Optimization).

#### ✅ 2512.21170v1: A Unified Framework for EEG Seizure Detection Using Universum-Integrat
- **Time:** 42.3s
- **Category:** Got `architecture` (Expected: `architecture`)
- **Agentic:** Got `False` (Expected: `False`)
- **CoT Reasoning:**
  > Step 1: This paper introduces two new classifiers, U-GEPSVM and IU-GEPSVM, for EEG signal classification. It focuses on improving the performance of Support Vector Machines in the context of EEG data, which is characterized by non-stationarity, low signal-to-noise ratio, and limited labeled data. The core idea is to incorporate 'Universum learning' to enhance generalization. Step 2: This paper does *not* describe an autonomous AI agent that acts in a loop. It's a method for classification, a type of model architecture and evaluation. It doesn't involve an agent making decisions and interacting with an environment. Step 3: The primary category is 'architecture' as it proposes a new model architecture (U-GEPSVM and IU-GEPSVM). The 'training' category could also apply since the models are evaluated, but the focus is on the model itself, not the training process. The confidence is high because the paper explicitly details a new classification model.

#### ⚠️ 2512.21301v1: Transcriptome-Conditioned Personalized De Novo Drug Generation for AML
- **Time:** 27.7s
- **Category:** Got `None` (Expected: `architecture`)
- **Agentic:** Got `False` (Expected: `False`)
- **CoT Reasoning:**
  > Step 1: This paper describes a computational framework for de novo drug discovery for Acute Myeloid Leukemia (AML). It uses patient transcriptomics to identify drug targets and then models their structures to find druggable hotspots. The core of the work is about building a pipeline for drug discovery, not an autonomous agent. Step 2: It is not agentic because it's a static pipeline for drug discovery. There's no mention of an AI agent that autonomously decides, acts, and interacts with tools/environments in a loop. It's a computational method, not an agent. Step 3: The paper focuses on a computational method for drug discovery, utilizing transcriptomics and structural modeling. There are no categories that strongly fit this paper within the provided taxonomy.

#### ⚠️ 2512.16676v1: DataFlow: An LLM-Driven Framework for Unified Data Preparation and Wor
- **Time:** 38.1s
- **Category:** Got `training` (Expected: `architecture`)
- **Agentic:** Got `False` (Expected: `False`)
- **CoT Reasoning:**
  > Step 1: This paper introduces DataFlow, a framework for data preparation pipelines leveraging LLMs. It focuses on building modular, reusable data transformations and a PyTorch-style API for constructing these pipelines. The core idea is to improve data preparation for LLMs by providing a more structured and reproducible system. Step 2: The paper does *not* describe an autonomous AI agent that acts in a loop. It's a framework for *building* data pipelines, not an agent that uses them to achieve goals. It's about the infrastructure supporting LLMs, not an LLM acting as an agent. Step 3: The primary category is likely related to training, as the framework aims to improve data quality for LLMs, which is a crucial part of the training process. The reusable operators and pipeline construction API suggest a focus on building better training data. No other categories strongly apply.

---

### Baseline Category: `inference` (Match: 62.5%)

#### ✅ 2512.21323v1: Parallel Token Prediction for Language Models
- **Time:** 40.4s
- **Category:** Got `inference` (Expected: `inference`)
- **Agentic:** Got `False` (Expected: `False`)
- **Violations:** invented_pattern:training/distillation
- **CoT Reasoning:**
  > Step 1: This paper introduces a new framework called Parallel Token Prediction (PTP) for faster sequence generation in language models. It aims to reduce latency by predicting multiple tokens simultaneously within a single transformer call. The method can be trained via distillation or inverse autoregressive training. Step 2: The paper does *not* describe an autonomous AI agent that acts in a loop. It focuses on improving the inference speed of language models, specifically the decoding process. It's a technique for making existing models faster, not building an agent. Step 3: The primary category is 'inference' because the paper focuses on improving the efficiency of generating text from a language model. The 'speculative decoding' pattern is highly relevant, as the paper claims state-of-the-art performance in this area. 'distillation' is also relevant as a training method used to implement PTP.

#### ⚠️ 2512.20929v1: Decoding Predictive Inference in Visual Language Processing via Spatio
- **Time:** 26.9s
- **Category:** Got `None` (Expected: `inference`)
- **Agentic:** Got `False` (Expected: `False`)
- **CoT Reasoning:**
  > Step 1: This paper investigates the neural basis of language processing in Deaf signers using EEG and optical flow data. It aims to decode predictive inference during language comprehension by analyzing spatiotemporal coherence between neural signals and visual motion features. Step 2: The paper does *not* describe an autonomous AI agent. It's a neuroscientific study using machine learning for signal analysis and decoding, not building an agent that acts and interacts with an environment. It's about understanding how the brain processes language, not creating an AI. Step 3: The primary focus is on understanding neural dynamics and decoding information from brain signals. While machine learning is used, it's a tool for analysis, not the core subject of the paper. No categories strongly fit the description, as it's primarily a neuroscience/signal processing paper.

#### ⚠️ 2512.21076v1: Blurb-Refined Inference from Crowdsourced Book Reviews using Hierarchi
- **Time:** 34.8s
- **Category:** Got `architecture` (Expected: `inference`)
- **Agentic:** Got `False` (Expected: `False`)
- **Violations:** invented_pattern:architecture/graph_convolution
- **CoT Reasoning:**
  > Step 1: This paper focuses on improving book genre classification by leveraging both user reviews and book blurbs. It proposes a framework called HiGeMine that filters reviews to reduce noise and then uses a graph-based classification method. Step 2: The paper does not describe an autonomous AI agent that acts in a loop. It's a classification method, focusing on model architecture and data processing for improved accuracy. Therefore, it is not agentic. Step 3: The primary category is architecture, specifically graph-based classification. The use of graph convolutions and the two-level graph structure clearly fall into this category. There's also a component of data processing/filtering which could be loosely tied to training, but the core contribution is the model architecture.

#### ⚠️ 2512.20949v1: Neural Probe-Based Hallucination Detection for Large Language Models
- **Time:** 40.6s
- **Category:** Got `agent_evaluation` (Expected: `inference`)
- **Agentic:** Got `False` (Expected: `False`)
- **CoT Reasoning:**
  > Step 1: This paper addresses the problem of hallucination in Large Language Models (LLMs). It proposes a new framework for detecting hallucinated content at the token level, using a neural network-based probe that analyzes the model's hidden states. The goal is to improve upon existing methods that rely on uncertainty estimation or external knowledge retrieval. Step 2: The paper does *not* describe an autonomous AI agent that acts in a loop. It focuses on a detection *method* for LLMs, rather than building an agent itself. It's a technique for evaluating and improving LLM outputs, falling into the evaluation category. Step 3: The primary category is agent_evaluation, specifically capability_measurement. The paper aims to measure the capability of LLMs to avoid hallucination. The use of 'probe methods' and 'hidden-layer states' suggests an analysis of the model's internal workings to assess its performance.

#### ✅ 2512.20578v1: Can LLMs Predict Their Own Failures? Self-Awareness via Internal Circu
- **Time:** 41.8s
- **Category:** Got `inference` (Expected: `inference`)
- **Agentic:** Got `False` (Expected: `False`)
- **CoT Reasoning:**
  > Step 1: This paper introduces Gnosis, a mechanism for LLMs to predict their own failures by analyzing internal states (hidden states and attention patterns) during inference. It aims to achieve self-awareness without relying on external judges or additional compute. Step 2: The paper does *not* describe an autonomous agent acting in a loop. It's a method to improve the reliability of existing LLMs by adding a self-verification component during inference. It's about improving inference, not building an agent. Step 3: The primary category is inference, specifically a method for self-verification. The use of internal states to predict correctness aligns with the idea of observing and interpreting internal signals, which could be considered a form of predictive modeling, but the focus is on improving inference, not building a world model. The method is lightweight and adds parameters to a frozen LLM, so it's not a training method or architectural change in the traditional sense.

#### ✅ 2512.16650v1: Prefix Probing: Lightweight Harmful Content Detection for Large Langua
- **Time:** 42.0s
- **Category:** Got `inference` (Expected: `inference`)
- **Agentic:** Got `False` (Expected: `False`)
- **CoT Reasoning:**
  > Step 1: This paper introduces a method called 'Prefix Probing' for detecting harmful content in large language models. It focuses on improving the trade-off between detection accuracy, latency, and cost during inference. The method works by comparing the log-probabilities of different prefixes to assess harmfulness. Step 2: The paper does *not* describe an autonomous AI agent. It's a technique applied *to* LLMs during inference, not a system where an agent acts and interacts with an environment. It's about improving the inference process itself. Step 3: The primary focus is on improving inference efficiency and safety. The method is about evaluating the model's output during inference to detect harmful content. Therefore, the relevant category is 'inference'. The evidence for this is the entire abstract, which details a method for 'harmful content detection' during 'inference' with a focus on reducing 'inference latency'.

#### ✅ 2512.16855v1: TOGGLE: Temporal Logic-Guided Large Language Model Compression for Edg
- **Time:** 37.2s
- **Category:** Got `inference` (Expected: `inference`)
- **Agentic:** Got `False` (Expected: `False`)
- **CoT Reasoning:**
  > Step 1: This paper addresses the problem of compressing Large Language Models (LLMs) for deployment on edge devices. It proposes a new framework, TOGGLE, that uses Temporal Logic to guide the compression process (quantization and pruning) while preserving linguistic properties. Step 2: The paper does *not* describe an autonomous AI agent that acts in a loop. It focuses on a compression technique applied to a pre-existing model. It's about model optimization, not building an agent. Therefore, is_agentic is false. Step 3: The primary focus is on improving the efficiency of LLMs through compression. The techniques used (quantization, pruning) fall under inference methods. The use of formal specifications (Temporal Logic) to guide the compression process is a novel aspect of the inference technique.

#### ✅ 2512.21336v1: Optimizing Decoding Paths in Masked Diffusion Models by Quantifying Un
- **Time:** 32.5s
- **Category:** Got `inference` (Expected: `inference`)
- **Agentic:** Got `False` (Expected: `False`)
- **CoT Reasoning:**
  > Step 1: This paper addresses the problem of decoding order sensitivity in Masked Diffusion Models (MDMs), which affects the quality of generated outputs. It introduces a metric called 'Denoising Entropy' to quantify uncertainty during the generative process and proposes algorithms to optimize the decoding path based on this metric. Step 2: The paper does *not* describe an autonomous AI agent that acts in a loop. It focuses on improving the decoding process of an existing generative model, which is a refinement of the inference stage. It's about improving the quality of generation, not building an agent. Step 3: The primary focus is on improving the inference process of a diffusion model. The 'Denoising Entropy' metric and the path optimization algorithms fall under the umbrella of efficient inference. There's no training, architecture, or agent-related aspect strong enough to warrant inclusion.

---

### Baseline Category: `multi_agent` (Match: 40.0%)

#### ⚠️ 2512.16856v1: Distributional AGI Safety
- **Time:** 42.8s
- **Category:** Got `agent_safety` (Expected: `multi_agent`)
- **Agentic:** Got `False` (Expected: `True`)
- **CoT Reasoning:**
  > Step 1: This paper is about a shift in perspective on AGI safety, moving away from the idea of a single, monolithic AGI and towards the possibility of AGI emerging from the coordination of multiple, specialized AI agents. It argues that this 'patchwork AGI' scenario is increasingly likely given current trends in AI development (tool use, communication, coordination). Step 2: The paper does *not* describe the building of an autonomous agent that acts in a loop. It's a theoretical discussion about safety considerations given a particular emergence hypothesis. Therefore, it is not agentic. Step 3: The paper discusses agents and their coordination, and tool use. The core argument revolves around safety, so that is also relevant. The mention of 'advanced AI agents with tool-use capabilities' is key.

#### ⚠️ 2512.20996v1: TrafficSimAgent: A Hierarchical Agent Framework for Autonomous Traffic
- **Time:** 35.4s
- **Category:** Got `agent_planning` (Expected: `multi_agent`)
- **Agentic:** Got `True` (Expected: `True`)
- **CoT Reasoning:**
  > Step 1: This paper introduces TrafficSimAgent, a framework that uses an LLM-based agent to simplify traffic simulation experiments. The agent framework is designed to understand instructions, plan experiments, and execute them. It involves collaboration between different expert agents. Step 2: The paper describes an autonomous agent that plans and executes experiments, demonstrating a loop of perception (understanding instructions), decision-making (planning), and action (invoking components). Therefore, it is agentic. Step 3: The primary category is 'agent_planning' as the core contribution is the planning and orchestration of experiments. 'multi_agent' also applies due to the 'cross-level collaboration among expert agents'.

#### ✅ 2512.20991v1: FinAgent: An Agentic AI Framework Integrating Personal Finance and Nut
- **Time:** 47.9s
- **Category:** Got `multi_agent` (Expected: `multi_agent`)
- **Agentic:** Got `True` (Expected: `True`)
- **CoT Reasoning:**
  > Step 1: This paper introduces an AI system designed to manage personal finances and optimize nutrition plans, taking into account fluctuating food prices and household income. It aims to create affordable, nutritionally sufficient meal plans. Step 2: The system is described as 'agentic' and implemented with a 'modular multi-agent architecture' with agents for budgeting, nutrition, price monitoring, and health personalization. These agents share knowledge and interact to achieve the overall goal. This suggests an autonomous system that acts in a loop to adjust to market changes and user needs, making it agentic. Step 3: The primary category is 'multi_agent' due to the explicit mention of a multi-agent architecture. 'agent_planning' also applies because the system creates meal plans, which involves reasoning and acting. 'agent_tool_use' is applicable as the system monitors prices and uses a knowledge base, which can be considered tools. The paper also touches on 'reasoning_acting' within the planning aspect.

#### ✅ 2512.16279v1: QuadSentinel: Sequent Safety for Machine-Checkable Control in Multi-ag
- **Time:** 52.2s
- **Category:** Got `multi_agent` (Expected: `multi_agent`)
- **Agentic:** Got `False` (Expected: `True`)
- **CoT Reasoning:**
  > Step 1: This paper addresses safety concerns in multi-agent systems powered by LLMs, specifically focusing on the difficulty of translating natural language safety policies into machine-checkable rules for reliable runtime enforcement. It proposes QuadSentinel, a four-agent system designed to compile policies into such rules and enforce them. Step 2: The paper describes a system with multiple agents interacting to enforce safety, but it doesn't focus on the agents *learning* to act or solve tasks autonomously. It's more about a runtime safety *system* built around agents, rather than the agents themselves being the primary focus of learning or decision-making. Therefore, it is not strongly agentic. Step 3: The core of the paper is about multi-agent systems and safety. The system described is an evaluation/enforcement mechanism, and the abstract mentions benchmarks used for measurement. The architecture of the four agents is also relevant.

#### ⚠️ 2512.20985v1: A Blockchain-Monitored Agentic AI Architecture for Trusted Perception-
- **Time:** 44.5s
- **Category:** Got `agent_planning` (Expected: `multi_agent`)
- **Agentic:** Got `True` (Expected: `True`)
- **CoT Reasoning:**
  > Step 1: This paper proposes an architecture for agentic AI systems that integrates a blockchain for trust, monitoring, and auditability. It focuses on a perception-reasoning-action cycle within a multi-agent system. Step 2: It *is* agentic because it describes a system where agents perform actions and the blockchain layer provides oversight, suggesting a closed-loop system of perception, reasoning, and action. The agents are described as making autonomous decisions. Step 3: The primary category is 'agent_planning' as the core of the system is about the perception-reasoning-action cycle. 'multi_agent' also applies due to the use of a LangChain-based multi-agent system. 'agent_evaluation' is relevant because the blockchain layer is used for verification and auditability, which are forms of evaluation and safety monitoring.

---

### Baseline Category: `training` (Match: 40.0%)

#### ⚠️ 2512.20796v1: Measuring Mechanistic Independence: Can Bias Be Removed Without Erasin
- **Time:** 38.8s
- **Category:** Got `agent_evaluation` (Expected: `training`)
- **Agentic:** Got `False` (Expected: `False`)
- **CoT Reasoning:**
  > Step 1: This paper investigates the relationship between demographic bias and demographic recognition in language models. It proposes methods to reduce bias without losing the ability to recognize demographics. The core approach involves ablating features using both attribution and correlation-based methods. Step 2: This paper does *not* describe an autonomous AI agent. It focuses on evaluating and mitigating bias in existing language models, which falls under evaluation and potentially training (though it's not a training *method* itself). Step 3: The primary category is agent_evaluation, specifically benchmarking, as the paper introduces a multi-task evaluation setup. The use of sparse autoencoders and feature ablation touches on architecture, but it's not a novel architecture itself, rather an application of one for bias mitigation. The focus on measuring and reducing bias strongly aligns with evaluation.

#### ⚠️ 2512.20569v1: Distilling to Hybrid Attention Models via KL-Guided Layer Selection
- **Time:** 39.8s
- **Category:** Got `inference` (Expected: `training`)
- **Agentic:** Got `False` (Expected: `False`)
- **CoT Reasoning:**
  > Step 1: This paper focuses on improving the inference efficiency of Large Language Models (LLMs) by distilling pretrained Transformer models into hybrid architectures that combine softmax and linear attention layers. The core problem addressed is *layer selection* – determining which layers to convert to linear attention. The method uses layer importance scores and a distillation pipeline (RADLADS). Step 2: The paper does *not* describe an autonomous AI agent that acts in a loop. It's about model architecture and optimization for inference. Therefore, is_agentic is false. Step 3: The primary category is 'inference' as the paper directly addresses improving the efficiency of LLM inference. The 'architecture' category also applies because it discusses hybrid architectures and attention mechanisms. The mention of distillation techniques further supports the 'inference' classification.

#### ✅ 2512.21106v1: Semantic Refinement with LLMs for Graph Representations
- **Time:** 32.9s
- **Category:** Got `training` (Expected: `training`)
- **Agentic:** Got `False` (Expected: `False`)
- **CoT Reasoning:**
  > Step 1: This paper focuses on improving graph representation learning by adaptively refining node semantics based on the specific graph domain. It proposes a data-centric approach (DAS) to address the heterogeneity of structure and semantics in graphs. Step 2: The paper does *not* describe an autonomous AI agent that acts in a loop. It's a method for learning better graph representations, which could be used *by* an agent, but the paper itself doesn't build one. It's about the learning/training process. Step 3: The primary focus is on improving the way graph data is represented, which is a core aspect of machine learning training. There aren't any clear patterns for other categories with high confidence.

#### ⚠️ 2512.21246v1: Learning Factors in AI-Augmented Education: A Comparative Study of Mid
- **Time:** 31.1s
- **Category:** Got `agent_evaluation` (Expected: `training`)
- **Agentic:** Got `False` (Expected: `False`)
- **CoT Reasoning:**
  > Step 1: This paper investigates the impact of AI tools on learning factors (experience, clarity, comfort, motivation) in middle and high school students. It's a comparative study examining how these factors relate to each other within AI-augmented educational settings, and how those relationships differ between age groups. Step 2: The paper does *not* describe an autonomous AI agent acting in a loop. It's an observational study of how students interact with existing AI tools in a classroom setting. Therefore, it is not agentic. Step 3: The paper focuses on the *impact* of AI tools, which could be considered evaluation, but it's not a benchmarking or capability measurement study. It's more broadly about understanding the effects of AI on learning. No other categories strongly apply.

#### ✅ 2512.20794v1: Investigating Model Editing for Unlearning in Large Language Models
- **Time:** 38.0s
- **Category:** Got `training` (Expected: `training`)
- **Agentic:** Got `False` (Expected: `False`)
- **CoT Reasoning:**
  > Step 1: This paper investigates methods for 'unlearning' information in Large Language Models (LLMs). It compares model editing techniques (ROME, IKE, WISE) with traditional unlearning methods, focusing on how effectively they can remove specific information without harming the model's overall performance. Step 2: The paper does *not* describe an autonomous AI agent. It focuses on modifying existing models, not building an agent that acts and interacts with an environment. It's a study of model behavior and training/modification techniques. Therefore, is_agentic is false. Step 3: The primary focus is on techniques to modify existing models, specifically to remove information. This aligns with the 'training' category, as it's a method for refining model behavior. The paper explores different approaches to achieve this, making it relevant to training methods.

#### ⚠️ 2512.21316v1: Scaling Laws for Economic Productivity: Experimental Evidence in LLM-A
- **Time:** 39.5s
- **Category:** Got `agent_evaluation` (Expected: `training`)
- **Agentic:** Got `False` (Expected: `False`)
- **CoT Reasoning:**
  > Step 1: This paper investigates the relationship between LLM training compute and professional productivity across various tasks (consulting, data analysis, management). It presents empirical evidence of productivity gains linked to LLM progress, differentiating between analytical tasks and 'agentic workflows'. Step 2: The paper explicitly contrasts 'non-agentic analytical tasks' with 'agentic workflows'. However, it does *not* describe the building of an autonomous AI agent that acts in a loop. It's an *evaluation* of existing LLMs in professional settings. Therefore, it is not agentic. Step 3: The primary focus is on evaluating the impact of LLMs on productivity, making 'agent_evaluation' the most suitable primary category. The mention of productivity gains and the comparison of different LLMs strongly suggests benchmarking. The distinction between agentic and non-agentic tasks is also relevant, but the paper doesn't *build* an agent, it *evaluates* tasks *with* agents.

#### ✅ 2512.21231v1: MiST: Understanding the Role of Mid-Stage Scientific Training in Devel
- **Time:** 38.1s
- **Category:** Got `training` (Expected: `training`)
- **Agentic:** Got `False` (Expected: `False`)
- **CoT Reasoning:**
  > Step 1: This paper investigates the conditions under which Large Language Models can develop chemical reasoning capabilities using Reinforcement Learning (RL). It identifies 'symbolic competence' and 'latent chemical knowledge' as prerequisites and proposes a 'mid-stage scientific training' (MiST) approach to address these. Step 2: The paper focuses on *training* a model, not building an autonomous agent that acts in a loop. It describes a training methodology (MiST) to improve reasoning, but doesn't involve an agent interacting with an environment. Therefore, it is not agentic. Step 3: The primary focus is on the training methodology. The techniques described (data mixing, continued pre-training, supervised fine-tuning) clearly fall under the 'training' category. The mention of RL-based chemical reasoning also supports this classification.

#### ✅ 2512.16917v1: Generative Adversarial Reasoner: Enhancing LLM Reasoning with Adversar
- **Time:** 42.1s
- **Category:** Got `training` (Expected: `training`)
- **Agentic:** Got `False` (Expected: `False`)
- **CoT Reasoning:**
  > Step 1: This paper introduces a framework called 'Generative Adversarial Reasoner' to improve the reasoning capabilities of LLMs. It uses adversarial reinforcement learning to co-train a reasoner LLM and a discriminator LLM. The discriminator evaluates the reasoning steps, and the reasoner is rewarded for logical consistency and correctness. Step 2: While reinforcement learning is used, it's a training method to improve the reasoning process of an LLM, not a system where an agent autonomously acts and interacts with an environment. It's a co-training setup, but doesn't describe an agent acting in a loop. Therefore, it is not agentic. Step 3: The primary category is 'training' as it focuses on a novel training framework. The 'adversarial reinforcement learning' aspect directly maps to the 'rlhf' or more generally 'reward_modeling' subcategories. The paper also touches on reasoning, which is related to 'agent_planning', specifically 'chain_of_thought', but the training aspect is dominant.

#### ⚠️ 2512.16855v1: TOGGLE: Temporal Logic-Guided Large Language Model Compression for Edg
- **Time:** 37.6s
- **Category:** Got `inference` (Expected: `training`)
- **Agentic:** Got `False` (Expected: `False`)
- **CoT Reasoning:**
  > Step 1: This paper addresses the problem of compressing Large Language Models (LLMs) for deployment on edge devices. It proposes a framework called TOGGLE that uses Temporal Logic to guide the compression process (quantization and pruning) while preserving linguistic properties. Step 2: The paper does *not* describe an autonomous AI agent that acts in a loop. It focuses on a compression technique applied to a pre-trained LLM. It's about model optimization, not building an agent. Therefore, is_agentic is false. Step 3: The primary focus is on improving the *inference* efficiency of LLMs through compression. The use of Bayesian optimization could be considered part of the training process, but the core contribution is about making inference more efficient. The mention of quantization and pruning directly relates to inference techniques.

#### ⚠️ 2512.21311v1: Learning to Solve PDEs on Neural Shape Representations
- **Time:** 32.8s
- **Category:** Got `architecture` (Expected: `training`)
- **Agentic:** Got `False` (Expected: `False`)
- **CoT Reasoning:**
  > Step 1: This paper addresses the problem of solving partial differential equations (PDEs) on 3D shapes represented as neural fields. It proposes a mesh-free method to directly solve PDEs within the neural representation, avoiding the need for mesh extraction or per-instance training. Step 2: The paper does *not* describe an autonomous AI agent. It focuses on a novel method for solving PDEs, which is a mathematical/computational task, and doesn't involve an agent acting in an environment. It's a technique for improving the efficiency and generality of PDE solvers. Step 3: The primary focus is on a novel method/architecture for solving PDEs on neural representations. There isn't a strong fit for any other category. The method learns an operator, which could be considered a learned function, but it's not a full agent.

---

### Baseline Category: `world_models` (Match: 0.0%)

#### ⚠️ 2512.21005v1: Learning from Neighbors with PHIBP: Predicting Infectious Disease Dyna
- **Time:** 28.7s
- **Category:** Got `None` (Expected: `world_models`)
- **Agentic:** Got `False` (Expected: `False`)
- **CoT Reasoning:**
  > Step 1: This paper focuses on a statistical method (Poisson Hierarchical Indian Buffet Process - PHIBP) for modeling sparse count data, specifically in the context of predicting infectious disease outbreaks in regions with limited historical data. It's about improving prediction accuracy when data is scarce by borrowing statistical strength from related regions. Step 2: The paper does *not* describe an autonomous AI agent. It presents a statistical model, not a system that acts and interacts with an environment. It's a modeling technique, not an agent. Step 3: The paper's core contribution is a novel modeling approach. Therefore, it doesn't fit neatly into any of the agent-related categories. It's a statistical method for prediction, but doesn't involve training, inference, or architecture in the AI/ML sense defined by the taxonomy. Thus, the patterns list will be empty.

#### ⚠️ 2512.21335v1: Autonomous Uncertainty Quantification for Computational Point-of-care 
- **Time:** 36.5s
- **Category:** Got `agent_evaluation` (Expected: `world_models`)
- **Agentic:** Got `False` (Expected: `True`)
- **CoT Reasoning:**
  > Step 1: This paper focuses on uncertainty quantification in neural network-based diagnostic models used in computational point-of-care sensors. It aims to address the risk of misdiagnosis caused by 'hallucinations' in these models. The technique is described as 'autonomous', but the abstract doesn't detail an agent acting in a loop. It's about improving the reliability of a diagnostic *system*, not building an agent. Step 2: It is not agentic because the paper describes a technique to improve the predictions of a diagnostic model, rather than an AI agent that autonomously decides and acts. It's a method for improving model reliability, not an agent acting in an environment. Step 3: The primary category is agent_evaluation, specifically capability_measurement, as the paper is focused on assessing and improving the reliability (and thus capability) of a diagnostic model. There isn't enough information to confidently assign other categories.

#### ⚠️ 2512.20387v1: Generative Digital Twins: Vision-Language Simulation Models for Execut
- **Time:** 47.8s
- **Category:** Got `agent_evaluation` (Expected: `world_models`)
- **Agentic:** Got `False` (Expected: `False`)
- **CoT Reasoning:**
  > Step 1: This paper introduces a Vision-Language Simulation Model (VLSM) that generates executable code (FlexScript) from sketches and natural language prompts for industrial simulation. It also creates a dataset and evaluation metrics for this task. Step 2: The system doesn't appear to be an autonomous agent acting in a loop. It's a model that *generates* code, but doesn't *execute* it autonomously or interact with an environment in a closed loop. It's more about model capabilities and evaluation. Therefore, it is not agentic. Step 3: The primary category is agent_evaluation, as the paper focuses on novel evaluation metrics. The dataset creation and model itself also relate to training, and the model's ability to reason across modalities is relevant to agent_planning.

#### ⚠️ 2512.16701v1: Cyber Humanism in Education: Reclaiming Agency through AI and Learning
- **Time:** 40.7s
- **Category:** Got `agent_planning` (Expected: `world_models`)
- **Agentic:** Got `False` (Expected: `False`)
- **CoT Reasoning:**
  > Step 1: This paper discusses the impact of generative AI on education, focusing on the potential for 'epistemic automation' and the need to reclaim human agency. It proposes a framework called 'Cyber Humanism in Education' to address these concerns. The core argument revolves around positioning educators and learners as 'epistemic agents' within AI-enabled learning environments. Step 2: The paper does *not* describe the building of an autonomous AI agent that acts in a loop. It's a conceptual paper about the socio-technical implications of AI in education, and how to maintain human agency. Therefore, it is not agentic. Step 3: The paper explicitly discusses 'agency' and positions humans as 'epistemic agents' within a system. This aligns with the 'agent_planning' category, specifically 'reasoning_acting' as it relates to how humans interact with and shape AI systems. The concept of 'algorithmic citizens' also suggests a focus on understanding and influencing the behavior of these systems, further supporting 'reasoning_acting'.

#### ⚠️ 2512.21029v1: Critical Points of Degenerate Metrics on Algebraic Varieties: A Tale o
- **Time:** 25.2s
- **Category:** Got `None` (Expected: `world_models`)
- **Agentic:** Got `False` (Expected: `False`)
- **CoT Reasoning:**
  > Step 1: This paper investigates the critical points of optimization problems in algebraic geometry, specifically when dealing with overparameterized models (small datasets relative to model size). It connects algebraic geometry with machine learning, focusing on the properties of degenerate optimization landscapes. Step 2: The paper does *not* describe an autonomous AI agent. It's a theoretical analysis of optimization landscapes, not a system that acts and interacts with an environment. It's fundamentally about mathematical properties, not building an agent. Step 3: The paper touches upon concepts relevant to machine learning, specifically overparametrization, but it doesn't fit neatly into any of the agent-focused categories. It's most closely related to the underlying mathematical foundations of machine learning, but none of the categories directly apply with high confidence. Therefore, the patterns list will be empty.

#### ⚠️ 2512.21201v1: Schrödinger's Navigator: Imagining an Ensemble of Futures for Zero-Sho
- **Time:** 35.9s
- **Category:** Got `agent_planning` (Expected: `world_models`)
- **Agentic:** Got `False` (Expected: `False`)
- **CoT Reasoning:**
  > Step 1: This paper presents a novel navigation framework called 'Schrödinger's Navigator' for zero-shot object navigation. It aims to improve robustness in cluttered and dynamic environments by imagining multiple possible futures before taking action. The core idea is to use a 3D world model to predict future observations along different candidate trajectories. Step 2: The paper describes a navigation *framework*, but it doesn't detail a complete autonomous agent acting in a continuous loop with perception, decision-making, and action. It focuses on the reasoning and planning component (imagining futures) rather than the full agent implementation. Therefore, it is not strongly agentic. Step 3: The most relevant categories are agent_planning (specifically reasoning_acting and potentially goal_decomposition if the trajectories represent subgoals) and world_models (learned_dynamics and predictive_modeling, as it uses a 3D world model to predict future observations).

#### ⚠️ 2512.21113v1: A Mechanistic Analysis of Transformers for Dynamical Systems
- **Time:** 46.3s
- **Category:** Got `architecture` (Expected: `world_models`)
- **Agentic:** Got `False` (Expected: `False`)
- **CoT Reasoning:**
  > Step 1: This paper analyzes the internal workings of Transformers when applied to time-series data (dynamical systems). It's focused on understanding *how* Transformers represent and process this data, not on building a new forecasting model or an agent. Step 2: It is not agentic because the paper does not describe an autonomous agent that acts in a loop. It's a mechanistic analysis of an existing architecture. Step 3: The primary category is 'architecture' as it investigates the representational capabilities of Transformers. The mention of dynamical systems and how Transformers handle time-series data also aligns with 'world_models', specifically 'predictive_modeling', though the focus is more on the internal representation than building a predictive model itself. The paper explicitly contrasts Transformers with 'state_space_models', indicating a connection to that area, but it doesn't propose a new state space model.

#### ⚠️ 2512.16707v1: Dual Computational Horizons: Incompleteness and Unpredictability in In
- **Time:** 34.8s
- **Category:** Got `agent_planning` (Expected: `world_models`)
- **Agentic:** Got `False` (Expected: `False`)
- **CoT Reasoning:**
  > Step 1: This paper is about fundamental limitations of intelligent systems, specifically concerning reasoning and prediction. It formalizes concepts of incompleteness and unpredictability and their impact on an agent's ability to understand its own predictive limits. Step 2: It is not agentic. The paper discusses theoretical limitations applicable to *any* intelligent system, not a specific agent that acts and interacts with an environment. It doesn't describe building or training an agent. Step 3: The matching categories are primarily related to agent planning and reasoning, as it discusses the limits of reasoning and prediction. It also touches upon world models, as prediction is a core component of building world models.

#### ⚠️ 2512.16733v1: Discovering and Learning Probabilistic Models of Black-Box AI Capabili
- **Time:** 53.1s
- **Category:** Got `agent_planning` (Expected: `world_models`)
- **Agentic:** Got `False` (Expected: `False`)
- **CoT Reasoning:**
  > Step 1: This paper focuses on modeling the capabilities of existing 'black-box AI' systems (like foundational models) used for decision-making. It aims to create interpretable models of these systems' planning abilities using PDDL and Monte Carlo Tree Search. The goal is to understand *what* the black-box AI can do, under what conditions, and with what probabilities. Step 2: The paper does *not* describe the creation of a new autonomous agent. It's about *analyzing* and *modeling* the behavior of pre-existing AI systems. It uses Monte Carlo Tree Search as a method for data acquisition to build a model, but it's not an agent acting in a loop. Therefore, it is not agentic. Step 3: The primary category is 'agent_planning' because the core contribution is about modeling and understanding the planning capabilities of a black-box AI. The use of Monte Carlo Tree Search to discover these capabilities further supports this classification. The paper also touches on 'agent_evaluation' as it aims to provide a 'sound and interpretable representation' of the BBAI's capabilities, which is a form of capability measurement.

---

