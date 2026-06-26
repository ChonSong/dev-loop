---
name: adversarial-commitment-audit
description: "Independent adversarial audit of whether an agent follows its stated commitments. Scans session transcripts, cross-references behavior against known rules, and produces structured violation reports."
category: quality
---

# Adversarial Commitment Auditor

You are an **independent** auditor — not the agent being audited. Do not trust the agent's self-assessment. Verify every claim with transcript evidence.

## When to Use

Any time the user asks you to:
- "Check if the agent is following its rules"
- "Audit commitment compliance"
- "Verify the agent's behavior against stated standards"
- "Run a commitment audit"
- "Check what skills/commitments the agent has been ignoring"

## Prerequisites

- Access to session_search (FTS5 session DB) — the primary evidence source
- Know which commitments exist (the user provides them, or you read a commitments file)
- Write-only access to /tmp/ for the audit report (no cross-profile persistence)

## Workflow

### Step 1: Capture the Commitments

Write a temporary file at `/tmp/commitments_audit.md` with the commitments to verify. Each commitment needs:
- **ID**: e.g., C-20260708-001
- **Description**: What the agent promised to do
- **Verification method**: What transcript evidence would confirm or refute compliance

### Step 2: Retrieve Session Data

Use `session_search(limit=10, sort="newest")` to get recent sessions. Focus on:

- **High-message-count sessions** (50+ messages) — these are non-trivial and most likely to violate commitments
- **Sessions where file writes (write_file, patch) occurred** — these are the critical verification points for C-001 (skill_view before edits)
- **Sessions where the agent overcame errors** — these are the targets for C-003 (learning capture)

### Step 3: Analyze Each Commitment

**C-001 (Skill Usage Before Non-Trivial Tasks)**: 
- For any session with 3+ tool calls, check if skill_view was called BEFORE the first file write or edit.
- Use session_search with `query="skill_view"` to find all skill_view calls.
- Cross-reference: find the earliest file write/patch and compare timestamps.
- Flag: if a session started with investigative tool calls (browser, terminal, read_file) without loading a skill first.

**C-002 (Commitment Logging)**:
- Often unverifiable from isolated audit containers.
- Note this limitation explicitly rather than fabricating a finding.

**C-003 (Learning Capture After Difficult Tasks)**:
- For sessions with 5+ tool calls and visible error recovery, check whether skill_manage or memory tools were called.
- Use session_search with `query="skill_manage OR memory"` to find capture events.
- Flag: major work sessions that end with a summary but no skill/memory capture.

**Other commitments**: Adapt the analysis to the specific verification criteria.

### Step 4: Write the Report

Format at `/tmp/audit-report.md`:

```markdown
# Commitment Audit Report
**Generated**: [date]
**Commitments checked**: N
**Sessions analyzed**: N
**Violations found**: N

## Violations (if any)
- [C-ID] [severity: HIGH/MEDIUM/LOW]: detail — session date

## Summary
Brief assessment: improving, static, or regressing?
```

### Step 5: Output

Print the summary to stdout. Do NOT use send_message — the audit report IS the final response.

## Pitfalls

- **Don't trust the agent's self-report.** Verify with actual transcript text. The session_search tool returns message content — use it.
- **Don't skip borderline sessions.** If a task has 3+ tool calls and is non-trivial, it counts. Mechanical push-to-github might be borderline; a 55-message GDD review is not.
- **Don't assume skill_view = compliance.** Check WHEN it was called, not just that it was called. Late-in-session skill_view violates C-001 even if it eventually happened.
- **Don't fabricate C-002 findings.** If you can't access the agent's commitments file, say so clearly.
- **Don't be lenient.** The role is adversarial auditor, not friendly reviewer.
- **Cron sessions are partially exempt** if the system injects their skill context. But they still should scan for additional matching skills.
- **session_search with query="skill_view" or "skill_manage OR memory"** is the most efficient way to find evidence across many sessions. Use it.

## Evidence-Gathering Techniques

| Question | How to Check |
|----------|-------------|
| Did agent call skill_view? | `session_search(query="skill_view", limit=10, sort="newest")` |
| Did agent call skill_manage or memory? | `session_search(query="skill_manage OR memory", limit=10)` |
| Was skill_view before file writes? | Compare message_id patterns — skill_view call ID should appear before write_file/patch IDs |
| Was the session non-trivial? | Count tool calls. 3+ browser/terminal/file operations + reasoning = non-trivial |
| Were errors overcome? | Look for error messages, retries, workarounds in transcript |
| Did the session capture learning? | Check last 3-5 messages for skill_manage or memory tool calls |
