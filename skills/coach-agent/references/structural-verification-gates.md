# Structural Verification Gates — Coach Primary Review

> **Why this exists**: TRAIL (Patronus 2025) proved LLM-based review detects only 11% of errors in agent traces. These deterministic gates are your PRIMARY review — they catch what LLMs literally cannot see. Your semantic review (reference comparison, methodology gate) is SUPPLEMENTARY.

## Gate Execution Order

Run these IN ORDER. If any gate fails, the verdict is FIX (or REVERT if critical). Do NOT skip to semantic review if structural gates fail.

### Gate 1: Test Suite (NON-NEGOTIABLE)

```bash
# Player should have run tests, but verify independently
cd <repo>
# For Python projects
python3 -m pytest --tb=short 2>&1 | tail -20
# For JS/TS projects
npx vitest run 2>&1 | tail -20
# For E2E
npx playwright test 2>&1 | tail -20
```

**Pass**: All tests pass (0 failures)
**Fail**: Any test fails → verdict FIX. NO EXCEPTIONS. Do not approve with failing tests even if "it's just a flaky test" — flaky tests are infrastructure debt and must be fixed or quarantined.

### Gate 2: Build/Compile

```bash
# Verify the project builds
cd <repo>
npm run build 2>&1 | tail -10  # or make, cargo build, etc.
```

**Pass**: Build succeeds with exit code 0
**Fail**: Build fails → verdict FIX

### Gate 3: Diff Validation

```bash
# What files did the Player change?
cd <repo>
git diff HEAD~1 --stat
git diff HEAD~1 --name-only
```

Check:
- **Scope creep**: Did the Player touch files unrelated to the task? If yes, flag as P2 methodology gap.
- **Must-change gate**: Is the diff empty? If yes → verdict FIX (DELEGATE-52 `has_written` check).
- **File provenance**: Files changed > 10? Flag as P2 — possible scope creep.
- **Prohibited patterns**: Did the diff introduce `console.log`, `TODO`, commented-out code, or `only()` in test files? Flag each.

### Gate 4: Known-Bug Regression Check

```bash
# Re-verify every spec_gap from checkpoint.json
cd <repo>
python3 /home/sc/repos/dev-loop/scripts/check-staleness.py --repo <project>
```

Check every `spec_gaps` entry in `.checkpoint.json`. For each:
- If the bug was claimed "fixed" but is still present → verdict REVERT (Player produced false fix).
- If the bug is still present and was NOT claimed fixed → note in findings, increment cycles_stagnant.
- If cycles_stagnant >= 3 → escalate to Grand SIE.

### Gate 5: Deploy Verification

```bash
# Verify the deploy actually succeeded
curl -s -o /dev/null -w "%{http_code}" https://wiz.codeovertcp.com
curl -s -o /dev/null -w "%{http_code}" https://hex.codeovertcp.com
```

**Pass**: HTTP 200 from deployed URL
**Fail**: Non-200 → verdict REVERT (page is down)

**CRITICAL DISTINCTION**: Gate 5 verifies the page LOADS (structural). It does NOT verify the page WORKS (semantic). For "does it work", proceed to Step 2 (reference comparison). Do not conflate these.

## Gate Results → Verdict Mapping

| Gates Result | Minimum Verdict |
|-------------|----------------|
| All 5 pass | Can proceed to semantic review (Step 2) |
| Gate 1 (tests) fail | FIX |
| Gate 2 (build) fail | FIX |
| Gate 3 (empty diff) | FIX |
| Gate 3 (scope creep) | FIX with P2 flag |
| Gate 4 (known bug unfixed) | FIX |
| Gate 4 (false fix claimed) | REVERT |
| Gate 5 (page down) | REVERT |

## Why This Order

1. **Gates 1-5 are deterministic** — they produce the same result every time. There is no judgment call.
2. **LLM semantic review (your Step 2) is probabilistic** — TRAIL shows it has an 11% ceiling. It's valuable but unreliable.
3. **Structural gates catch ~89% of errors** (the ones LLMs miss). Semantic review catches the remaining ~11%.
4. **If structural gates fail, semantic review is wasted effort** — the Player's work isn't ready for review.

## Integration with Player Pre-Commit Hooks

The Player's pre-commit hooks (installed by `install-structural-hooks.py`) already run:
- Must-change gate (no empty commits)
- Security scan (no secrets)
- No self-referential test tasks in AGENTS.md

Your Gates 1-5 are the **post-commit verification** — they validate the work AFTER it's committed, not just the diff before commit. Together they create a structural safety net that catches what LLM review cannot.
