---
name: hermes-curator-evolver
description: Evidence-driven companion to v0.12's built-in Curator. Observes tool/skill/session events into local SQLite, backfills existing `~/.hermes/sessions/*.json`
category: 
tags: []
source: 0xNyk
is_imported: true
---

# hermes-curator-evolver

Evidence-driven companion to v0.12's built-in Curator. Observes tool/skill/session events into local SQLite, backfills existing `~/.hermes/sessions/*.json`

**Category:** hermes-internal
**Source:** 0xNyk

---

## Architecture

Two layers are at play:

### 1. Built-in Curator Daemon (primary)
Configured in `config.yaml` under `auxiliary.curator`:
```yaml
curator:
  enabled: true
  interval: 7d
  max_runs: 1
auxiliary:
  curator:
    provider: auto    # MUST be explicit — auto fails with 404 on MiniMax-M2
    model: ''         # Set explicitly, e.g. 'anthropic/claude-sonnet-4'
    timeout: 600
```
The daemon runs on a schedule, writes evidence to SQLite (`~/.hermes/curator/evidence.db`), and performs an LLM review pass to identify skill gaps.

### 2. Skill Stub (this skill)
The `hermes-curator-evolver` skill file is a **class-level umbrella** — an empty shell that documents the subsystem. The actual evolution happens in the built-in daemon. This skill's job is to be the entry point for understanding, diagnosing, and improving the curator loop.

---

## Key Integration Points

| Component | Location | Purpose |
|-----------|----------|---------|
| Evidence DB | `~/.hermes/curator/evidence.db` | SQLite: tool calls, skill loads, errors, session events |
| Session backfill | `~/.hermes/sessions/*.json` | Historical session ingestion |
| Skill-selector | `~/.hermes/scripts/skill-selector.py` | Scores all skills per turn, underpins the selector layer |
| Skill cache | `~/.hermes/skill-selector-cache/` | Metadata + context_scores from skill-selector-prep |
| Prep cron | skill-selector-prep | Weekly sync from 5 remote repos (~3913 skills total) |

---

## Diagnosing Failures

**404 on curator LLM review step:**
- Cause: `provider: auto` resolves to MiniMax-M2.7, but MiniMax rejects an empty model string in this context
- Fix: Set explicit `provider` and `model` in `auxiliary.curator` (e.g. `provider: openrouter`, `model: anthropic/claude-sonnet-4`)
- The curator daemon itself runs fine — only the LLM review pass fails

**Skill not improving after corrections:**
- Check `~/.hermes/curator/evidence.db` for recent events
- Confirm `curator.enabled: true` in config.yaml
- Verify the skill that was corrected has a body (empty-stub skills like this one cannot be patched by curator)

---

## Pitfalls

- **Empty skill stubs:** `hermes-curator-evolver` and `hermes-dojo` are class-level umbrellas maintained here. The built-in daemon does the actual work — these files document the subsystem, they don't implement it.
- **Auto provider + 404:** Never leave `provider: auto` with an empty model string for curator's LLM review. Always use an explicit working provider.
- **Confusing skill-selector with curator:** skill-selector scores skills per turn; curator evolves them over time. They are complementary, not redundant.
- **`hermes-dojo` is a sibling stub:** same pattern as `hermes-curator-evolver` — documents a subsystem but the actual work happens elsewhere. Dojo monitors skill performance; curator drives evolution. Both need the same config care (explicit LLM providers, no auto-provider defaults).

---

## Related Skills

| Skill | Role |
|-------|------|
| `software-development/skill-selector` | Per-turn scoring + auto-load (~3913 skills) |
| `software-development/skill-selector-prep` | Weekly cache rebuild from 5 remote repos |
| `hermes-curator-evolver` | Evidence-driven skill evolution (built-in daemon) |
| `hermes-dojo` | Performance monitoring + skill improvement |

---

## When to Use This Skill

- User asks whether curator is running or worth enabling
- Diagnosing a curator failure or performance issue
- Understanding the evidence-gathering → skill-improvement loop
- Deciding between fixing curator config vs relying on skill-selector layer alone
