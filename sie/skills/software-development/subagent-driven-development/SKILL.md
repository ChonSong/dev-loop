---
name: subagent-driven-development
description: "Execute plans via delegate_task subagents (2-stage review)."
version: 1.1.0
author: Hermes Agent (adapted from obra/superpowers)
license: MIT
metadata:
  hermes:
    tags: [delegation, subagent, implementation, workflow, parallel]
    related_skills: [writing-plans, requesting-code-review, test-driven-development]
---

# Subagent-Driven Development

## Overview

Execute implementation plans by dispatching fresh subagents per task with systematic two-stage review.

**Core principle:** Fresh subagent per task + two-stage review (spec then quality) = high quality, fast iteration.

## When to Use

Use this skill when:
- You have an implementation plan (from writing-plans skill or user requirements)
- Tasks are mostly independent
- Quality and spec compliance are important
- You want automated review between tasks

**vs. manual execution:**
- Fresh context per task (no confusion from accumulated state)
- Automated review process catches issues early
- Consistent quality checks across all tasks
- Subagents can ask questions before starting work

## The Process

### 1. Read and Parse Plan

Read the plan file. Extract ALL tasks with their full text and context upfront. Create a todo list:

```python
# Read the plan
read_file("docs/plans/feature-plan.md")

# Create todo list with all tasks
todo([
    {"id": "task-1", "content": "Create User model with email field", "status": "pending"},
    {"id": "task-2", "content": "Add password hashing utility", "status": "pending"},
    {"id": "task-3", "content": "Create login endpoint", "status": "pending"},
])
```

**Key:** Read the plan ONCE. Extract everything. Don't make subagents read the plan file — provide the full task text directly in context.

### 2. Per-Task Workflow

For EACH task in the plan:

#### Step 1: Dispatch Implementer Subagent

Use `delegate_task` with complete context:

```python
delegate_task(
    goal="Implement Task 1: Create User model with email and password_hash fields",
    context="""
    TASK FROM PLAN:
    - Create: src/models/user.py
    - Add User class with email (str) and password_hash (str) fields
    - Use bcrypt for password hashing
    - Include __repr__ for debugging

    FOLLOW TDD:
    1. Write failing test in tests/models/test_user.py
    2. Run: pytest tests/models/test_user.py -v (verify FAIL)
    3. Write minimal implementation
    4. Run: pytest tests/models/test_user.py -v (verify PASS)
    5. Run: pytest tests/ -q (verify no regressions)
    6. Commit: git add -A && git commit -m "feat: add User model with password hashing"

    PROJECT CONTEXT:
    - Python 3.11, Flask app in src/app.py
    - Existing models in src/models/
    - Tests use pytest, run from project root
    - bcrypt already in requirements.txt
    """,
    toolsets=['terminal', 'file']
)
```

#### Step 2: Dispatch Spec Compliance Reviewer

After the implementer completes, verify against the original spec:

```python
delegate_task(
    goal="Review if implementation matches the spec from the plan",
    context="""
    ORIGINAL TASK SPEC:
    - Create src/models/user.py with User class
    - Fields: email (str), password_hash (str)
    - Use bcrypt for password hashing
    - Include __repr__

    CHECK:
    - [ ] All requirements from spec implemented?
    - [ ] File paths match spec?
    - [ ] Function signatures match spec?
    - [ ] Behavior matches expected?
    - [ ] Nothing extra added (no scope creep)?

    OUTPUT: PASS or list of specific spec gaps to fix.
    """,
    toolsets=['file']
)
```

**If spec issues found:** Fix gaps, then re-run spec review. Continue only when spec-compliant.

#### Step 3: Dispatch Code Quality Reviewer

After spec compliance passes:

```python
delegate_task(
    goal="Review code quality for Task 1 implementation",
    context="""
    FILES TO REVIEW:
    - src/models/user.py
    - tests/models/test_user.py

    CHECK:
    - [ ] Follows project conventions and style?
    - [ ] Proper error handling?
    - [ ] Clear variable/function names?
    - [ ] Adequate test coverage?
    - [ ] No obvious bugs or missed edge cases?
    - [ ] No security issues?

    OUTPUT FORMAT:
    - Critical Issues: [must fix before proceeding]
    - Important Issues: [should fix]
    - Minor Issues: [optional]
    - Verdict: APPROVED or REQUEST_CHANGES
    """,
    toolsets=['file']
)
```

**If quality issues found:** Fix issues, re-review. Continue only when approved.

#### Step 4: Mark Complete

```python
todo([{"id": "task-1", "content": "Create User model with email field", "status": "completed"}], merge=True)
```

### 3. Final Review

After ALL tasks are complete, dispatch a final integration reviewer:

```python
delegate_task(
    goal="Review the entire implementation for consistency and integration issues",
    context="""
    All tasks from the plan are complete. Review the full implementation:
    - Do all components work together?
    - Any inconsistencies between tasks?
    - All tests passing?
    - Ready for merge?
    """,
    toolsets=['terminal', 'file']
)
```

### 4. Verify and Commit

```bash
# Run full test suite
pytest tests/ -q

# Review all changes
git diff --stat

# Final commit if needed
git add -A && git commit -m "feat: complete [feature name] implementation"
```

## Parallel Track Mode (for large codebases)

**When the serial task-by-task pattern is too slow**, use parallel track delegation:

1. Write a detailed `PLAN.md` with every interface, file path, and data flow locked
2. Define 3-6 tracks, each owning **non-overlapping file sets**
3. Dispatch all tracks simultaneously via `delegate_task`
4. Each subagent writes files and pushes commits independently
5. After all tracks complete, verify build + vet pass

**Critical rules:**
- Each track MUST have exclusive file ownership. If two tracks touch the same file, they'll conflict.
- The PLAN.md must specify exact file paths for every track.
- Include a final integration track (Track N) that wires all packages together.
- Each track should push commits frequently — one subagent may fail while others succeed.

**Example from hermes-web-computer (May 2026):**
- Track 1: Go packages (`backend/layout/`, `backend/security/`, `backend/telemetry/`) — 340s
- Track 2: Frontend (`frontend/src/components/`, `frontend/src/stores/`) — 200s (timed out first at 600s with Monaco, succeeded on narrower scope)
- Track 3: Integration (`backend/ws/`, `backend/cmd/`, `deploy/`, `.github/`, `Makefile`) — 343s
- Total: ~6 min vs ~30+ min serial

**When to use parallel mode:**
- Building a new codebase from spec (not modifying existing code)
- Clear file ownership boundaries exist
- Subagents won't need to read each other's output during execution
- You'll verify integration after all tracks complete

**When NOT to use parallel mode:**
- Modifying existing code (risk of merge conflicts)
- Tasks have interdependencies (Track B needs Track A's output)
- Complex refactoring (serial review catches issues earlier)

## Handling Subagent Timeouts

**Heavy dependencies cause timeouts.** When a subagent tries to install or work with a large library (Monaco, heavy Node modules, large Python ML packages), it can exhaust the API call budget or hit network timeouts.

**The pattern:**
1. First attempt fails with timeout — note which dependency caused it
2. Retry with narrower scope: remove the heavy dependency from the subagent's goal
3. Build the heavy dependency separately or defer it to a later track

**Example:** Frontend track with Monaco editor timed out at 600s (37 API calls). Retry without Monaco (just Tile/CommandPalette/KeymapOverlay) succeeded at 200s (16 API calls). Monaco was deferred to a separate track.

**Prevention:** In the PLAN.md, identify heavy dependencies upfront and either:
- Scope them out of parallel tracks (build separately)
- Add explicit "skip if X is too heavy, report back" instructions

### Task-Type Routing: Which Pattern to Use

**Not every task should go through subagent delegation.** Match the execution pattern to the task type:

| Task Type | Execution Pattern | Why |
|-----------|-----------------|-----|
| Code implementation (multi-file Svelte+Go) | **Direct** (read → patch → build → commit) | Build steps cause subagent timeouts; direct is faster |
| Research/investigation | `delegate_task` (fresh context, parallel possible) | Independent exploration, no build dependency |
| Visual QA / screenshot comparison | **Host script** (playwright on EndeavourOS via SSH) | Container lacks Chromium; needs host environment |
| Documentation / single-file changes | `delegate_task` | Fast, no build verification needed |
| Integration / wiring work | **Direct** or single subagent | Interdependencies require full context |

### The Visual QA Closed-Loop (Non-Delegable)

Visual QA cannot be delegated to a subagent because:
1. The container (where subagents run) lacks Chromium system libraries
2. Playwright screenshots require the EndeavourOS host with a browser installed
3. Vision comparison needs human judgment on "good enough" thresholds

**The pattern:**
```
Build component → commit
     ↓
SSH to host: run playwright screenshot script
     ↓
Vision compare (browser_vision or v2 verify)
     ↓ pass → done
fail → fix specific CSS tokens → re-screenshot → re-compare
```

For hermes-web-computer: use `scripts/visual-qa.sh` on the host. See `hermes-computer` skill §"Container Browser Execution Model".

### When to Abandon Delegation Mid-Session

- 3+ consecutive subagent timeouts on the same task type → switch to direct
- Build steps in the subagent goal (npm run build, go build) → remove them, verify builds yourself
- Visual/screenshot work → not delegable, run on host
- Task involves browser automation → not delegable (missing deps in container)

## Direct Execution Fallback

**When subagents fail repeatedly (3+ consecutive timeouts), abandon delegation and execute directly.**

The `delegate_task` subagents consistently hit 600s API timeouts on hermes-web-computer tasks involving multi-file Svelte + Go changes. They complete 15-22 API calls, modify 5-16 files, then timeout during summary generation. The code is always on disk — but the pattern wastes 30+ minutes waiting for results.

**Direct execution is faster for this project:**
1. Read the relevant files yourself
2. Make the changes directly via `write_file` or `patch`
3. Verify with `go build ./...` and `npm run build`
4. Commit and push

**When to delegate anyway:** Single-file changes, documentation updates, or tasks that don't require build verification. Multi-file Svelte + Go changes with build steps should be done directly.

### Check-Before-Implement (Post-Timeout Recovery)

**After subagent timeouts, ALWAYS check what was actually committed before starting new work.**

A subagent that times out may have still written files and even committed/pushed partial work. Starting fresh implementation of the same feature causes:
- Duplicate work
- Merge conflicts with the timed-out subagent's partial commits
- Wasted API calls implementing what's already done

**The recovery pattern (May 2026 hermes-web-computer session):**
1. Subagent timed out on "implement drag-and-drop" — 19 API calls, likely wrote files
2. Before re-implementing, ran `git status --short` and `grep -n "drop\|dragover"` on relevant files
3. **Result:** drag-and-drop was already fully implemented (FileTree draggable, RightPanel/MiddlePanel drop targets) — just not committed
4. Committed the existing work, saved 2-3 hours of duplicate implementation

**Rule:** After any subagent timeout on a code task, run these before re-implementing:
```bash
git status --short          # see what files were modified
git diff --stat             # see what changed
grep -rn "feature_keyword" relevant_files/   # check if feature is partially implemented
```

**hermes-web-computer Build Timing Pitfall**

**The hermes-web-computer project (`/opt/data/hermes-web-computer`) reliably causes subagent timeouts** when the task includes build verification:

| Step | Time |
|------|------|
| File writes (5-8 files) | ~60-120s |
| `go build ./...` (backend) | ~10s |
| `npm run build` (frontend, Svelte 5 + Monaco) | ~60-120s |
| git commit + push | ~10s |

**Total: 140-260s of work, but 25-40 API calls to get there → timeout at 600s.**

**Solution:** Remove `npm run build` from the subagent's task instructions. Do the build yourself after reviewing the diffs. The subagent will complete more file changes and won't waste API calls on the slow build step.

**Delegate task without build verification:**
```
1. Create/modify files as described
2. Commit + push to main
3. Return summary

DO NOT run npm run build or go build — I will verify builds after reviewing.
```

**Build verification helper:** Use `scripts/hwc-build-verify.sh` (in this skill's directory) to run Go and frontend builds on the host via SSH.

**Better yet — skip delegate_task entirely for hermes-web-computer multi-file changes.** The direct execution approach (read → patch → build → commit) is faster than waiting for a subagent that will timeout anyway. See "Direct Execution Fallback" section above.

### Visual QA Comparison Method

**CRITICAL PITFALL (learned 2026-05-24):** Never use pixel-diff (PIL `ImageChops.difference`) for theme/UI comparison. It produces meaningless scores that don't correlate with human perception (e.g., 81.9% pixel match vs 5% perceived similarity).

**The correct method: CSS token extraction + perceptual color comparison.** For screenshot capture, use `npx playwright screenshot` on the host — NOT `node -e require('playwright')` inline scripts (module resolution fails). See `e2e-testing` skill's `references/playwright-screenshot-technique.md` for the full technique catalog.

**The correct method: CSS token extraction + perceptual color comparison.**

```python
# WRONG — pixel-diff gives misleading scores
diff = ImageChops.difference(hwc_screenshot, reference)
matches = sum(1 for p in diff.getdata() if p == (0, 0, 0))
similarity = matches / total_pixels  # Meaningless number

# CORRECT — extract dominant colors per region, compare with OKLab ΔE
def oklab_delta(rgb1, rgb2):
    """Perceptual color difference. ΔE < 1 = imperceptible, > 10 = obvious."""
    # Convert RGB → OKLab → Euclidean distance
    ...

for region, (x1, y1, x2, y2) in regions.items():
    got = extract_dominant_color(screenshot.crop((x1,y1,x2,y2)))
    expected = spec_tokens[region]  # e.g. "#131313"
    delta = oklab_delta(got, expected)
    if delta > threshold: FAIL → actionable CSS patch
```

**Why pixel-diff fails:**
1. Glassmorphism (translucent+blur) changes every underlying pixel → same perceived color = different pixel values
2. Anti-aliasing and sub-pixel rendering adds noise
3. Font rendering differences (Ligatures, hinting, sub-pixel AA) → identical text = different pixel patterns
4. Whole-image comparison masks component-level mismatches

**OKLab ΔE thresholds:**
| ΔE | Human perception |
|----|-----------------|
| < 1 | Imperceptible |
| 1-2 | Slight difference (acceptable for dark themes) |
| 2-5 | Noticeable (needs fixing) |
| > 5 | Obvious (wrong color) |

### Structural Mismatch Detection

Beyond colors — identify missing elements:
- Reference has dock, screenshot doesn't → CSS display issue or JS not rendering
- Reference has sidebar, screenshot shows full-width → layout collapse  
- Reference has rounded corners, screenshot has sharp → border-radius missing

See `references/visual-qa-methodology.md` in this skill's directory for the full Python implementation.

### Visual QA Script (Non-Delegable Pattern)

Visual QA requires the **EndeavourOS host** — the container lacks Chromium system libraries. This is NOT delegable to subagents because they run in the container.

**The pattern for host-side visual QA in a subagent task:**
```
Controller (this env) ---SSH---> EndeavourOS host (172.19.0.1)
                              |
                              +---> google-chrome-stable (screenshot)
                              +---> /tmp/hwc-qa/baselines/ (baseline storage)
                              +---> scripts/visual-qa.sh (comparison)
```

**Example from 2026-05-23 (HWC visual QA pipeline setup):**
```python
# 1. Controller: dispatch subagent to set up scripts on host
delegate_task(
    goal="Install Chromium and verify Playwright can take screenshots...",
    toolsets=['terminal']  # Must have terminal to SSH
)
# Subagent SSH's to host, runs Chrome CLI screenshot, copies back
```

**SSH tunnel for local dev access:**
```bash
# Container -> host port 3113 (HWC backend)
ssh -i /home/hermeswebui/.hermes/container_key -f -N -L 3113:localhost:3113 sean@172.19.0.1

# Verify tunnel working
curl -s -o /dev/null -w "%{http_code}" http://localhost:3113/  # should return 200
```

**Key finding from 2026-05-23:** `google-chrome-stable` (already on host at `/usr/bin/google-chrome-stable`) works for CLI screenshots. The Playwright chromium headless shell in the container (`~/.cache/ms-playwright/chromium_headless_shell-1223/`) cannot launch due to missing system libs — but Chrome on the host can.

**Pre-commit visual QA checklist (hermes-computer):**
- [ ] Go backend builds on host: `ssh host "cd /opt/data/hermes-web-computer/backend && go build -o /tmp/hwc-server ./cmd/server/"`
- [ ] Backend health: `curl -s -o /dev/null -w "%{http_code}" http://localhost:3113/` → 200
- [ ] Run visual QA on host: `ssh host "bash /opt/data/hermes-web-computer/scripts/visual-qa.sh"`
- [ ] Check diff output — if > 1% regression, fix CSS/tokens before committing

**Baseline storage:** On host at `/tmp/hwc-qa/baselines/baseline-default.png` (1440x900, 120KB). Captured 2026-05-23.

## Common Build & Environment Pitfalls

### NODE_ENV=production blocks devDependencies

When `NODE_ENV=production` is set in the environment, `npm install` skips devDependencies entirely. This causes `vite`, `typescript`, and other build tools to be missing.

**Symptom:** `vite: not found` after `npm install` even though vite is in devDependencies.

**Fix:**
```bash
NODE_ENV=development npm install
# Or
npm install --include=dev
```

### Stale dist directories shadow new builds

When serving static files (Go http.FileServer, nginx, etc.), if multiple `dist/` directories exist on the system, the first one found wins. An old project's stale dist can shadow the new build.

**Symptom:** Server serves old HTML (`<div id="root">`) even though new dist has `<div id="app">`.

**Fix:** Use absolute paths checked first in the file server configuration:
```go
distPaths := []string{
    "/opt/data/hermes-web-computer/frontend/dist",  // Absolute first
    "../frontend/dist",
    "../../frontend/dist",
}
```

### Port binding failures from previous test servers

Long-lived test servers (Go binaries, Node servers) often survive across sessions and block ports.

**Fix:** Force kill before binding:
```bash
fuser -k 3001/tcp 2>/dev/null; sleep 1
# Or use a fresh port each time
PORT=3005 ./agent-os
```

### Go PTY dual-reader race

When both a ring buffer goroutine AND a forwarder read from the same PTY file descriptor, only one gets the data. This causes silent PTY output loss.

**Fix:** Use a single reader goroutine that fans out to both ring buffer and a channel:
```go
// Single reader
go func() {
    for {
        n, _ := p.Read(buf)
        session.RingBuf.Write(buf[:n])
        data := make([]byte, n); copy(data, buf[:n])
        select { case session.Output <- data: default: }
    }
}()

// Client reads from channel
for data := range pty.Output { sendToClient(data) }
```

**Prevention:** In PLAN.md, if building a PTY-based system, specify the channel-based fan-out pattern upfront. Don't have two goroutines read from the same PTY fd.

## Task Granularity

**Each task = 2-5 minutes of focused work.**

**Too big:**
- "Implement user authentication system"

**Right size:**
- "Create User model with email and password fields"
- "Add password hashing function"
- "Create login endpoint"
- "Add JWT token generation"
- "Create registration endpoint"

## Red Flags — Never Do These

- Start implementation without a plan
- Skip reviews (spec compliance OR code quality)
- Proceed with unfixed critical/important issues
- Dispatch multiple implementation subagents for tasks that touch the same files
- Make subagent read the plan file (provide full text in context instead)
- Skip scene-setting context (subagent needs to understand where the task fits)
- Ignore subagent questions (answer before letting them proceed)
- Accept "close enough" on spec compliance
- Skip review loops (reviewer found issues → implementer fixes → review again)
- Let implementer self-review replace actual review (both are needed)
- **Start code quality review before spec compliance is PASS** (wrong order)
- Move to next task while either review has open issues

## Handling Issues

### If Subagent Asks Questions

- Answer clearly and completely
- Provide additional context if needed
- Don't rush them into implementation

### If Reviewer Finds Issues

- Implementer subagent (or a new one) fixes them
- Reviewer reviews again
- Repeat until approved
- Don't skip the re-review

### If Subagent Fails a Task

- Dispatch a new fix subagent with specific instructions about what went wrong
- Don't try to fix manually in the controller session (context pollution)

## Efficiency Notes

**Why fresh subagent per task:**
- Prevents context pollution from accumulated state
- Each subagent gets clean, focused context
- No confusion from prior tasks' code or reasoning

**Why two-stage review:**
- Spec review catches under/over-building early
- Quality review ensures the implementation is well-built
- Catches issues before they compound across tasks

**Cost trade-off:**
- More subagent invocations (implementer + 2 reviewers per task)
- But catches issues early (cheaper than debugging compounded problems later)

## Skills Loading in Delegation Context

**Critical pitfall discovered 2026-05-03:** When a controller (cron job, orchestrator) dispatches subagents for work, it must explicitly load the relevant skills into the subagent's context. The subagent does NOT automatically inherit the controller's loaded skills.

**The problem:**
- Phase 6 cron dispatches a subagent to "fix CI quality gates"
- The subagent's context does NOT include `requesting-code-review`, `test-driven-development`, or `github-pr-workflow` unless explicitly loaded by the controller
- Result: the subagent produces vague output instead of using the established quality skill patterns

**The fix — always in the controller prompt:**
```
SKILLS TO LOAD: requesting-code-review, test-driven-development, github-pr-workflow
```
Or in the delegate_task context:
```
Use the requesting-code-review skill for all quality checks.
Use the test-driven-development skill before writing any new code.
Use the github-pr-workflow skill for CI configuration changes.
```

**Rule of thumb:** If the task has a skill, the controller must name it in the subagent's context. Never assume the subagent will know to consult a skill unprompted.

## Integration with Other Skills

### With writing-plans

This skill EXECUTES plans created by the writing-plans skill:
1. User requirements → writing-plans → implementation plan
2. Implementation plan → subagent-driven-development → working code

### With test-driven-development

Implementer subagents should follow TDD:
1. Write failing test first
2. Implement minimal code
3. Verify test passes
4. Commit

Include TDD instructions in every implementer context.

### With requesting-code-review

The two-stage review process IS the code review. For final integration review, use the requesting-code-review skill's review dimensions.

### With systematic-debugging

If a subagent encounters bugs during implementation:
1. Follow systematic-debugging process
2. Find root cause before fixing
3. Write regression test
4. Resume implementation

## Example Workflow

```
[Read plan: docs/plans/auth-feature.md]
[Create todo list with 5 tasks]

--- Task 1: Create User model ---
[Dispatch implementer subagent]
  Implementer: "Should email be unique?"
  You: "Yes, email must be unique"
  Implementer: Implemented, 3/3 tests passing, committed.

[Dispatch spec reviewer]
  Spec reviewer: ✅ PASS — all requirements met

[Dispatch quality reviewer]
  Quality reviewer: ✅ APPROVED — clean code, good tests

[Mark Task 1 complete]

--- Task 2: Password hashing ---
[Dispatch implementer subagent]
  Implementer: No questions, implemented, 5/5 tests passing.

[Dispatch spec reviewer]
  Spec reviewer: ❌ Missing: password strength validation (spec says "min 8 chars")

[Implementer fixes]
  Implementer: Added validation, 7/7 tests passing.

[Dispatch spec reviewer again]
  Spec reviewer: ✅ PASS

[Dispatch quality reviewer]
  Quality reviewer: Important: Magic number 8, extract to constant
  Implementer: Extracted MIN_PASSWORD_LENGTH constant
  Quality reviewer: ✅ APPROVED

[Mark Task 2 complete]

... (continue for all tasks)

[After all tasks: dispatch final integration reviewer]
[Run full test suite: all passing]
[Done!]
```

## Remember

```
Fresh subagent per task
Two-stage review every time
Spec compliance FIRST
Code quality SECOND
Never skip reviews
Catch issues early
```

**Quality is not an accident. It's the result of systematic process.**
