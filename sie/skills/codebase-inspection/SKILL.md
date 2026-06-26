---
name: codebase-inspection
description: "Inspect and assess codebases: quantitative (pygount LOC/language metrics) + qualitative (repo triage, state assessment, capability-constrained redesign)."
version: 2.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [LOC, Code Analysis, pygount, Codebase, Metrics, Repository, Triage, Assessment]
    related_skills: [github-repo-management, repo-discovery]
prerequisites:
  commands: [pygount]
---

# Codebase Inspection & Assessment

Two modes: **quantitative** (LOC, language breakdown via pygount) and **qualitative** (repo triage, state assessment, capability-constrained redesign).

---

## Part 1: Repo Triage (Qualitative Assessment)

When asked to "review" or "assess" a repository, follow this multi-source discovery protocol before giving any verdict.

### Multi-Source Discovery Protocol

Do NOT assume the repo's state from a single source. Check all of these:

| Source | What to Check | Why |
|--------|---------------|-----|
| **Local clone** | `find /home /workspace -name ".git" -path "*/repo-name*" 2>/dev/null` | The repo may be cloned locally but not in the expected location |
| **Archived copies** | `find /workspace/archive /home -maxdepth 4 -name "repo-name" -type d` | Workspace reorganization may have moved it |
| **GitHub API** | `curl -sL "https://api.github.com/repos/Org/repo-name/contents"` | Shows current contents, file sizes, and directory structure |
| **Session history** | `session_search(query="repo-name keywords")` | Past sessions may have context: blockers, decisions, running services, resolved issues |
| **Running services** | Check ports listed in the repo's configuration | Dashboard, API, DB — may still be running even if code isn't cloned locally |
| **Original plan/docs** | Compare against PLAN.md, PROGRESS.md, README status tables | Stale docs reveal stalled phases and blocker patterns |
| **External dependencies** | Check if the design references repos/APIs/keys that don't exist | The most common disconnect: plan assumes resources that were never obtained |

### Example: Repo Triage Flow

```
1. Check local clone          → NOT FOUND
2. Check archived copies      → FOUND at /workspace/archive/repo/streamlit_onetag/
3. Check GitHub API           → FOUND: full repo with 30+ files, 7 dirs
4. Search session history     → FOUND: 3 sessions, known blockers (API key, repo URL)
5. Check running services     → NOT RUNNING: ports return 000
6. Compare against PLAN.md    → Day 0 complete, all other phases "not started"
7. Check external deps        → Engine repo URL unknown, API key unavailable

Conclusion: Repo exists on GitHub, stalled at Day 0, 2 unresolved blockers.
```

### Capability-Constrained Assessment

When a project's original design depends on resources that don't exist (unavailable API keys, unreachable external repos, missing services), DO NOT assume the project is dead. Instead:

1. **Identify what IS available** — data files, schemas, working code, infrastructure that's running
2. **Separate methodology from implementation** — the pattern/approach may work with a different implementation
3. **Re-ground the core concept** — strip the project to its essential methodology and rebuild around available assets
4. **Update naming and descriptions** — stale docs that describe the original vision will confuse future reads
5. **Present the fork** — "Here's the original plan, here's what's actually available, here's the redesigned approach"

### Stale-Doc Detection

When a repo has a PLAN.md, PROGRESS.md, or README with a status table:

- Cross-reference actual file timestamps against the plan timeline
- Cross-reference dates in daily logs against the current date
- If phases are marked "not started" but the timeline has elapsed, note the slippage
- If the plan references external repos, APIs, or keys that don't exist locally, flag as unresolved blockers

### Stating Blocker State

Present blockers in a table format with status, impact, and what's needed:

| Blocker | Status | Impact | Action |
|---------|--------|--------|--------|
| External repo URL | 🔴 Blocking | Can't clone/setup | Confirm org name |
| API key | 🔴 Blocking | Can't run experiments | Request from team |

If ALL phases beyond setup are blocked by the same 1-2 issues, say so explicitly.

---

## Part 2: Quantitative Analysis (pygount)

Analyze repositories for lines of code, language breakdown, file counts, and code-vs-comment ratios using `pygount`.

### When to Use

- User asks for LOC (lines of code) count
- User wants a language breakdown of a repo
- User asks about codebase size or composition
- User wants code-vs-comment ratios
- General "how big is this repo" questions

### Prerequisites

```bash
pip install --break-system-packages pygount 2>/dev/null || pip install pygount
```

### 1. Basic Summary (Most Common)

Get a full language breakdown with file counts, code lines, and comment lines:

```bash
cd /path/to/repo
pygount --format=summary \
  --folders-to-skip=".git,node_modules,venv,.venv,__pycache__,.cache,dist,build,.next,.tox,.eggs,*.egg-info" \
  .
```

**IMPORTANT:** Always use `--folders-to-skip` to exclude dependency/build directories, otherwise pygount will crawl them and take a very long time or hang.

### 2. Common Folder Exclusions

Adjust based on the project type:

```bash
# Python projects
--folders-to-skip=".git,venv,.venv,__pycache__,.cache,dist,build,.tox,.eggs,.mypy_cache"

# JavaScript/TypeScript projects
--folders-to-skip=".git,node_modules,dist,build,.next,.cache,.turbo,coverage"

# General catch-all
--folders-to-skip=".git,node_modules,venv,.venv,__pycache__,.cache,dist,build,.next,.tox,vendor,third_party"
```

### 3. Filter by Specific Language

```bash
# Only count Python files
pygount --suffix=py --format=summary .

# Only count Python and YAML
pygount --suffix=py,yaml,yml --format=summary .
```

### 4. Detailed File-by-File Output

```bash
# Default format shows per-file breakdown
pygount --folders-to-skip=".git,node_modules,venv" .

# Sort by code lines (pipe through sort)
pygount --folders-to-skip=".git,node_modules,venv" . | sort -t$'\t' -k1 -nr | head -20
```

### 5. Output Formats

```bash
# Summary table (default recommendation)
pygount --format=summary .

# JSON output for programmatic use
pygount --format=json .

# Pipe-friendly: Language, file count, code, docs, empty, string
pygount --format=summary . 2>/dev/null
```

### 6. Interpreting Results

The summary table columns:
- **Language** — detected programming language
- **Files** — number of files of that language
- **Code** — lines of actual code (executable/declarative)
- **Comment** — lines that are comments or documentation
- **%** — percentage of total

Special pseudo-languages:
- `__empty__` — empty files
- `__binary__` — binary files (images, compiled, etc.)
- `__generated__` — auto-generated files (detected heuristically)
- `__duplicate__` — files with identical content
- `__unknown__` — unrecognized file types

### Pitfalls

1. **Always exclude .git, node_modules, venv** — without `--folders-to-skip`, pygount will crawl everything and may take minutes or hang on large dependency trees.
2. **Markdown shows 0 code lines** — pygount classifies all Markdown content as comments, not code. This is expected behavior.
3. **JSON files show low code counts** — pygount may count JSON lines conservatively. For accurate JSON line counts, use `wc -l` directly.
4. **Large monorepos** — for very large repos, consider using `--suffix` to target specific languages rather than scanning everything.

---

## References

- `references/forrest-plan-triage.md` — Full worked example of the triage protocol applied to the Forrest Plan & Track repo (ChonSong/forrest-plan-and-track)
