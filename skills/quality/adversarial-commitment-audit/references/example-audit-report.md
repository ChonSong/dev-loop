# Example Audit Report (June 15, 2026)

This is a reference audit produced by the adversarial-commitment-audit skill. Use it as a template for future audits.

## Commitments Checked
- C-20260708-001: Skill Usage Before Non-Trivial Tasks
- C-20260708-002: Commitment Logging
- C-20260708-003: Learning Capture After Difficult Tasks

## Sessions Analyzed
10 sessions (June 13–15, 2026) including:
- a4a60df185eb — Polytopia game (564 messages, non-trivial)
- a3acef21aeeb — GDD review (55 messages, Coach agent)
- 384d4f2ab053 — GitHub push (36 messages, mechanical + auth debug)
- Various cron sessions (player-agent, coach-agent, QA audit, curation)

## Evidence-Gathering Flow

### Finding skill_view calls
```
session_search(query="skill_view", limit=10, sort="newest")
```
Returns sessions where skill_view was called, with message_id anchors for timeline analysis.

### Finding learning capture
```
session_search(query="skill_manage OR memory", limit=10)
```
Returns sessions with skill_manage or memory tool calls — good for C-003 verification.

### Checking session timing
For each session discovered above, use session_search(session_id=..., window=20) to:
1. Check bookend_start — what was the first thing the agent did?
2. If first action was NOT skill_view but was investigative (browser_navigate, read_file, terminal), that's a violation.
3. Check bookend_end — did the session end with a skill_manage or memory call?

## Typical Violation Categories

| Violation | Pattern | Severity |
|-----------|---------|----------|
| Late skill_view | Agent calls skill_view mid-session after already making edits | MEDIUM |
| No skill_view | Non-trivial session with 3+ tool calls, zero skill_view calls | HIGH |
| No learning capture | 5+ tool call session, errors overcome, ends with summary but no skill_manage/memory | HIGH |
| Unverifiable commitment | Can't access agent's internal files from isolated container | NOTE |

## Report Format

```markdown
# Commitment Audit Report
**Generated**: [date]
**Commitments checked**: N
**Sessions analyzed**: N
**Violations found**: N

## Violations
- [C-ID] [severity]: detail — session date

## Summary
Mixed/improving/regressing with key observations.
```

## Key Lessons from This Audit

1. **session_search query="skill_view"** is the most efficient entry point — returns all skill-loading events across sessions with message_id anchors for further scrolling.
2. **Cron sessions have partially-loaded skills** injected by the cron infrastructure. The agent didn't call skill_view itself. This is a grey area — flag it but note the infrastructural exemption.
3. **Commitment C-002 is structurally unverifiable** from an isolated audit container. Always note this rather than guessing.
4. **The audit report goes to /tmp/audit-report.md** — this is a temporary file, not persisted. The summary is stdout.
