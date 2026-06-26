---
name: zoul-delegation
description: "Delegation patterns migrated from OpenClaw zoul agent. Maps OpenClaw spawn_agent to Hermes delegate_task."
---

# Zoul Delegation Patterns

Migrated from OpenClaw. This skill defines how to decompose and delegate tasks using Hermes tools.

## Delegation Philosophy

**Delegate first.** You are an orchestrator — decompose and dispatch, not execute everything yourself. Only do the work yourself when no agent fits or the task is trivial (<5 min).

## Task → Agent Mapping

| Task Type | Hermes Tool | Approach |
|-----------|-------------|----------|
| Research / data gathering | `delegate_task` + web toolset | Research subagent |
| Code review / refactor / QA | `delegate_task` + terminal+file toolsets | Coder subagent |
| Context prep / code ingestion | `delegate_task` + terminal+file toolsets | Codi subagent |
| Planning / architecture | `delegate_task` + web toolset | Planner subagent |
| Writing / documentation | `delegate_task` + file toolset | Writer subagent |
| Learning / guidance / mentoring | `delegate_task` + web toolset | Coach subagent |
| Automation scripts / ops | `delegate_task` + terminal toolset | Automator subagent |
| Browser automation | `delegate_task` + browser toolset | Browser subagent |

## Using delegate_task

### Single task
```json
{
  "goal": "Research the latest FastAPI middleware patterns",
  "toolsets": ["web"],
  "role": "leaf"
}
```

### Parallel batch
```json
{
  "tasks": [
    {"goal": "Task A", "toolsets": ["web"]},
    {"goal": "Task B", "toolsets": ["terminal", "file"]},
    {"goal": "Task C", "toolsets": ["browser"]}
  ]
}
```

## Do It Yourself When

- No agent fits the task
- Task is quick (<5 min equivalent)
- You have unique context the subagent lacks
- Someone explicitly asks you personally

## Long-Horizon Autonomous Work

For persistent overnight planning and execution, see the **`roadmap-engine` skill** — covers the Roadmap Autonomy Engine architecture, task types, the nightly session cycle, and productivity dimensions.

## Roadmap Engine (Active Implementation)

Built May 2026. Lives in `hermes-sync/scripts/`:
- `roadmap.py` — data model + CRUD
- `reporters.py` — Phase 3 narrative report generator
- `roadmap_engine.py` — main entry point, wires Phase 1+2+3

Tracked projects: `repo-transmute`, `everything-dashboard`, `hermes-agent`, `nanobot`.

**Known issue:** `repo-transmute` had 0 tests collected — `pyproject.toml` configures `tests/` but pytest not discovering. Verify test discovery works before running `test` task type.

## Anti-patterns

- Don't spawn subagents for trivial lookups — do it yourself
- Don't chain 5 subagents in sequence when one can do the job
- Don't delegate tasks that require user interaction (subagents can't use clarify)

## Subagent → Backend Dependency Rule

When delegating frontend Socket.IO work, **always verify the backend emits the required event first**.

**Pattern:** Subagent adds `onFooEvent()` in `socket.ts` + wires it in a page → but backend never emits `'foo'`. Frontend silently fails.

**Before delegating:** `grep -n "\.emit\(" /opt/data/agent-os/apps/dashboard/backend/src/index.ts`
- If the event isn't there: add backend emission first, then delegate frontend
- Or delegate both together with explicit backend instructions in the `context` field

This applies to any event the subagent needs: `docker:containers`, `log`, `cron:updated`, `events`, etc.

## Multi-Agent Pipeline Workflows

For complex closed-loop systems, design agents in a pipeline rather than parallel. Example: **visual QA pipeline** (built for hermes-web-computer 2026-05-23):

```
capture_agent  →  screenshot_agent  →  diff_agent  →  repair_agent  →  verify_agent
     │                  │                  │              │               │
  chrome on         SCP to container   PIL pixel      CSS fix plan   score ≥ 0.85
  host via SSH          for analysis     diff          via LLM          → commit
```

**Key pattern:** Each agent does one thing well. The pipeline self-corrects: verify_agent's score feeds back to repair_agent's next iteration. Only proceed when threshold is met.

**Delegate to pipeline when:**
- Task has distinct phases (capture → analyze → fix → verify)
- Each phase needs different tooling / model capability
- Quality threshold must be met before moving forward
- No single agent can do all phases efficiently

**Pipeline constraints:**
- `no_agent=True` script-only agents for data collection (watchdog pattern)
- LLM-driven agents for analysis, repair planning, judgment calls
- Host-side execution for browser/Chrome operations (container sandbox lacks system libs)
- Self-contained prompts — cron runs have no session context

**Example context passed to each agent:**
```
capture_agent: "SSH to 172.19.0.1, run chrome-headless screenshot at 1440x900, save to /tmp/hwc-qa/screenshots/"
screenshot_agent: "SCP screenshots from host to container, verify file integrity"
diff_agent: "PIL pixel-diff current vs baseline, return diff_percent and diff_image"
repair_agent: "Given diff output + reference image, generate CSS fix list"
verify_agent: "If score ≥ 0.85: commit. If < 0.85: loop back to repair_agent with specific failures."
```
