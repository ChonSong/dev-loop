# Competitive Landscape: Autonomous Coding & Multi-Agent Systems

Capability-oriented comparison of external repos vs. our Coach/Player loop.
Focus on what each system does that ours doesn't — not token efficiency or speed.

## 1. Constrained Agent-Computer Interface

### SWE-agent / mini-SWE-agent
- **What they do differently:** Constrained action space — agent can only `bash`, `edit`, `submit`. No web browsing, no arbitrary Python, no tool drift.
- **mini-SWE-agent**: 100 lines of Python, 65% on SWE-bench Verified. The constraint IS the feature — fewer failure modes, more predictable output.
- **Relevance to Coach:** When reviewing Player output, consider whether the task would have been better served by a constrained toolset. "Could this bug have been prevented by the Player not having browser access during an API-only task?"

### OpenHands (All-Hands-AI/OpenHands)
- **What it does differently:** Control plane for heterogeneous coding agents — runs Claude Code, Codex, Gemini, or any ACP-compatible agent under one orchestrator with sandboxing and state management.
- **Relevance to Coach:** We already have OpenCode, Claude Code, Codex CLI skills. OpenHands validates the "orchestrator-of-heterogeneous-agents" pattern but at platform level with sandbox isolation. If we add ACP agent support to the Player, OpenHands is the reference architecture for agent-agnostic state management.

### Claude Code (anthropics/claude-code)
- **What it does differently:** 87.6% SWE-bench Verified — best single-agent coding tool. Plugin architecture for custom extensions. Terminal-native.
- **Relevance to Coach:** When a Player task is struggling, the reference metric is ~88% on real GitHub issues. Our Player should never fall below ~50% of what Claude Code achieves on analogous tasks. The plugin architecture is also a pattern for extending Coach's review capabilities.

## 2. Structured Multi-Agent Collaboration

### MetaGPT (FoundationAgents/MetaGPT)
- **What it does differently:** Software company simulation — PM writes PRD, Architect writes design docs, Engineers implement, QA tests. Communication via **structured artifacts** (formal documents), not free-form chat.
- **Key insight:** Artifact formats are the contract between agents. Our Coach/Player loop uses AGENTS.md + .checkpoint.json as shared artifacts. MetaGPT suggests extending this: if the Player produced a structured implementation summary and the Coach consumed it as a structured review form, the loop becomes more deterministic. The artifact IS the message.
- **Relevance to Coach:** Could Coach issue a structured review template (checklist with YAGNI/Security/Perf/Correctness sections) that the Player fills before submitting? This inverts the review loop and catches design errors earlier.

### CrewAI (crewAIInc/crewAI)
- **What it does differently:** Role-based agents with three orchestration modes: sequential, hierarchical, and **Flows** (event-driven state machines). Built-in memory, knowledge sharing, guardrails.
- **Key capability:** Flows architecture — granular event-driven orchestration with explicit states and transitions.
- **Relevance to Coach:** Our Coach/Player loop is a 2-agent fixed sequential pattern. CrewAI's Flows suggest a state machine: `investigating → implementing → testing → committing → awaiting_review → reviewing → approved/reverted`. Each state has explicit entry criteria, transition guards, and error recovery hooks. Our binary checkpoint format doesn't capture this — a CrewAI-style state machine would give better error recovery on stuck tasks.

### AutoGen (microsoft/autogen)
- **What it does differently:** Event-driven multi-agent conversations with flexible speaker selection (round-robin, LLM-driven, rule-based). Supports distributed agents across machines/languages.
- **Key capability:** Dynamic group chat — agents don't have fixed roles; the conversation graph is determined at runtime.
- **Relevance to Coach:** Could let us insert specialized agents on demand (Frontend Specialist, API Specialist, Security Reviewer) rather than having our 2 fixed agents do everything. The group-chat pattern allows self-organization instead of hard-coded delegation.

## 3. Self-Improvement & Cross-Session Learning

### Voyager (MineDojo/Voyager)
- **What it does differently:** Lifelong learning via **skill library** — agent writes Python skills, stores them in vector DB, retrieves relevant ones for new tasks. Loop: propose → attempt → if success, save as skill → if failure, reflect and retry.
- **Key insight:** Skills are **self-generated** from successful work, not human-written.
- **Relevance to Coach:** Our skill_manage() supports creating skills, but creation is human-directed. If Coach could distill successful Player patches into reusable skills automatically (detect: "the Player fixed this pattern 3 times → this should be a skill"), the system accelerates over time without human intervention.

### Reflexion (noahshinn/reflexion)
- **What it does differently:** Verbal self-reflection + episodic memory. After failing, agent writes natural-language reflection ("I failed because X, next time I should Y"). Stored with retrieval cues — injected on similar future tasks. No gradient updates.
- **Key capability:** Learning from failure without gradient updates — purely in-context learning from past mistakes.
- **Relevance to Coach:** Coach's `coach_review.notes` in .checkpoint.json is a primitive version. Formalizing this: (1) detect failure/regression → (2) write structured reflection → (3) store with retrieval cues → (4) inject into Coach context on similar tasks. This would prevent the Coach from rubber-stamping the same regression twice.

## 4. Code-First Task Decomposition

### TaskWeaver (microsoft/TaskWeaver)
- **What it does differently:** Plans are **executable code, not text**. The planner generates a Python function that orchestrates plugin calls. Plans are debuggable, testable, reusable.
- **Relevance to Coach:** Player's "mini-plan" is currently text. TaskWeaver writes it as code with assertions. If Player's plan were a Python skeleton, Coach could **run the plan** to verify it before implementation starts. Catches design errors at plan time instead of after 3 ticks of coding.

## 5. Multi-Agent Reasoning (Latent-Space)

### RecursiveMAS (RecursiveMAS/RecursiveMAS)
- **What it does differently:** Agents communicate via **RecursiveLink modules** on hidden states, not text. The entire MAS is a unified recursive computation with gradient-based credit assignment across rounds. Requires fine-tuned models (15+ HF checkpoints).
- **Relevance to Coach:** This is a fundamentally different paradigm — agents as a differentiable computation rather than separate LLM processes. Not directly applicable to our text-based loop, but the **latent-state handoff** concept could inspire a compressed representation for Coach↔Player handoffs (instead of dumping full diffs).

## 6. Multi-Modal & GUI Agents

### GUIRepair (SWE-bench Multimodal leaderboard)
- **What it does differently:** Achieves 35.98% on SWE-bench Multimodal by incorporating screenshots into the repair loop — agent sees UI bugs and fixes them visually.
- **Relevance to Coach:** Validates Coach's visual-comparison-first approach. The SWE-bench Multimodal benchmark is the ground truth for how well vision-based review works. Our Coach's `browser_vision` QA is doing the same thing conceptually.

## Current SWE-bench Verified Landscape (as of mid-2026)

Top scores on SWE-bench Verified (500 human-validated issues):
- Claude Code (Opus 4.7): 87.6%
- GPT-5.2 Codex: 72.8%
- mini-SWE-agent + GPT-5: 65%
- SWE-agent + various: 40-60%
- OpenHands + Claude Sonnet 4: ~34%
- Agentless: ~25%

**Takeaway:** The gap between open-source frameworks (SWE-agent, OpenHands) and proprietary CLI tools (Claude Code) is shrinking. Our Player should benchmark against these to calibrate capability expectations. If Claude Code can fix 87% of real GitHub issues, what's blocking our Player from comparable performance? Likely factors: constrained action space, test-retry loops, and structured debugging patterns — all architecture decisions, not model capability.

## Capability Gap Matrix

| Capability | We Have | SWE-agent | MetaGPT | Voyager | Reflexion | CrewAI |
|---|---|---|---|---|---|---|
| Constrained action space | Partial (subagent toolsets) | Core design | No | No | No | No |
| Structured agent artifacts | AGENTS.md + checkpoint | Git diff only | PRDs, Designs, API specs | Skills library | Reflections | Tasks + Context |
| Self-generated skills | No | No | No | Core design | No | No |
| Episodic failure memory | .checkpoint.json notes | No | No | No | Core design | Memory module |
| State-machine orchestration | Binary (approved/stuck) | Linear | Sequential only | Loop-based | Linear | Flows (event-driven) |
| Executable plans | No | No | No | No | No | No |
| Dynamic role assignment | Fixed 2-agent | Single agent | Fixed roles | Single agent | Single agent | Configurable |
