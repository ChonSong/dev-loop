# Timeout Diagnosis for Cron Jobs

## The Two Timeouts

| Timeout | Config Key | Default | Error Signal | What It Kills |
|---------|-----------|---------|-------------|---------------|
| **Terminal** | `terminal.timeout` | 180s (3 min) | `[Errno 32] Broken pipe` | A single subprocess (command) |
| **Agent idle** | `agent.gateway_timeout` / `HERMES_AGENT_TIMEOUT` | 1800s (30 min) | Agent stops making tool calls | The entire agent session |

## Diagnostic Checklist

When a cron job fails with `[Errno 32] Broken pipe`:

1. **Check the cron output** — look at what command was running when it died (test suite, build, install). Long-running commands are the culprit.
2. **Increase `terminal.timeout`** — `hermes config set terminal.timeout 600` (10 min). This is almost always the right fix.
3. **Do NOT assume it's a prompt/skill bloat problem** — inline skill content increases token consumption (rate-limit concern) but does not cause broken pipes.

## When to Increase Terminal Timeout

- Project test suite takes >2 min (`npx vitest run`, `npx turbo build`, `uv run pytest`)
- Multiple project sub-commands chained in a single `terminal()` call
- Docker build/pull operations
- Any command whose wall time might exceed 180s

## When to Trim Skill Content Instead

- The cron job consistently hits **provider rate limits** (HTTP 429, insufficient quota)
- The agent takes noticeably long to start processing (30+ seconds before first tool call)
- The inline skill is >20KB and the cron runs frequently (every 30min or less)

These are orthogonal concerns — fixing the timeout doesn't fix rate limits, and trimming skills doesn't fix broken pipes.

## Current Settings (as of 2026-06-23)

```bash
# Check current values
grep "timeout:" ~/.hermes/config.yaml
grep "max_turns:" ~/.hermes/config.yaml
```

### Applied 2026-06-23 batch

| Setting | Before | After | Why |
|---------|--------|-------|-----|
| `terminal.timeout` | 180s | **600s** | Player was hitting broken pipe on long test runs (pytest 20s + vitest) |
| `agent.gateway_timeout` | 1800s (30 min) | **3600s (60 min)** | Coach needs runway for 85KB skill loading + Tandem comparison + backlog gen |
| `agent.max_turns` | 300 | **500** | More tool call budget for multi-phase reviews that span Tandem + tests + backlog |

```bash
hermes config set terminal.timeout 600
hermes config set agent.gateway_timeout 3600
hermes config set agent.max_turns 500
```

### How to verify
```bash
grep -A4 "^agent:" ~/.hermes/config.yaml
grep "timeout:" ~/.hermes/config.yaml
```

## Reducing Token Pressure (Orthogonal to Timeouts)

When cron jobs hit rate limits (HTTP 429) rather than broken pipes, the fix is reducing prompt size, not increasing timeouts.

**Coach-agent example (2026-06-23):** 81KB skill → 17KB (trimmed to ~20% original). Same operational knowledge, 4x less token overhead per tick. Approach:
- Cut verbose subsections (6 checks A-F, 5 external sources, phase-by-phase instructions)
- Keep core logic (review protocol, decision framework, canvas interaction)
- Move session-specific details to `references/` directory
- Replace elaborated examples with one-line summaries

Apply same pattern to any skill that causes rate-limit pressure: trim before restructuring.
