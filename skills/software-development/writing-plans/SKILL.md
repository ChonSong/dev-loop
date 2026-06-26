---
name: writing-plans
description: "Write implementation plans: bite-sized tasks, paths, code."
version: 1.1.0
author: Hermes Agent (adapted from obra/superpowers)
license: MIT
metadata:
  hermes:
    tags: [planning, design, implementation, workflow, documentation]
    related_skills: [subagent-driven-development, test-driven-development, requesting-code-review]
---

# Writing Implementation Plans

## Overview

Write comprehensive implementation plans assuming the implementer has zero context for the codebase and questionable taste. Document everything they need: which files to touch, complete code, testing commands, docs to check, how to verify. Give them bite-sized tasks. DRY. YAGNI. TDD. Frequent commits.

Assume the implementer is a skilled developer but knows almost nothing about the toolset or problem domain. Assume they don't know good test design very well.

**Core principle:** A good plan makes implementation obvious. If someone has to guess, the plan is incomplete.

## When to Use

**Always use before:**
- Implementing multi-step features
- Breaking down complex requirements
- Delegating to subagents via subagent-driven-development

**Don't skip when:**
- Feature seems simple (assumptions cause bugs)
- You plan to implement it yourself (future you needs guidance)
- Working alone (documentation matters)

## Bite-Sized Task Granularity

**Each task = 2-5 minutes of focused work.**

Every step is one action:
- "Write the failing test" — step
- "Run it to make sure it fails" — step
- "Implement the minimal code to make the test pass" — step
- "Run the tests and make sure they pass" — step
- "Commit" — step

**Too big:**
```markdown
### Task 1: Build authentication system
[50 lines of code across 5 files]
```

**Right size:**
```markdown
### Task 1: Create User model with email field
[10 lines, 1 file]

### Task 2: Add password hash field to User
[8 lines, 1 file]

### Task 3: Create password hashing utility
[15 lines, 1 file]
```

## Plan Document Structure

### Header (Required)

Every plan MUST start with:

```markdown
# [Feature Name] Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

---
```

### Task Structure

Each task follows this format:

````markdown
### Task N: [Descriptive Name]

**Objective:** What this task accomplishes (one sentence)

**Files:**
- Create: `exact/path/to/new_file.py`
- Modify: `exact/path/to/existing.py:45-67` (line numbers if known)
- Test: `tests/path/to/test_file.py`

**Step 1: Write failing test**

```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

**Step 2: Run test to verify failure**

Run: `pytest tests/path/test.py::test_specific_behavior -v`
Expected: FAIL — "function not defined"

**Step 3: Write minimal implementation**

```python
def function(input):
    return expected
```

**Step 4: Run test to verify pass**

Run: `pytest tests/path/test.py::test_specific_behavior -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
```
````

## Writing Process

### Step 1: Understand Requirements

Read and understand:
- Feature requirements
- Design documents or user description
- Acceptance criteria
- Constraints

**Planning before building — user preference:** When a design or spec is presented, focus on PLANNING first. Do NOT jump to implementation. Walk the design tree, resolve dependencies, provide recommendations. Only build after shared understanding is reached. If the user says "lets focus on planning now", stop all implementation work and switch to planning mode. This prevents building on wrong assumptions and ensures architectural decisions are deliberate.

**Design-tree interrogation pattern:** For complex or ambiguous requests, walk the design tree before planning. Question relentlessly — scope, format, tech choices, edge cases, dependencies between decisions. Present one decision at a time with your recommended answer. Resolve dependencies between decisions one-by-one. If a question can be answered by exploring codebases, do that before asking. This prevents building a plan on wrong assumptions.

**Repo-grounded questioning:** When a spec references specific repos (e.g., "use `google/adk-go` for agent patterns"), explore those repos first — check their actual file structure, dependencies, API patterns, and whether they match the spec's claims. Only then ask questions. Example: "The spec says use `google/adk-go` but I checked — it's an agent SDK with `gorilla/mux`, not a WebSocket server framework. Should we still use it or just reference its patterns?" This prevents asking questions that could be answered by 2 minutes of repo exploration.

**Spec-to-reality validation:** Specs often make architectural claims about referenced repos that are wrong or outdated. Always verify:
- **Dependencies**: Check `go.mod`, `package.json`, `requirements.txt` — don't trust the spec's claims about what a repo uses.
- **Entry points**: Check actual main files, server scripts, API endpoints — the spec may describe a subprocess model when the repo ships a full HTTP server.
- **Protocol details**: If the spec says "Opus stream via stdio pipe" but the repo has a WebSocket server with a binary protocol, the spec is wrong. Report the discrepancy and adapt.
- Example: A spec claimed Fun-Audio-Chat was a subprocess with stdio bridge. Reality: it ships `web_demo/server/server.py` — an aiohttp WebSocket server with a custom binary protocol (HANDSHAKE/AUDIO/TEXT/CONTROL messages on port 11235). The bridge design had to change from "spawn + pipe" to "WebSocket relay".

### Step 2: Explore the Codebase

Use Hermes tools to understand the project:

```python
# Understand project structure
search_files("*.py", target="files", path="src/")

# Look at similar features
search_files("similar_pattern", path="src/", file_glob="*.py")

# Check existing tests
search_files("*.py", target="files", path="tests/")

# Read key files
read_file("src/app.py")
```

### Step 3: Design Approach

Decide:
- Architecture pattern
- File organization
- Dependencies needed
- Testing strategy

**E2E testing strategy for local dev tools:**
When planning Playwright/E2E tests for internal dev tools (dashboards, IDEs, admin panels — not consumer websites), the user prefers:
- **Single browser (Chromium)** — drop Firefox/WebKit/Mobile matrix. This is a local tool, not a public website. Cross-browser compatibility is not the bottleneck.
- **Deep complex workflows over breadth** — invest in multi-step scenarios that exercise the full stack end-to-end rather than shallow tests across many browsers.
- **Real user scenarios** — tests should mirror actual workflows: open file → edit → save → reopen → verify persistence, not just "click opens file."
- **Chaos/resilience coverage** — server death, network throttling, WS floods, concurrent sessions. These matter more than browser compatibility for dev tools.
- Example: Instead of 6 functional tests × 4 browsers = 24 runs, prefer 2 functional + 5 workflow + 4 chaos + 3 a11y + 2 visual + 3 perf = 19 focused tests on one browser.

**When to use cross-browser matrix:** Only for consumer-facing web apps where the user explicitly requests it, or when the product must work across browsers by design. Default to Chromium-only for internal tools.

### Step 4: Write Tasks

Create tasks in order:
1. Setup/infrastructure
2. Core functionality (TDD for each)
3. Edge cases
4. Integration
5. Cleanup/documentation

### Step 5: Add Complete Details

For each task, include:
- **Exact file paths** (not "the config file" but `src/config/settings.py`)
- **Complete code examples** (not "add validation" but the actual code)
- **Exact commands** with expected output
- **Verification steps** that prove the task works

### Step 6: Review the Plan

Check:
- [ ] Tasks are sequential and logical
- [ ] Each task is bite-sized (2-5 min)
- [ ] File paths are exact
- [ ] Code examples are complete (copy-pasteable)
- [ ] Commands are exact with expected output
- [ ] No missing context
- [ ] DRY, YAGNI, TDD principles applied

### Step 7: Save the Plan

```bash
mkdir -p docs/plans
# Save plan to docs/plans/YYYY-MM-DD-feature-name.md
git add docs/plans/
git commit -m "docs: add implementation plan for [feature]"
```

## Principles

### DRY (Don't Repeat Yourself)

**Bad:** Copy-paste validation in 3 places
**Good:** Extract validation function, use everywhere

### YAGNI (You Aren't Gonna Need It)

**Bad:** Add "flexibility" for future requirements
**Good:** Implement only what's needed now

```python
# Bad — YAGNI violation
class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email
        self.preferences = {}  # Not needed yet!
        self.metadata = {}     # Not needed yet!

# Good — YAGNI
class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email
```

### TDD (Test-Driven Development)

Every task that produces code should include the full TDD cycle:
1. Write failing test
2. Run to verify failure
3. Write minimal code
4. Run to verify pass

See `test-driven-development` skill for details.

### Frequent Commits

Commit after every task:
```bash
git add [files]
git commit -m "type: description"
```

## Common Mistakes

### Vague Tasks

**Bad:** "Add authentication"
**Good:** "Create User model with email and password_hash fields"

### Incomplete Code

**Bad:** "Step 1: Add validation function"
**Good:** "Step 1: Add validation function" followed by the complete function code

### Missing Verification

**Bad:** "Step 3: Test it works"
**Good:** "Step 3: Run `pytest tests/test_auth.py -v`, expected: 3 passed"

### Missing File Paths

**Bad:** "Create the model file"
**Good:** "Create: `src/models/user.py`"

### Asking Before Investigating

**Bad:** "Which repos are the inspiration ones?" — when the user said "incorporate features from all our inspiration repositories" without listing them. The user assumes you know which repos they mean based on shared context.

**Good:** Investigate first. Search session history, check workspace memory, look at what repos exist in ~/.hermes/. List your candidates: "I think you mean: hermes-workspace (outsourc-e), features-list (ChonSong/features-list), agent-os, and hermes-webui — is that right?" Only ask for confirmation after you've done the homework.

**Rule:** If the user references something ("our inspiration repositories", "the kanban board", "that feature") and it isn't immediately obvious from current context, session_search + filesystem investigation comes before asking. Present your best guess with evidence, then confirm.

### Skipping Self-Contained Design Check

**Bad:** Planning includes "run the onboarding wizard" or "user must install X externally" when the user has specified self-contained packaging.

**Good:** When the user says "no wizard or external dependencies required other than Docker" — honor that as a hard constraint. Don't plan installer steps, don't plan dependency on external services beyond Docker, don't plan first-run wizards. The system is self-contained.

## Common Ambiguities

### "Inspiration repositories" without a list

When the user says "incorporate them from all our inspiration Repositories" but does NOT provide a list, they are relying on shared context you should be able to reconstruct. Do NOT plan until you have named the repos and confirmed.

**Recovery sequence:**
1. session_search for prior mentions of "inspiration" or "features-list" or specific repo names
2. Check ~/.hermes/ for cloned repos
3. Check features-list/README.md (already has the catalog)
4. Present your candidate list for confirmation
5. Only then proceed with planning

### "You should know this" assumption

The user often assumes you know what they mean based on prior conversations. "Are all its features covered in Hermes workspace?" — they're testing whether you know the relationship between hermes-webui and hermes-workspace. The correct response is to investigate and answer, not ask for clarification.

**Answer your own questions before asking.** If you can find the answer by reading files, searching history, or checking the filesystem — do that first. Only ask when you've exhausted your ability to find the answer.

## Execution Handoff

After saving the plan, offer the execution approach:

**"Plan complete and saved. Ready to execute using subagent-driven-development — I'll dispatch a fresh subagent per task with two-stage review (spec compliance then code quality). Shall I proceed?"**

When executing, use the `subagent-driven-development` skill:
- Fresh `delegate_task` per task with full context
- Spec compliance review after each task
- Code quality review after spec passes
- Proceed only when both reviews approve

## Remember

```
Bite-sized tasks (2-5 min each)
Exact file paths
Complete code (copy-pasteable)
Exact commands with expected output
Verification steps
DRY, YAGNI, TDD
Frequent commits
```

**A good plan makes implementation obvious.**

## References

- `references/repo-documentation-standard.md` — AGENTS.md pattern, README structure, MIGRATION.md template for AI-agent-optimized repo docs
- `references/fun-audio-chat-architecture.md` — Fun-Audio-Chat server architecture, binary protocol, GPU requirements, and bridge design patterns (verified against actual repo code)
- `references/spec-to-monorepo-workflow.md` — Workflow for taking a spec to a working monorepo: grounding, decision locking, incremental build, push discipline
- `references/hermes-knowledge-base-build.md` — Build pattern for Hermes ecosystem knowledge bases: 6-dimension scope confirmation, D3 graph gotchas, GitHub Pages path gotchas, anti-patterns
