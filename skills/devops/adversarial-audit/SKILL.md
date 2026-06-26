---
name: adversarial-audit
description: "Use when: (1) building commitment tracking / promise-keeping systems for AI agents, (2) running compliance audits against stated commitments, (3) designing cron-based adversarial verification of agent behavior, (4) debugging why an auditor cron job failed to run or produced no output. Covers the full pattern: commitments.md format, auditor cron job design, session_search-based transcript analysis, and filesystem isolation pitfalls across container boundaries."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [adversarial, audit, compliance, commitments, cron, verification, agent-ops]
    related_skills: [agent-ops, self-improvement-engine, cron-job-patterns]
---

# Adversarial Audit Pattern

Build external verification systems that check whether an agent follows its stated commitments. The core principle: **don't trust the agent to verify itself.**

## When to Use

- User asks "how do I trust you to do X" or "make sure you actually do Y"
- Building commitment/promise tracking for an AI agent
- Running compliance audits against stated commitments
- Designing cron-based adversarial verification
- Debugging why an auditor cron job failed or produced no output

## Architecture

```
/workspace/
├── commitments.md          # Source of truth — all active commitments
├── audit-report.md         # Latest audit output
└── scripts/
    └── commitment_auditor.py  # Standalone auditor script (optional)
```

### Commitments File Format

Each commitment needs:
- **ID**: `C-YYYYMMDD-NNN` — unique, sortable
- **Commitment text**: Specific and verifiable (not vague promises)
- **Verification method**: What to look for in session transcripts
- **Status**: `active` | `fulfilled` | `violated` | `retired`
- **Violation count**: Incremented by the auditor

### Auditor Cron Job Design

The auditor is a **separate cron job** that:
1. Reads `commitments.md`
2. Uses `session_search` to find recent sessions
3. Analyzes transcripts for each commitment
4. Writes violations to `audit-report.md`
5. Prints summary to stdout (delivered to user)

**Critical**: The auditor runs in its own context. It must NOT trust the agent being audited.

## Session Analysis Patterns

### Skill Usage Compliance (C-20260708-001 pattern)

For each session with 3+ tool calls:
- Check if `skill_view` was called BEFORE file writes/edits
- Look for explicit skill scan logging ("Skills scanned: X, loaded: Y")
- Flag sessions where non-trivial work began without loading relevant skills
- **Heuristic**: Count tool call indicators in session summary. If `read_file`, `write_file`, `terminal`, `patch`, `search_files`, `skill_view`, `skill_manage`, `delegate_task`, `execute_code` appear 3+ times total, it's non-trivial.

### Learning Capture Compliance (C-20260708-003 pattern)

For sessions where errors were overcome:
- Check if `skill_manage` or `memory` tools were called near session end
- Look for phrases like "logged learning", "captured learning", "saved as skill"
- Flag difficult sessions (containing "error", "overcome", "difficult", "tricky", "debug", "fix") that end without learning capture

### Commitment Logging Compliance (C-20260708-002 pattern)

Cross-reference conversation transcripts against commitments file:
- Any stated commitment not logged in the file within the same session is a violation
- This is inherently circular (the auditor IS the commitment logging mechanism) — acknowledge this limitation

## Common Pitfalls

### 1. Filesystem Isolation Across Containers

**The #1 pitfall.** Webui sessions and cron jobs may run in different container contexts with different filesystem views. Files written to `/workspace/` in one container may not exist in another.

**Fix**: Use a shared path that persists across containers:
- `/opt/data/` — typically shared via volume mount
- `/home/hermes/` — home directory, usually shared
- Verify with: `ls <path>` from both contexts before relying on it

**Real example**: The auditor cron job referenced `/workspace/commitments.md` but the file was created in the webui container. The cron container couldn't see it. The auditor would silently fail on first run.

### 2. Session Search Limitations

`session_search` returns summaries, not full transcripts. The auditor must work with:
- Session summaries (compact, may omit details)
- `bookend_start` and `bookend_end` messages (±3 messages around match)
- `messages` window (±5 messages around match)

For deeper analysis, use `session_search(session_id=..., around_message_id=..., window=N)` to scroll through specific sessions.

### 3. Cron Job Delivery Configuration

The `deliver` parameter controls where audit reports go:
- `"origin"` — delivers to the session that triggered the cron
- `"local"` — delivers to the local terminal
- Array syntax like `["terminal", "file", "web"]` may not work — use a single string

If the auditor produces no output, check:
1. Can it read `commitments.md`? (filesystem isolation)
2. Can it call `session_search`? (tool availability in cron context)
3. Is `deliver` configured correctly?

### 4. Heuristic-Based Detection Is Imperfect

The auditor uses heuristics on session summaries. It will miss violations and may produce false positives. This is acceptable — the goal is to catch obvious patterns, not achieve 100% accuracy.

**Do not** let "the auditor didn't find violations" be interpreted as "commitments are being followed." The auditor has limited visibility.

### 5. Self-Referential Commitment Logging

The commitment to log commitments (C-20260708-002) creates a circular dependency: the auditor checks whether commitments were logged, but the auditor IS the mechanism that logs commitments. This commitment is inherently unverifiable by the automated auditor.

**Mitigation**: Log commitments proactively during the session, not just when the auditor runs. The auditor can then verify that the log matches what was said.

## Verification Checklist

Before declaring the adversarial audit system operational:

- [ ] `commitments.md` exists at a path visible from the cron container
- [ ] At least one active commitment is logged with verifiable criteria
- [ ] Auditor cron job is created with correct schedule and delivery
- [ ] Auditor prompt includes specific session analysis steps
- [ ] Test run: manually trigger the cron job and verify it produces output
- [ ] Verify the output is delivered to the user (not just written to a file)

## Integration with Agent-Ops

This skill complements `agent-ops`:
- `agent-ops` = gotchas, terminal gating, validation (prevention)
- `adversarial-audit` = commitment tracking, compliance checking (detection)

Use both together: agent-ops prevents known failure modes, adversarial audit detects commitment violations.

## Detecting Regression — The Two-Step session_search Technique

The hardest thing to audit is the ABSENCE of a behavior. If OWL never calls
`skill_view`, you cannot find `skill_view` in search results — and empty results
don't tell you whether no sessions exist or sessions exist but lack the behavior.

**Technique**:
1. **Browse**: Call `session_search()` with no arguments. This returns the most
   recent sessions chronologically with previews, regardless of content.
2. **Search for presence**: For each session ID returned in step 1, call
   `session_search(query="skill_view", session_id="<id>")`. If this returns no
   results, the session did NOT use skill_view.
3. **Check message count**: Sessions with high message counts (100+) that have
   zero skill_view/memory/skill_manage calls are high-confidence violations.

**Important**: FTS5 only indexes what's in the messages. It cannot tell you
what's NOT there. The two-step browse-then-verify technique is the only reliable
way to detect compliance absence.

## The Infrastructure-vs-Behavior Gap

A critical pattern discovered in the second audit: **the agent built the
commitment infrastructure but did not change its working behavior.**

This manifests as:
- Commitments.md written, auditor cron created, AGENTS.md updated — all correct
- Working sessions (Discord fix, GTO development) after the commitments show
  zero compliance: no skill loading, no learning capture, no change
- The agent does what it was asked to do structurally, then reverts to old
  patterns in actual work sessions

**Detection**: Compare pre-commitment and post-commitment sessions on the same
metrics (skill_view count, skill_manage count, learning capture). If post-
commitment numbers are identical to pre-commitment, the commitments are
performative.

**Implication**: Prompt-based commitments alone are insufficient. Consider:
- Structural enforcement (pre-tool-call gating that requires skill scan output)
- System prompt modification (embedding skill-loading as a hard constraint)
- Runtime hooks that reject tool calls before the first skill scan

## Systemic vs Agent-Specific Violations

Cron agents and webui agents may run different models with different capabilities.
In a real deployment:
- Webui sessions use `openrouter/owl-alpha` (or similar)
- Cron sessions use `deepseek-v4-flash` (or similar)

**Audit them separately**: A cron agent skipping skill loading when its prompt
explicitly says to do it is a different problem from OWL skipping it — different
model, different prompt, different tool access. But both violating the same
behavioral expectation suggests a **systemic** issue (the system prompt
instruction format isn't effective) rather than an agent-specific one.

## Real-World Calibration

### First Audit (2026-06-08)
- 3 commitments checked, 3 violations found across 5 sessions
- Skill loading was performative (3 generic skills loaded, dozens of relevant ones ignored)
- Learning capture was inconsistent (some sessions captured learnings, many didn't)
- Self-improvement-engine infrastructure was broken
- Filesystem isolation was the #1 structural risk
- Assessment: **static with concerning gaps**

### Second Audit (2026-06-11)
- 3 commitments checked, 4 violations found across 4 sessions
- Zero skill_view calls in ALL post-commitments webui sessions
- Discord fix session (422 msgs): complete C-001 failure
- GTO wizard clone session: same pattern post-commitments
- Cron agents also skipping skill loading despite explicit instructions
- Assessment: **regressing** — the gap between commitments and behavior widened

Full details: `references/second-audit-regression-findings.md`
