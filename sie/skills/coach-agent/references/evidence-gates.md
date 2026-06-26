# Coach Evidence Gates — From g3 and Block AI Research

These 8 evidence gates prevent the coach from rubber-stamping and ensure genuine adversarial review. From the Block AI Research paper "Adversarial Cooperation in Code Synthesis" and g3's implementation.

## The 8 Gates

| # | Gate | What It Prevents | Implementation |
|---|------|-----------------|----------------|
| 1 | **Requirements checklist** | Missing requirements | Check each AGENTS.md success criterion individually (✅/❌ with specific gap notes) |
| 2 | **Compilation/run gate** | Code doesn't compile | Run the test suite yourself — don't trust the player's "tests pass" claim |
| 3 | **Functional test gate** | Happy-path-only testing | Test actual behavior with real inputs, not just compilation |
| 4 | **Edge case gate** | Missing boundary conditions | Test negative and boundary cases, not just the primary path |
| 5 | **Security gap checklist** | Auth/validation holes | Check auth on endpoints, input validation, error handling |
| 6 | **Approval sentinel** | Vague prose approval | `DECISION: APPROVE/FIX/REVERT` must be the first line — no prose-only approvals |
| 7 | **Turn limit circuit breaker** | Infinite loops | If you find yourself repeatedly FIXing the same class of issue, escalate via daily audit instead |
| 8 | **Fresh context** | Rationalization of player shortcuts | You already run as a separate agent — no shared history. Use this advantage. |

## Rubber-Stamp Prevention Mechanisms

From the research, five structural techniques prevent the coach from rubber-stamping:

1. **No batching**: Review one commit/unit at a time. Never batch multiple units into one review.
2. **Minimum evidence requirement**: Each criterion must have explicit evidence (diff quote, curl output, test result). "Looks good" is not evidence.
3. **Approval sentinel**: The `DECISION: APPROVE/FIX/REVERT` first-line requirement forces explicit categorization, not prose.
4. **Separation of duties**: The player (implementer) cannot be the sole approver. This is enforced by separate cron jobs.
5. **Requirements anchoring**: Always evaluate against the AGENTS.md criteria, NOT the player's commit message or self-report. The player's description of what they did is irrelevant — only what they actually produced matters.

## Model Guidance

The coach SHOULD use a different (typically stronger/lower-temp) model than the player. In g3, the coach uses lower `max_tokens` and can use a different provider entirely. For this system:
- Coach: `openrouter/owl-alpha` (free, 1M context, strong reasoning)
- Player: `deepseek-v4-flash` (cheap, fast)
- Daily audit: `openrouter/owl-alpha` (free, once daily)
- Expensive models: reserved for rare escalation/architecture tasks only

## Common Coach Failure Modes

| Failure Mode | Symptom | Fix |
|-------------|---------|-----|
| Rubber-stamping | Every review is APPROVE with no evidence | Tighten evidence requirements, check sentinel compliance |
| Over-correction | Coach keeps FIXing trivial style issues | Coach should only block on criteria failures, not taste |
| Inconsistent standards | Same-quality work gets different verdicts | Re-anchor to AGENTS.md criteria every time |
| Context contamination | Coach uses knowledge from previous reviews | Fresh agent per run (already guaranteed by cron separation) |
| Task-mismatch blindness | Coach can't find the "right" task in AGENTS.md and skips review | Evaluate commit against the AGENTS.md task matching the actual file changes; note mismatch in report |

## Session Notes

### 2026-06-15: Player task jumping
The checkpoint's `current_task` was `fix-dev-environment` but the player committed Badugi UI work (`feat(badugi): refactor meta.ai Badugi hand display into React component`). The commit didn't match any checkpoint entry. Resolution: identified the matching AGENTS.md task (`fix-variant-equity-pages`) from the file paths changed, evaluated against that task's criteria, and approved as an incremental improvement. Lesson: always review what was actually committed, regardless of checkpoint state.

### 2026-06-15: git stat command choice
`git log -1 --stat` showed files from the working tree (unstaged changes to pyproject.toml, uv.lock, etc.) in addition to the actual commit's files. Use `git show HEAD --stat` or `git diff HEAD~1..HEAD --stat` to get only the commit's own file list.

### 2026-06-15: Multi-commit backlog review
Player made 3 commits between coach runs (238afc2, 3a7286d, 0148fb2). The coach's `git show HEAD --stat` only reviews the most recent commit, missing the middle one. Solution: use `git log --oneline --after="<last_review_timestamp>" HEAD` to count unreviewed commits first, then if >1, diff `last_reviewed_sha..HEAD` and batch-evaluate. The coach must also update `last_review` in the master checkpoint after reviewing to prevent re-reviewing the same commits.
