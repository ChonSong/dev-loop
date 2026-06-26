---
name: structured-code-review
description: "Structured code review output format. Trigger on: reviewing code / /review / /cr / asking to audit / get a second opinion on a plan, PR, diff, or design doc. The reviewer MUST produce output conforming to this format."
---

# Structured Code Review

Produce all code review output in this exact format. No deviation.

## Sections (required order)

### verdict: APPROVED | REVISION_REQUIRED | REJECTED
### severity: CRITICAL | WARN | INFO (only if REVISION_REQUIRED or REJECTED)
### summary: One-line description of the overall finding

### issues: (only if REVISION_REQUIRED or REJECTED)
  - **file**: path/to/file
  - **line**: N (optional)
  - **type**: bug | style | missing | perf | security
  - **description**: what is wrong
  - **fix**: specific suggestion (not "fix it")

### approved_items: (only if APPROVED)
  - list of items/files that passed review

### notes: (optional) Additional context for the orchestrator

## Rules

- CRITICAL → verdict is REJECTED
- WARN → verdict is REVISION_REQUIRED
- INFO alone does not block approval
- CRITICAL: data loss risk, security vuln, broken functionality
- WARN: wrong approach, missing tests, significant tech debt
- INFO: style nits, minor improvements

## Anti-patterns (do not do)

- Don't write "LGTM" without the `### verdict: APPROVED` line
- Don't omit `### issues:` block when verdict is REVISION_REQUIRED
- Don't use conversational language — use the schema fields
- Don't suggest fixes without being specific (no "fix the bug")

## When to Reject vs Request Revision

| Situation | Verdict |
|-----------|---------|
| Security vuln (SQL injection, auth bypass, secrets in code) | REJECTED |
| Data loss possible (no backup, destructive operation) | REJECTED |
| Core functionality completely broken | REJECTED |
| Wrong approach but fixable | REVISION_REQUIRED |
| Missing tests (non-critical path) | REVISION_REQUIRED |
| Style nits, formatting, minor | INFO (APPROVED with notes) |
| All checks pass | APPROVED |