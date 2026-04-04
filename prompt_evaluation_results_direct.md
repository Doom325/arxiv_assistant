# Prompt Evaluation Results

**Model:** gemma3:27b  
**Prompt Pattern Version:** v6_direct  
**Date:** 2026-04-03 22:32  
**Papers tested:** 71 of 71  

## Overview Metrics

| Metric | Result |
|---|---|
| Average Time/Paper | 15.2s |
| Total Taxonomy Violations | 4 |
| Parse / Network Errors | 0 |
| `primary_category` Match Rate vs Baseline | 50.7% |
| `is_agentic` Match Rate vs Baseline | 84.5% |

## Detailed Results

### Baseline Category: `agent_evaluation` (Match: 60.0%)

#### ✅ 2512.20948v1: Foundation Model-based Evaluation of Neuropsychiatric Disorders: A Lif
- **Time:** 26.4s
- **Category:** Got `agent_evaluation` (Expected: `agent_evaluation`)
- **Agentic:** Got `False` (Expected: `False`)

#### ✅ 2512.21329v1: Your Reasoning Benchmark May Not Test Reasoning: Revealing Perception 
- **Time:** 17.3s
- **Category:** Got `agent_evaluation` (Expected: `agent_evaluation`)
- **Agentic:** Got `False` (Expected: `False`)

#### ✅ 2512.21227v1: PhononBench:A Large-Scale Phonon-Based Benchmark for Dynamical Stabili
- **Time:** 15.9s
- **Category:** Got `agent_evaluation` (Expected: `agent_evaluation`)
- **Agentic:** Got `False` (Expected: `False`)

#### ✅ 2512.21010v1: LLM Swiss Round: Aggregating Multi-Benchmark Performance via Competiti
- **Time:** 15.7s
- **Category:** Got `agent_evaluation` (Expected: `agent_evaluation`)
- **Agentic:** Got `False` (Expected: `False`)

#### ✅ 2512.21326v1: Measuring all the noises of LLM Evals
- **Time:** 16.4s
- **Category:** Got `agent_evaluation` (Expected: `agent_evaluation`)
- **Agentic:** Got `False` (Expected: `False`)

#### ⚠️ 2512.16873v1: The Social Responsibility Stack: A Control-Theoretic Architecture for 
- **Time:** 13.4s
- **Category:** Got `architecture` (Expected: `agent_evaluation`)
- **Agentic:** Got `False` (Expected: `False`)

#### ⚠️ 2512.16707v1: Dual Computational Horizons: Incompleteness and Unpredictability in In
- **Time:** 10.7s
- **Category:** Got `agent_planning` (Expected: `agent_evaluation`)
- **Agentic:** Got `False` (Expected: `False`)

#### ✅ 2512.21110v1: Beyond Context: Large Language Models Failure to Grasp Users Intent
- **Time:** 10.7s
- **Category:** Got `agent_evaluation` (Expected: `agent_evaluation`)
- **Agentic:** Got `False` (Expected: `False`)

#### ⚠️ 2512.16553v1: Needle in the Web: A Benchmark for Retrieving Targeted Web Pages in th
- **Time:** 20.9s
- **Category:** Got `agent_tool_use` (Expected: `agent_evaluation`)
- **Agentic:** Got `True` (Expected: `False`)

#### ⚠️ 2512.16698v1: Do Multi-Agents Solve Better Than Single? Evaluating Agentic Framework
- **Time:** 19.9s
- **Category:** Got `multi_agent` (Expected: `agent_evaluation`)
- **Agentic:** Got `True` (Expected: `False`)

---

### Baseline Category: `agent_memory` (Match: 0.0%)

#### ⚠️ 2512.20985v1: A Blockchain-Monitored Agentic AI Architecture for Trusted Perception-
- **Time:** 20.2s
- **Category:** Got `agent_planning` (Expected: `agent_memory`)
- **Agentic:** Got `True` (Expected: `True`)

#### ⚠️ 2512.21039v1: Agentic Multi-Persona Framework for Evidence-Aware Fake News Detection
- **Time:** 14.9s
- **Category:** Got `agent_planning` (Expected: `agent_memory`)
- **Agentic:** Got `True` (Expected: `True`)

#### ⚠️ 2512.20991v1: FinAgent: An Agentic AI Framework Integrating Personal Finance and Nut
- **Time:** 17.3s
- **Category:** Got `agent_planning` (Expected: `agent_memory`)
- **Agentic:** Got `True` (Expected: `True`)

#### ⚠️ 2512.20959v1: Can Agentic AI Match the Performance of Human Data Scientists?
- **Time:** 16.3s
- **Category:** Got `agent_evaluation` (Expected: `agent_memory`)
- **Agentic:** Got `True` (Expected: `True`)

#### ⚠️ 2512.20848v1: Nemotron 3 Nano: Open, Efficient Mixture-of-Experts Hybrid Mamba-Trans
- **Time:** 27.8s
- **Category:** Got `architecture` (Expected: `agent_memory`)
- **Agentic:** Got `True` (Expected: `True`)

#### ⚠️ 2512.20491v2: Step-DeepResearch Technical Report
- **Time:** 24.6s
- **Category:** Got `agent_planning` (Expected: `agent_memory`)
- **Agentic:** Got `True` (Expected: `True`)

#### ⚠️ 2512.16171v1: Science Consultant Agent
- **Time:** 11.3s
- **Category:** Got `agent_tool_use` (Expected: `agent_memory`)
- **Agentic:** Got `True` (Expected: `False`)

#### ⚠️ 2512.21220v1: RoboSafe: Safeguarding Embodied Agents via Executable Safety Logic
- **Time:** 14.7s
- **Category:** Got `agent_planning` (Expected: `agent_memory`)
- **Agentic:** Got `True` (Expected: `False`)

---

### Baseline Category: `agent_planning` (Match: 100.0%)

#### ✅ 2512.16301v1: Adaptation of Agentic AI
- **Time:** 14.1s
- **Category:** Got `agent_planning` (Expected: `agent_planning`)
- **Agentic:** Got `True` (Expected: `False`)

#### ✅ 2512.21243v1: LookPlanGraph: Embodied Instruction Following Method with VLM Graph Au
- **Time:** 10.1s
- **Category:** Got `agent_planning` (Expected: `agent_planning`)
- **Agentic:** Got `True` (Expected: `False`)

#### ✅ 2512.20586v1: Automated stereotactic radiosurgery planning using a human-in-the-loop
- **Time:** 15.7s
- **Category:** Got `agent_planning` (Expected: `agent_planning`)
- **Agentic:** Got `True` (Expected: `True`)

#### ✅ 2512.21066v1: Agentic Explainable Artificial Intelligence (Agentic XAI) Approach To 
- **Time:** 16.4s
- **Category:** Got `agent_planning` (Expected: `agent_planning`)
- **Agentic:** Got `True` (Expected: `True`)

---

### Baseline Category: `agent_tool_use` (Match: 71.4%)

#### ✅ 2512.16171v1: Science Consultant Agent
- **Time:** 11.3s
- **Category:** Got `agent_tool_use` (Expected: `agent_tool_use`)
- **Agentic:** Got `True` (Expected: `False`)

#### ⚠️ 2512.20996v1: TrafficSimAgent: A Hierarchical Agent Framework for Autonomous Traffic
- **Time:** 13.7s
- **Category:** Got `multi_agent` (Expected: `agent_tool_use`)
- **Agentic:** Got `True` (Expected: `True`)

#### ✅ 2512.20745v1: AgentMath: Empowering Mathematical Reasoning for Large Language Models
- **Time:** 20.3s
- **Category:** Got `agent_tool_use` (Expected: `agent_tool_use`)
- **Agentic:** Got `True` (Expected: `True`)

#### ✅ 2512.20745v1: AgentMath: Empowering Mathematical Reasoning for Large Language Models
- **Time:** 19.1s
- **Category:** Got `agent_tool_use` (Expected: `agent_tool_use`)
- **Agentic:** Got `True` (Expected: `True`)

#### ✅ 2512.20957v1: One Tool Is Enough: Reinforcement Learning for Repository-Level LLM Ag
- **Time:** 15.1s
- **Category:** Got `agent_tool_use` (Expected: `agent_tool_use`)
- **Agentic:** Got `True` (Expected: `True`)

#### ⚠️ 2512.16301v1: Adaptation of Agentic AI
- **Time:** 14.0s
- **Category:** Got `agent_planning` (Expected: `agent_tool_use`)
- **Agentic:** Got `True` (Expected: `False`)

#### ✅ 2512.20856v1: NVIDIA Nemotron 3: Efficient and Open Intelligence
- **Time:** 24.3s
- **Category:** Got `agent_tool_use` (Expected: `agent_tool_use`)
- **Agentic:** Got `True` (Expected: `True`)
- **Violations:** invented_pattern:agent_tool_use/multi-step tool use

---

### Baseline Category: `architecture` (Match: 50.0%)

#### ⚠️ 2512.20612v1: Making Large Language Models Efficient Dense Retrievers
- **Time:** 14.9s
- **Category:** Got `inference` (Expected: `architecture`)
- **Agentic:** Got `False` (Expected: `False`)

#### ✅ 2512.16919v1: DVGT: Driving Visual Geometry Transformer
- **Time:** 14.8s
- **Category:** Got `architecture` (Expected: `architecture`)
- **Agentic:** Got `False` (Expected: `False`)

#### ✅ 2512.20968v1: Mesh-Attention: A New Communication-Efficient Distributed Attention wi
- **Time:** 18.2s
- **Category:** Got `architecture` (Expected: `architecture`)
- **Agentic:** Got `False` (Expected: `False`)

#### ✅ 2512.16873v1: The Social Responsibility Stack: A Control-Theoretic Architecture for 
- **Time:** 13.4s
- **Category:** Got `architecture` (Expected: `architecture`)
- **Agentic:** Got `False` (Expected: `False`)

#### ⚠️ 2512.21301v1: Transcriptome-Conditioned Personalized De Novo Drug Generation for AML
- **Time:** 4.4s
- **Category:** Got `None` (Expected: `architecture`)
- **Agentic:** Got `False` (Expected: `False`)

#### ⚠️ 2512.21102v1: Shared Representation Learning for High-Dimensional Multi-Task Forecas
- **Time:** 15.0s
- **Category:** Got `world_models` (Expected: `architecture`)
- **Agentic:** Got `False` (Expected: `False`)

#### ✅ 2512.16676v1: DataFlow: An LLM-Driven Framework for Unified Data Preparation and Wor
- **Time:** 16.1s
- **Category:** Got `architecture` (Expected: `architecture`)
- **Agentic:** Got `False` (Expected: `False`)

#### ⚠️ 2512.21024v1: Policy-Conditioned Policies for Multi-Agent Task Solving
- **Time:** 10.3s
- **Category:** Got `multi_agent` (Expected: `architecture`)
- **Agentic:** Got `True` (Expected: `False`)

#### ⚠️ 2512.21054v1: DexAvatar: 3D Sign Language Reconstruction with Hand and Body Pose Pri
- **Time:** 13.1s
- **Category:** Got `world_models` (Expected: `architecture`)
- **Agentic:** Got `False` (Expected: `False`)

#### ✅ 2512.21332v1: C2LLM Technical Report: A New Frontier in Code Retrieval via Adaptive 
- **Time:** 14.9s
- **Category:** Got `architecture` (Expected: `architecture`)
- **Agentic:** Got `False` (Expected: `False`)

---

### Baseline Category: `inference` (Match: 75.0%)

#### ✅ 2512.20578v1: Can LLMs Predict Their Own Failures? Self-Awareness via Internal Circu
- **Time:** 13.8s
- **Category:** Got `inference` (Expected: `inference`)
- **Agentic:** Got `False` (Expected: `False`)

#### ✅ 2512.16650v1: Prefix Probing: Lightweight Harmful Content Detection for Large Langua
- **Time:** 15.4s
- **Category:** Got `inference` (Expected: `inference`)
- **Agentic:** Got `False` (Expected: `False`)

#### ✅ 2512.16855v1: TOGGLE: Temporal Logic-Guided Large Language Model Compression for Edg
- **Time:** 12.5s
- **Category:** Got `inference` (Expected: `inference`)
- **Agentic:** Got `False` (Expected: `False`)

#### ⚠️ 2512.20929v1: Decoding Predictive Inference in Visual Language Processing via Spatio
- **Time:** 8.9s
- **Category:** Got `world_models` (Expected: `inference`)
- **Agentic:** Got `False` (Expected: `False`)

#### ✅ 2512.21336v1: Optimizing Decoding Paths in Masked Diffusion Models by Quantifying Un
- **Time:** 12.2s
- **Category:** Got `inference` (Expected: `inference`)
- **Agentic:** Got `False` (Expected: `False`)

#### ✅ 2512.20949v1: Neural Probe-Based Hallucination Detection for Large Language Models
- **Time:** 8.8s
- **Category:** Got `inference` (Expected: `inference`)
- **Agentic:** Got `False` (Expected: `False`)

#### ✅ 2512.21323v1: Parallel Token Prediction for Language Models
- **Time:** 17.5s
- **Category:** Got `inference` (Expected: `inference`)
- **Agentic:** Got `False` (Expected: `False`)
- **Violations:** invented_pattern:training/distillation

#### ⚠️ 2512.21076v1: Blurb-Refined Inference from Crowdsourced Book Reviews using Hierarchi
- **Time:** 12.5s
- **Category:** Got `architecture` (Expected: `inference`)
- **Agentic:** Got `False` (Expected: `False`)
- **Violations:** invented_pattern:architecture/graph_convolutions

---

### Baseline Category: `multi_agent` (Match: 80.0%)

#### ⚠️ 2512.20985v1: A Blockchain-Monitored Agentic AI Architecture for Trusted Perception-
- **Time:** 20.4s
- **Category:** Got `agent_planning` (Expected: `multi_agent`)
- **Agentic:** Got `True` (Expected: `True`)

#### ✅ 2512.20996v1: TrafficSimAgent: A Hierarchical Agent Framework for Autonomous Traffic
- **Time:** 13.9s
- **Category:** Got `multi_agent` (Expected: `multi_agent`)
- **Agentic:** Got `True` (Expected: `True`)

#### ✅ 2512.20991v1: FinAgent: An Agentic AI Framework Integrating Personal Finance and Nut
- **Time:** 11.2s
- **Category:** Got `multi_agent` (Expected: `multi_agent`)
- **Agentic:** Got `True` (Expected: `True`)

#### ✅ 2512.16279v1: QuadSentinel: Sequent Safety for Machine-Checkable Control in Multi-ag
- **Time:** 17.7s
- **Category:** Got `multi_agent` (Expected: `multi_agent`)
- **Agentic:** Got `True` (Expected: `True`)

#### ✅ 2512.16856v1: Distributional AGI Safety
- **Time:** 14.9s
- **Category:** Got `multi_agent` (Expected: `multi_agent`)
- **Agentic:** Got `True` (Expected: `True`)

---

### Baseline Category: `training` (Match: 40.0%)

#### ✅ 2512.20908v1: Where Did This Sentence Come From? Tracing Provenance in LLM Reasoning
- **Time:** 13.5s
- **Category:** Got `training` (Expected: `training`)
- **Agentic:** Got `False` (Expected: `False`)

#### ✅ 2512.21107v1: Semi-Supervised Learning for Large Language Models Safety and Content 
- **Time:** 13.5s
- **Category:** Got `training` (Expected: `training`)
- **Agentic:** Got `False` (Expected: `False`)

#### ✅ 2512.21288v1: Model Merging via Multi-Teacher Knowledge Distillation
- **Time:** 12.6s
- **Category:** Got `training` (Expected: `training`)
- **Agentic:** Got `False` (Expected: `False`)
- **Violations:** invented_pattern:training/distillation

#### ⚠️ 2512.21021v1: Towards Better Search with Domain-Aware Text Embeddings for C2C Market
- **Time:** 14.1s
- **Category:** Got `inference` (Expected: `training`)
- **Agentic:** Got `False` (Expected: `False`)

#### ⚠️ 2512.21075v1: Understanding Scaling Laws in Deep Neural Networks via Feature Learnin
- **Time:** 17.1s
- **Category:** Got `architecture` (Expected: `training`)
- **Agentic:** Got `False` (Expected: `False`)

#### ⚠️ 2512.21311v1: Learning to Solve PDEs on Neural Shape Representations
- **Time:** 12.6s
- **Category:** Got `architecture` (Expected: `training`)
- **Agentic:** Got `False` (Expected: `False`)

#### ⚠️ 2512.21316v1: Scaling Laws for Economic Productivity: Experimental Evidence in LLM-A
- **Time:** 16.9s
- **Category:** Got `agent_evaluation` (Expected: `training`)
- **Agentic:** Got `False` (Expected: `False`)

#### ⚠️ 2512.16656v1: Comprehensive AI Literacy: The Case for Centering Human Agency
- **Time:** 16.5s
- **Category:** Got `agent_evaluation` (Expected: `training`)
- **Agentic:** Got `False` (Expected: `False`)

#### ✅ 2512.21152v1: MODE: Multi-Objective Adaptive Coreset Selection
- **Time:** 13.6s
- **Category:** Got `training` (Expected: `training`)
- **Agentic:** Got `False` (Expected: `False`)

#### ⚠️ 2512.21020v1: Enhancing diffusion models with Gaussianization preprocessing
- **Time:** 13.7s
- **Category:** Got `architecture` (Expected: `training`)
- **Agentic:** Got `False` (Expected: `False`)

---

### Baseline Category: `world_models` (Match: 22.2%)

#### ⚠️ 2512.16733v1: Discovering and Learning Probabilistic Models of Black-Box AI Capabili
- **Time:** 11.8s
- **Category:** Got `agent_planning` (Expected: `world_models`)
- **Agentic:** Got `False` (Expected: `False`)

#### ⚠️ 2512.16701v1: Cyber Humanism in Education: Reclaiming Agency through AI and Learning
- **Time:** 17.8s
- **Category:** Got `agent_planning` (Expected: `world_models`)
- **Agentic:** Got `False` (Expected: `False`)

#### ⚠️ 2512.21201v1: Schrödinger's Navigator: Imagining an Ensemble of Futures for Zero-Sho
- **Time:** 14.8s
- **Category:** Got `agent_planning` (Expected: `world_models`)
- **Agentic:** Got `True` (Expected: `False`)

#### ⚠️ 2512.21113v1: A Mechanistic Analysis of Transformers for Dynamical Systems
- **Time:** 13.4s
- **Category:** Got `architecture` (Expected: `world_models`)
- **Agentic:** Got `False` (Expected: `False`)

#### ✅ 2512.21005v1: Learning from Neighbors with PHIBP: Predicting Infectious Disease Dyna
- **Time:** 13.8s
- **Category:** Got `world_models` (Expected: `world_models`)
- **Agentic:** Got `False` (Expected: `False`)

#### ⚠️ 2512.21335v1: Autonomous Uncertainty Quantification for Computational Point-of-care 
- **Time:** 14.3s
- **Category:** Got `agent_evaluation` (Expected: `world_models`)
- **Agentic:** Got `False` (Expected: `True`)

#### ✅ 2512.20387v1: Generative Digital Twins: Vision-Language Simulation Models for Execut
- **Time:** 17.8s
- **Category:** Got `world_models` (Expected: `world_models`)
- **Agentic:** Got `False` (Expected: `False`)

#### ⚠️ 2512.21029v1: Critical Points of Degenerate Metrics on Algebraic Varieties: A Tale o
- **Time:** 11.3s
- **Category:** Got `training` (Expected: `world_models`)
- **Agentic:** Got `False` (Expected: `False`)

#### ⚠️ 2512.16707v1: Dual Computational Horizons: Incompleteness and Unpredictability in In
- **Time:** 13.3s
- **Category:** Got `agent_planning` (Expected: `world_models`)
- **Agentic:** Got `False` (Expected: `False`)

---

