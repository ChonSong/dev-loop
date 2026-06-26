---
name: parallel-delegation
description: Batch delegate_task via tasks=[] for parallel subagent execution. Config allows 3 concurrent children.
category: software-development
---

# Parallel Delegation

**Use batch `tasks=[...]`** instead of sequential `delegate_task(goal=...)` calls.

## Why

Hermes config allows **3 concurrent children** (`max_concurrent_children: 3`). Running subagents one-at-a-time wastes wall-clock time. Batch dispatch collapses `N` sequential runs into `N/3` wall-clock time.

Config currently shows: **0% parallel utilization** — all 92 subagent sessions in the last 7 days ran serially.

## How

### ❌ Serial (slow — do not use for 2+ independent tasks)
```python
result_a = delegate_task(goal="Research X")
result_b = delegate_task(goal="Research Y")
result_c = delegate_task(goal="Research Z")
```

### ✅ Parallel (fast — use for any 2+ independent tasks)
```python
results = delegate_task(tasks=[
    {"goal": "Research X", "toolsets": ["web"]},
    {"goal": "Research Y", "toolsets": ["web"]},
    {"goal": "Research Z", "toolsets": ["web"]},
])
# results[0], results[1], results[2] in parallel
```

## When to Use

- **Independent research tasks** (web search, doc lookups, data gathering)
- **Parallel code review** (review 3 files independently)
- **Multiple deployment health checks** (curl several endpoints)
- **Any batch of 2+ tasks with no cross-task dependency**

## When NOT to Use

- Tasks that depend on each other's output (sequential required)
- Tasks that modify the same files (causes git conflict markers)
- Writing to shared state files (checkpoints, AGENTS.md updates)

## Verification

Check parallelism is working by looking at session parent-child links:
- Sessions with `parent_session_id` set that have overlapping timestamps = true parallel
- Currently **0%** of parent sessions have overlapping children — this is the number to improve

## References

- `delegate_task` tool description: `tasks` array parameter
- Hermes config: `delegation.max_concurrent_children: 3`
- Pipeline dashboard: `https://pipeline.codeovertcp.com` — Subagent Fan-Out section
