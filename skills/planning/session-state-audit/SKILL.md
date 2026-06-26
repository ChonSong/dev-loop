---
name: session-state-audit
description: Review recent sessions, assess system/service state, define priorities, and recommend next actions. Use when the user asks "what have we done lately", "review recent sessions", "define goals", "what's the state of things", "advise continuing", or after returning to the conversation after an absence.
---

# Session State Audit

Systematic review of recent work, current system state, and prioritization of next moves. Designed for multi-day autonomous sessions where context needs to be re-established.

## When to Use

- User says "review recent sessions, define goals and advise continuing"
- User says "what's the state of things", "where were we", "what's happening"
- After returning to the conversation after hours/days of absence
- After a complex cron session delivered results that need context-setting
- Before starting a new task when the last interaction was a different class of work

## Process

### Phase 1 — Scan Recent Sessions

```python
# Browse recent sessions
session_search()  # No args = browse mode

# Search for specific topics from known issues
session_search(query="<topic>", sort="newest")
```

Read at minimum:
- Most recent 1-3 sessions' kickoff and resolution messages (use `session_search(session_id=..., around_message_id=...)`)
- Any cron job output sessions that delivered non-SILENT results

Extract:
- What was accomplished
- What was left unfinished
- What decisions were made

### Phase 2 — Inventory Current System State

Check against known problem areas:

```bash
# Core services
systemctl --user is-active hermes-gateway hermes-dashboard
curl -s -o /dev/null -w '%{http_code}' http://localhost:8787/ && echo ' webui'  # or appropriate ports

# Docker containers
docker ps --format '{{.Names}} {{.Status}}' | grep -E 'healthy|unhealthy'

# Check specific known trouble spots from memory
```

Also read the MEMORY.md file to refresh on known issues from prior sessions.

### Phase 3 — Cross-Reference with Cron Health

```bash
cronjob(action='list')
```

Look for:
- Jobs with `last_status: error`
- Jobs with high run counts that deliver every tick (bloat)
- Jobs referencing deleted/renamed skills

### Phase 4 — Build the Picture

Organize findings into three tiers:

| Tier | Meaning |
|------|---------|
| 🟢 Green | Working, no action needed |
| 🟡 Yellow | Needs attention but not urgent |
| 🔴 Red | Broken/down, needs active intervention |

Within each tier, note:
- What changed since the last review
- Whether the item is actively degrading or stable

### Phase 5 — Recommend Next Actions

For each red/yellow item:
- Estimated effort (2min / 15min / needs-you)
- What the fix is in one sentence
- Flag items blocked on the user (e.g., Discord token, new API key)

Order recommendations by:
1. Impact (what's actually broken vs. cosmetic)
2. Dependencies (fix SSH before deploying logrotate)
3. Automation potential (can a cron job handle this?)

## Output Shape

Present as concise tables with:
- One-line summary per item
- Status emoji
- What changed since last review

Keep the tone action-oriented. Start with what's urgent, end with what's ticking autonomously.

## Pitfalls

- Don't re-read every session fully — use bookend_start/bookend_end patterns to get goals and resolutions without full transcripts
- Don't re-invent the wheel — check memory for known issues from prior session-state-audits before re-scanning
- Don't report "all green" as SILENT — the user asked for a review, so they want to hear the state
- Distinguish between "needs user action" and "needs my action" — Discord tokens require the user; cron config changes require you
- The user prefers backend-heavy targets — weight recommendations toward infrastructure/code work over UI work
- If all is green and nothing notable happened, report that clearly and ask if they want to pick an area to improve

## Related Skills

- `cron-job-optimization` — for deep cron audits triggered by session review findings
- `development-communication` — for transparency norms during the follow-up work
- `project-decommissioning` — when session review identifies projects to remove
