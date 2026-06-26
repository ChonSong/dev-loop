---
name: parallel-investigation
description: "Parallel subagent delegation for research, investigation, and analysis tasks. Spawns 3+ subagents simultaneously to investigate different aspects of a problem, then collates findings into a structured, prioritised report."
version: 1.0.0
tags:
  - delegation
  - parallel
  - research
  - investigation
  - multi-agent
related_skills:
  - subagent-driven-development
  - parallel-subagent-conflicts
  - development-communication
---

# Parallel Investigation

Spawn multiple subagents simultaneously to investigate independent aspects of a topic, then collate results into a structured report with prioritised recommendations. The user explicitly prefers this pattern — "delegate frequently to investigate in parallel and collate findings."

## When to Use

- User says "investigate" or "research" about 2+ distinct subtopics
- User explicitly says "delegate frequently" or "in parallel"
- A decision needs evidence from multiple independent angles (cost, effort, tech fit, alternatives)
- Comparing multiple tools/vendors/approaches for the same problem
- Any task that decomposes naturally into independent research questions

**Parsimony check:** Before spawning N subagents, ask: could a single subagent with a clear goal answer all questions? If yes, use one. Parallel pays off when each subagent's research is completely independent — not just different facets of the same lookup.

## When NOT to Use

- Simple single-fact lookup (use web_search directly)
- Interdependent sub-tasks where one result feeds the next (use sequential delegation)
- Tasks requiring interactive user clarification (subagents can't call clarify)

## Workflow

### 1. Decompose into Independent Questions

Break the investigation into 2-3 questions that can be answered in isolation. Each must be:
- Self-contained (no dependency on other subagent outputs)
- Answerable with the toolsets provided
- Structured enough that the subagent knows what "done" looks like

### 2. Spawn Parallel Tasks

Use `delegate_task` with the `tasks` array:

```python
delegate_task(
    tasks=[
        dict(goal="Investigate X", context="...", toolsets=["web", "terminal"]),
        dict(goal="Investigate Y", context="...", toolsets=["web"]),
        dict(goal="Investigate Z", context="...", toolsets=["web", "terminal"]),
    ]
)
```

**Best practices for task context:**
- Always include: user's infrastructure (OS, RAM, Docker, SSH access), relevant paths, and what's already been tried
- State specific questions the subagent must answer, not vague goals
- Set a toolset restriction — most research needs only `["web"]` or `["web", "terminal"]`
- Avoid `["browser"]` unless the target site requires JS rendering — it's slower
- For environmental checks (is X installed?), include `["terminal"]`

### 3. Collate Findings

When all subagents return, structure the output as:

**For each investigation:**
- **What it is** — one-line summary
- **Key finding** — the single most important fact discovered
- **Data** — concrete numbers (stars, RAM footprint, deployment complexity, cost)
- **Verdict** — fits / doesn't fit / needs more info

**Cross-cutting synthesis:**
- Comparison table when investigating alternatives (feature × tool matrix)
- **Top recommendation** — which option wins and why
- **Action plan** — numbered steps in priority order, each independently deliverable

### 4. Verify Claims

Subagent summaries are self-reports, not verified facts. For claims with external side-effects (HTTP calls, writes, file paths), require the subagent to return a verifiable handle (URL, ID, status code) and verify it yourself.

### 5. Present with Next Step

End the collated report with a clear question or decision point: "Want me to proceed with X?" or "Which option should I implement?"

## Comparison: parallel-investigation vs subagent-driven-development

| Aspect | parallel-investigation | subagent-driven-development |
|--------|----------------------|---------------------------|
| Purpose | Research, analysis, fact-finding | Code execution, implementation |
| Output | Structured report with recommendations | Working code, tests, commits |
| Toolsets | Primarily `web`, sometimes `terminal` | Primarily `terminal`, `file` |
| Collation | Synthesise findings into one report | Integrate code from multiple agents |
| Risk | Incomplete or misleading findings | Git conflicts, broken builds |

## Pitfalls

- **Principle of Parsimony — don't over-parallelize** — Only parallelize when the sub-tasks are truly independent AND the additional context/token cost is justified by the information gain. A single subagent that can answer all questions is cheaper and faster than 3 parallel subagents with overlapping scope. The user explicitly flags this: "delegate frequently to deep-dive in parallel but don't forget principle of parsimony." When in doubt, prefer 1-2 well-scoped subagents over 3 broad ones.
- **Duplicate work** — Two subagents may independently research the same tool. Make sure `goal` statements have clear boundaries.
- **Lazy subagents** — A subagent may claim "I checked X and it's fine" without actually checking. Include verification commands in the context ("run this command and report the output").
- **Context overload** — Each subagent gets its own full context window. Don't cram all three investigations into one subagent.
- **Stale findings** — Web research results may be from cached/wrong pages. Ask subagents to report their sources.
- **Over-parallelisation** — 3 concurrent tasks is the max for this user. Pushing beyond that wastes credential capacity. Batch into groups of 3 if more are needed.
- **Terminal vs browser** — Default to `["web"]` for research tasks. Only add `["terminal"]` when the subagent needs to run environmental checks. `["browser"]` is slower and only needed for JS-rendered sites.
