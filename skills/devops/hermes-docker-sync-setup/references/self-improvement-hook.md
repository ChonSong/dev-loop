# Self-Improvement Hook

Migrated from OpenClaw's `agent:bootstrap` hook system to Hermes's native Gateway hook system.

## What it does

| Event | Action |
|-------|--------|
| `session:start` | Reads `.learnings/LEARNINGS.md`, `.learnings/ERRORS.md`, `.learnings/FEATURE_REQUESTS.md`. If any have bullet entries, writes `memory/HOOK_SELF_IMPROVEMENT_REMINDER.md` — picked up naturally by the agent on session start. Silently no-ops if no entries. |
| `session:end` | Writes `memory/NEXT_SESSION_CAPTURE_PROMPT.md` — reminds the agent to log anything before the session closes. Cleared on next `session:start`. |

## Location

- **In hermes-sync**: `hooks/self-improvement/HOOK.yaml` + `hooks/self-improvement/handler.py`
- **In running system**: `/opt/data/hooks/self-improvement/` (bind mount target: `~/.hermes/hooks/`)

## How it differs from OpenClaw

| OpenClaw | Hermes |
|----------|--------|
| `agent:bootstrap` event (before workspace injection) | `session:start` (after session context exists) |
| TypeScript hook injected virtual bootstrap file | Python hook writes to `memory/` — agent reads naturally |
| No persistence between sessions | Reminders persist, self-clear when entries consumed |
| Closed ClawHub registry | Open hook system — any skill can add a hook |

## Learnings files

Location: `/opt/data/skills/openclaw-imports/self-improving-agent/.learnings/`

| File | Purpose | Entry format |
|------|---------|--------------|
| `LEARNINGS.md` | Corrections, discoveries, better approaches | `- YYYY-MM-DD: <what happened>` |
| `ERRORS.md` | Command/operation failures | `- YYYY-MM-DD: <error and resolution>` |
| `FEATURE_REQUESTS.md` | Missing capabilities user wanted | `- YYYY-MM-DD: <capability description>` |

## Promotion rules

When a pattern is proven repeatedly, promote:
- Behavioral corrections → `SOUL.md`
- Workflow improvements → relevant skill SKILL.md
- Tool gotchas → relevant tool skill or `skills/software-development/`
- Errors with root cause → `skills/software-development/systematic-debugging/`

## Adding a new hook

```bash
mkdir -p ~/.hermes/hooks/<hook-name>/
# Create HOOK.yaml and handler.py
# Restart gateway to pick up
```

Example `HOOK.yaml`:
```yaml
---
name: my-hook
description: "Does X on session events"
events:
  - session:start
  - session:end
```

Example `handler.py`:
```python
def handle(event_type: str, context: dict) -> None:
    if event_type == "session:start":
        ...
```
