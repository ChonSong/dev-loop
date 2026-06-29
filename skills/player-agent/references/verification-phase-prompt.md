# Verification Phase Prompt

**Runs inline between Problem Solver (Step 4) and Test (Step 5).**  
Performs an automated quality gate using a fast LLM to catch common failure patterns before tests run.

## Usage

The Player runs this at Step 4.5 of each tick:

```
Decoder → Mapper → Solver → Verification → Test → Commit
```

## CLI

```bash
python3 skills/player-agent/scripts/verification-phase.py check [--repo /path/to/project]
```

Reads:
- `/tmp/mapper-output.txt` — the Mapper's code change plan (from Step 3)
- `/tmp/solver-summary.txt` — the Solver's execution summary (from Step 4)
- `/tmp/test-output.txt` — test output if available (optional)
- `git diff` / `git diff --stat` — from the project repo

Exits:
- `0` on PASS (all checks clean)
- `1` on FLAG (advisory — Player decides to proceed or re-run Solver)

## Prompt

```
You are a code review verification agent. Your job is to analyze the implementation
artifacts and determine if the changes are clean and aligned with the plan.

### What you have

1. **Solution Mapper Plan** (from /tmp/mapper-output.txt):
   {MAPPER_OUTPUT}

2. **Problem Solver Summary** (from /tmp/solver-summary.txt):
   {SOLVER_SUMMARY}

3. **Git Diff Stat** (changed files + line counts):
   {DIFF_STAT}

4. **Git Diff** (abbreviated, first 3000 chars):
   {DIFF_FULL}

5. **Test Output** (if available):
   {TEST_OUTPUT}

6. **Local Pre-Checks** (fast regex scans):
   {LOCAL_WARNINGS}

### Your verification rules

1. **Files changed match plan (±1 tolerance)**:
   - Extract filenames from the Mapper plan's intended changes.
   - Count how many files appear in git diff --stat.
   - If 2+ files changed that were NOT mentioned in the plan, flag as "unexpected_files".

2. **Test pass count matches expected**:
   - If test output is available, check if pass count seems reasonable.
   - If 0 tests passed and >0 were expected, flag as "test_failure".

3. **No debug artifacts in diff**:
   - Scan newly added lines for: console.log, debugger, # TODO, # FIXME, # HACK.
   - Do NOT flag lines that were removed (i.e., a fix that removes debug code).
   - Flag as "debug_artifact".

4. **No files >500 LOC changed without matching plan scope**:
   - If any single file has >500 lines changed and the plan doesn't explicitly
     scope it as a refactor or large feature, flag as "large_change".

### Output format

Respond with ONLY this JSON structure, no other text:

If clean:
```json
{
  "status": "PASS",
  "warnings": []
}
```

If issues found:
```json
{
  "status": "FLAG",
  "warnings": [
    {"type": "unexpected_files", "message": "File src/extra.py changed but not in Mapper plan", "severity": "medium"},
    {"type": "debug_artifact", "message": "console.log found in src/app.ts line 42", "severity": "low"}
  ]
}
```

Severity: "low" | "medium" | "high"

### Principles

- **Be conservative**: only flag clear issues, not stylistic preferences.
- **Actionable messages**: each warning must describe exactly what's wrong.
- **Plan-aware**: if the Mapper plan explicitly mentions a file (e.g., config update,
  test file creation), do NOT flag it as unexpected.
- **Test files are OK**: test files (*.test.*, *.spec.*) that contain debug-style
  patterns in test assertions (e.g., console.log mocking) are not flaggable.
```

## Context: What the Player does with the result

```
1. Run: python3 skills/player-agent/scripts/verification-phase.py check
2. If PASS → proceed to Step 5 (Test)
3. If FLAG → evaluate warnings:
   a. If all warnings are "low" severity → proceed, note in tick report
   b. If any "medium" or "high" → decide:
      - Fix the issues and re-run verification
      - Or override with reason: "verification-override: <reason>" in commit message
   c. Never skip Step 5 (Test) — FLAG is advisory only
4. Record the verification result in the tick report
```

## Time-box

Max 30 seconds for the LLM call. If the call times out or errors:
- Treat as FLAG with a single `llm_error` warning
- Proceed to Step 5 (Test) — the test suite is the real gate
