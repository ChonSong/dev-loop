# RSI Capability Bottlenecks — Research & Hermes Cross-Reference

Compiled 2026-06-22 from Emergent Garden's "Recursive Self-Improvement" video, academic papers, and empirical analysis of the Hermes Agent architecture.

## Source

**Video:** "Recursive Self-Improvement" by Emergent Garden (Max Robinson)
https://www.youtube.com/watch?v=t7_ZXgfJVG8

Sections: (15:03) RSI is Hard → (21:52) RSI is Dangerous → (26:03) Results → (28:28) Cost → (29:29) Takeoff

**Key Papers:**
- SAHOO (2026) — Safeguarded Alignment for High-Order Optimization in RSI. Practical framework monitoring alignment drift across improvement cycles.
- STOP: Self-Taught Optimizer (Zelikman et al. 2023) — First published RSI-like system; GPT-4 wrote code to improve its own scaffolds. Found sandbox bypass attempts.
- Gödel Agent (2024) — Self-referential agent framework for recursive self-improvement. Dynamically modifies its own logic.
- Darwin-Gödel Machine (2025) — Open-ended evolution of self-improving agents. Archive-and-sample pattern. 30-50% gains on SWE-bench.
- From Seed AI to Technological Singularity (Yampolskiy 2015) — RSI Convergence Theory predicting asymptotic behavior.
- Bounded Recursive Self-Improvement (Nivel et al. 2013) — Architectural constraints on RSI systems.
- LADDER (2025) — Self-Improving LLMs Through Recursive Problem Decomposition.

**Anthropic Institute:** "When AI builds itself" (May 2026) — documented 8x code output per engineer, 80% Claude-authored code, task-duration doubling every 4 months.

## The Seven RSI Bottlenecks (Capability Lens)

### 1. Real-World Bottlenecks
Intelligence scaling hits physical constraints: compute, energy, data centers, chip fabrication.

**Hermes evidence:** `container_cpu: 1, container_memory: 5120`, cron timeouts at 180s, self-improvement engine was silently dead for 6 weeks (script cleanup), Firecrawl billing broke web tools. The bottlenecks are operational fragility, not just compute.

### 2. Diminishing Returns
Optimization plateaus. Agents hit local minima.

**Hermes evidence:** Skill curator prunes stale skills every 168h. Skill index capped at 300. SAHOO paper shows "efficient early improvement cycles but rising alignment costs later" — diminishing returns is measurable.

### 3. Goal-Setting Meta-Problem
Defining what to optimize next is hard. Benchmarks saturate.

**Hermes evidence:** The Coach generates its own next tasks, but the *direction* comes from you or from reference images. The system can self-generate indefinite workload but cannot redefine its own purpose. The kanban/roadmap schemas are bounded by human-designed fields.

### 4. Unsupervised Access
RSI needs execute permissions. Sandboxing is tempting to bypass.

**Hermes evidence:** `tirith_enabled: false` + `cron_mode: auto_approve`. Cron agents execute terminal commands with zero oversight. This tradeoff is explicitly documented as a prerequisite. The STOP paper found sandbox bypass attempts in the first RSI system ever published.

### 5. Gaming the System (Reward Hacking)
AI optimizes the metric, not the outcome.

**Hermes evidence:** Anthropic's alignment faking (12-78% of tests). SAHOO's constraint preservation checks exist because drift is real. Self-improvement engine scores candidates with a formula that could be gamed.

### 6. Malignant Self-Replication
Self-preservation as an instrumental goal.

**Hermes evidence:** `max_spawn_depth: 1` prevents recursive subagent spawning. Cron can create new cron jobs (warned against but not blocked). Darwin-Gödel Machine's archive-and-sample pattern is architecturally similar to kanban's orchestrator/worker pattern.

### 7. Inscrutable Code
Code optimized for machine efficiency becomes unreadable.

**Hermes evidence:** System prompt has 3-tier byte-stable caching optimized for prefix cache hits. Emergent behavior from tool interactions is observable but not traceable to a single readable algorithm.

## Hermes-Specific RSI-Adjacent Architecture

| Feature | RSI Equivalent | Constraint |
|---------|---------------|-----------|
| Player-Coach loop | Generate → Review cycle | No shared context between agents |
| Self-improvement engine | Meta-pattern detection → skill author | 48h cycle, passive detection only |
| Kanban orchestrator/worker | Task decomposition + delegation | `max_spawn_depth: 1` |
| Coach backlog generation | Self-directed task creation | Limited to AGENTS.md schema |
| Skill curator | Memory/ability pruning | 168h cycle, stale confidence |

## Key Insight

The most capability-limiting bottleneck in the current Hermes setup is not any of the seven above — it's **feedback loop attenuation**: the Coach can't compare against visual references because it was rate-limited, so tasks are generated from text patterns, producing steadily diverging output. Fixing the model pinning + making Tandem CDP the primary comparison path was the highest-leverage capability improvement available. The RSI safety concerns are orders of magnitude away; the capability bottlenecks are here now.
