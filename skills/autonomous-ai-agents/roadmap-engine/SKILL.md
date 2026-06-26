---
name: roadmap-engine
description: "Roadmap Autonomy Engine — long-horizon autonomous planning and execution system. Runs nightly: Phase 1 research (clone/scan/revise roadmap.json), Phase 2 execute (test/code/research/review/browser tasks until 14:00 UTC), Phase 3 report (narrative + Telegram critical issues)."
---

# Roadmap Autonomy Engine

Long-horizon autonomous planning and execution system. Runs a nightly session cycle that revises a persistent `roadmap.json` (top-down goals + bottom-up discovery), executes tasks across 5 productivity dimensions, and reports to morning briefing.

## Directory Structure

> Scripts live at `/tmp/hermes-sync/scripts/` (see §Running). The read-only mount at `/opt/data/hermes-sync/` is bypassed automatically. ⚠️ Only 3 scripts exist in /tmp — the others were lost in a May 8 cleanup and need to be recovered or rewritten before the engine can use them.

```plaintext
/tmp/hermes-sync/scripts/
├── roadmap_engine.py       # ✅ Main entry point (1126 lines)
├── roadmap.py              # ✅ Data model + roadmap CRUD (429 lines)
└── reporters.py            # ✅ Phase 3 report generator (518 lines)
```

What IS NOT in /tmp (missing since May 8 cleanup — needs to be built or recovered):
- `executor.py` — task execution (was lost, needs rebuild)
- `planner.py` — LLM-driven task planning (was lost)
- `research.py` — Discovery-driven idea generation (was lost)
- `self_improvement.py` — Skill authoring pipeline (was lost)
- `learnings_scanner.py` — Scan learnings → rank skill candidates (was lost)
- `skill_author.py` — Author SKILL.md from candidates (was lost)

```
hermes-sync/workspace/plans/
├── roadmap.json           # Single source of truth (seeded with 4 projects)
└── roadmap-history/        # Per-session snapshots
```

## Roadmap Schema (`roadmap.json`)

| Field | Purpose |
|-------|---------|
| `goals[]` | Top-down objectives (set by Sean or reverse-engineered from priorities) |
| `projects[]` | Repos with metadata (name, path, url, status, priority) |
| `tasks[]` | Executable work items: status, priority, effort, skills_required, type |
| `ideas[]` | Voted on; promoted to tasks at 3+ votes |
| `learnings[]` | Findings that persist across sessions |
| `blockers[]` | Known external dependencies |
| `activity_log[]` | Per-session history |

## Task Types (Executor — embedded in roadmap_engine.py)

| Type | Status | Approach |
|------|--------|----------|
| `test` | ✅ Fixed 2026-05-29 | `_execute_test()` now scaffolds test frameworks, sets PYTHONPATH=src, detects package.json in frontend/ subdirectories. See Fix A below. |
| `code` | ⚠️ Buggy | TDD cycle inlined; `_execute_code()` has no preflight check for `local_path` existence before running ruff lint gate — missing dirs cause silent false-positive lint failures. Fix 4 not yet applied to the inlined executor. |
| `research` | ✅ Working | Spawn hermes chat with web toolset; findings saved to plans/research-* |
| `browser` | ✅ Working | Spawn hermes chat -t browser for web automation tasks |
| `review` | ✅ Working | Spawn hermes chat; review saved to plans/review-* |

> All task execution is inlined in `roadmap_engine.py` directly — no separate `executor.py`. `_execute_code()`, `_execute_test()`, `_execute_research()`, `_execute_browser()`, `_execute_review()` handle their respective types.

## Phase Cycle

```
Phase 1 RESEARCH (30-60 min):
  Clone/pull repos → scan TODOs/FIXMEs → GitHub issues → CI failures
  → self-improvement scan (learnings → high-priority skill candidates)
  → LLM planner revises roadmap.json → snapshot to roadmap-history/
  ✅ Working (as of 2026-05-24)

Phase 2 EXECUTE (until 14:00 UTC / midnight Sydney):
  Load top tasks → verify preconditions → execute via appropriate executor
  → record results → update roadmap → commit hermes-sync changes
  ⚠️ BLOCKED — lint gate false-positive on missing directory (Fix 4 needed)

Phase 3 REPORT (15-30 min):
  Generate narrative report → critical issues to Telegram → rest to morning briefing
  → push roadmap.json + report to git
  ✅ Working (as of 2026-05-24)
```

6. **Read-only hermes-sync filesystem** — `/opt/data/hermes-sync` is mounted read-only in the cron container. All writable operations (snapshot, report, git push, clone) fail. **WORKAROUND** ✅ — patches to `WORKSPACE_TMP = Path("/tmp/hermes-sync")` redirect all writable paths; read-only source paths (roadmap.json, existing repos) still use the real `/opt/data/hermes-sync` paths. Applied to `roadmap_engine.py`, `roadmap.py`, `reporter.py`. See `references/read-only-fs-workaround.md`.

7. **Openclaw monorepo path mismatch — proj-005 needs fixing before use** — `proj-005` is defined with `local_path: projects/openclaw` and `repo: ChonSong/agent-os`. The literal repo `ChonSong/openclaw` does not exist on GitHub. All 9 `task-openclaw-*` tasks fail at the lint gate because `ruff check` runs against a non-existent directory. Fix:
   ```bash
   cd /tmp/hermes-sync && git clone https://github.com/ChonSong/agent-os.git projects/openclaw
   ```
   Or update `roadmap.json` to point `proj-005.local_path` at the existing `projects/agent-os`.

8. **hermes binary path** — `/opt/hermes/.venv/bin/hermes` (correct, works from container). NOT `/home/sean/.hermes/hermes-sync/.venv/bin/hermes` (old venv location). The venv lives under `/opt/hermes/` not `/opt/data/hermes-sync/`.

9. **Self-improvement script missing** — `scripts/self_improvement.py` was deleted in the 2026-05-08 auto-sync cleanup. Phase 1 step `_run_self_improvement()` prints `"Script not found, skipping"` and exits gracefully — but the improvement loop is silently broken. See `self-improvement-engine` skill.

## Self-Improvement Loop (Phase 1)

Phase 1 now closes the loop on its own learnings — errors and corrections get turned into reusable skills automatically.

### Pipeline

```
Phase 1
  └── _run_self_improvement()
        ├── learnings_scanner.py   → skill_candidates.json (scored + ranked)
        └── skill_author.py        → SKILL.md authored → committed to hermes-sync
```

### Scoring formula

```
skill_score = priority_weight × area_multiplier × type_weight × recurrency × recency
```

| Signal | Effect |
|--------|--------|
| High priority (priority=high) | ×1.5 |
| Infrastructure area | ×1.3 |
| Implementation error type | ×1.2 |
| Recurring 3+ times | ×1.5 (recurrency multiplier) |
| Recent (<7 days old) | ×1.2 |

**Authoring threshold:** `score ≥ 50` OR `recurrences ≥ 3`

### What triggers a skill

| Candidate source | Example |
|-----------------|---------|
| `hermes-sync/workspace/plans/roadmap-learnings/` | Error patterns, fix recipes |
| `memory/` (parsed via session_search) | Repeated corrections or workflow issues |
| `skills/*/SKILL.md` (audit) | Missing coverage, gaps in existing skills |
| `hermes-sync/scripts/*` log traces | Patterns in stderr/stdout |

### What gets authored

- SKILL.md with: title, trigger condition, numbered steps, pitfalls
- References link back to the candidate ID that triggered it (full traceability)
- Committed to `hermes-sync/skills/<category>/<skill-name>/`
- Skill author hooks into `skills/` tool so future sessions load it automatically

### Skill lifecycle

```
detected (score < threshold) → tracked (score grows with recurrence)
    → authored (threshold met) → loaded (next applicable session)
    → used → corrected → tracked again (updated via patch)
```

### Key files

| File | Role |
|------|------|
| `scripts/self_improvement.py` | Orchestrator: runs scanner → skill_author pipeline |
| `scripts/learnings_scanner.py` | Scans 4 sources, scores candidates, writes `skill_candidates.json` |
| `scripts/skill_author.py` | Reads candidates, researches, authors SKILL.md, commits |

## Immediate Fixes (Highest Leverage)

### Fix A: `_execute_test()` now scaffolds + sets PYTHONPATH ✅ APPLIED 2026-05-29

**Previously:** Both `task-001` and `task-004` failed with "No test framework detected".
The executor detected missing/misconfigured frameworks but returned blocked instead of fixing.

**Fixed 2026-05-29:** Complete rewrite of `_execute_test()` and supporting code:
- **New `_detect_test_framework(local)` helper** — checks pyproject.toml, pytest.ini, setup.cfg, package.json (root + `frontend/`, `client/`, `web/`), go.mod
- Returns `(framework: str, workdir: Path, extra_env: dict)` — handles everything-dashboard's `frontend/` subdir
- **`run()` now accepts `extra_env=None`** — passes `PYTHONPATH=src` for Python projects (fixes repo-transmute ModuleNotFoundError)
- **Scaffolds test dir** — when pytest config exists but no `tests/` or `test/` directory, creates `tests/test_smoke.py`
- **Vitest output parsing** — regex for `Tests N passed` format
- **Better error messages** — when tests have tracebacks, includes first 500 chars of output
- **Support for Go projects** — runs `go test ./...`

**Result:** task-001 (172 tests) and task-004 (4 tests) both now pass. Executor no longer deadlocks.

### Fix B: Deduplicate learnings before adding to roadmap

617 learnings with massive duplication on 2026-05-27. The same TODO/FIXME comment from the same
file+lineno appears 3-4× because `hermes-agent` is scanned as both `proj-003` and as the engine's
own code. The deduplication logic (keyed on `{project_id, file, lineno}`) only works within a
single scan pass — it fails across multiple passes in the same session.

Fix: maintain a session-wide `seen_findings = set()` deduplication dict before any
`roadmap.add_learning()` call, across ALL scan passes in Phase 1.

### Fix C: Deduplicate ideas by title before persisting

"Add test suite for openclaw monorepo" appeared 4× in the 2026-05-27 report. The coverage-gap
scanner detects the same gap repeatedly across multiple scan passes.

Fix: before `roadmap.add_idea()`, check if an idea with the same `title` already exists in the
roadmap's `ideas[]` list. Deduplicate by `title` field.

### Fix D: Duration = 0 minutes (datetime timezone)

Session `sess-2026-05-26-8e6f10` reported 0.0h duration. Likely a UTC/AEDT timezone mismatch in
`datetime.now()` vs the stored ISO timestamps. Use UTC consistently for elapsed-time calculations.

## Short-Term Improvements (This Week)

- **Docker isolation per project** — run code/test tasks in containers (python:3.11 for repo-transmute, node:20 for everything-dashboard)
- **CI signal reader in Phase 1** — read GitHub Actions API for last 5 workflow runs, create tasks from failures automatically
- **Multi-source research** — research tasks should do: web search + file analysis + GitHub issues + synthesis (not single hermes chat call)

## Medium-Term (CI/CD Pipeline Integration)

- Add GHA `path:` filters per project in hermes-sync
- Add `semantic-release` with conventional commits (`feat:`, `fix:`)
- Add quality gate job: lint → test → type-check → audit
- Wire `on.check_run` webhook to update `roadmap.json` with CI results
- Consider Nx/Turborepo monorepo for shared tooling across projects

## Key Implementation Facts

- **Hermes binary:** `/opt/hermes/.venv/bin/hermes` (correct, works from container). NOT `/home/sean/.hermes/hermes-sync/.venv/bin/hermes` (old venv location). The venv lives under `/opt/hermes/` not `/opt/data/hermes-sync/`.
- **Python in venv:** `HERMES_SYNC / ".venv/bin/python"` — use this for running pip/py scripts in the hermes-sync venv context
- **ruff:** installed in venv (v0.15.13) — runs with `ruff check --fix --unsafe-fixes .` for auto-fix mode
- **workspace/projects/ ⚠️ cross-mount shadowing** — `/tmp/hermes-sync/projects/` and `/opt/data/hermes-sync/projects/` are NOT the same. Repos cloned at `/opt/data/hermes-sync/projects/` do not automatically appear at `/tmp/hermes-sync/projects/`. This causes "Repo not found" on projects that exist but live on the read-only mount. Always clone into `/tmp/hermes-sync/projects/` explicitly when running from the container.
- **Available toolsets:** `browser`, `cronjob`, `file`, `session_search`, `skills`, `terminal`, `web`
- **GitHub token:** `~/.netrc` with PAT — handled natively via urllib
- **xvfb-run:** `/usr/bin/xvfb-run` (for headless GUI tasks)
- **Browser:** Use `browser-agent` skill — **do NOT install standalone Playwright/Selenium**
- **Hermes runs in a container:** PID 1 is `/usr/bin/tini -g -- /opt/hermes/docker/entrypoint.sh gateway run` — hermes-agent itself runs inside a Docker container (Debian/Arch host). This has implications:
  - Docker-in-Docker does NOT work — the container lacks `CAP_NET_ADMIN` (iptables fails with "permission denied")
  - `dockerd` is not installed in the container — only the `docker` CLI is present
  - Docker socket is not mounted in — no access to host Docker daemon via `/var/run/docker.sock`
  - Deployments requiring Docker must use **GitHub Actions SSH deploy** pattern (build in GHA → SSH to server → `docker compose up`)
  - Host Docker API sometimes reachable at `http://172.17.0.1:2375` if host has Docker exposed, but often firewalled

## Agent-OS Deployment (SSH Deploy Pattern)

When deploying agent-os from hermes-agent (which can't run Docker directly):

1. **Generate ED25519 deploy key:** `ssh-keygen -t ed25519 -C "github-actions@agent-os" -f /tmp/github_actions_deploy -N ""`
2. **Add public key to server:** `echo "$(cat /tmp/github_actions_deploy.pub)" >> ~/.ssh/authorized_keys` on target server
3. **Store private key as GitHub secret:** `gh secret set DEPLOY_SSH_KEY -R ChonSong/agent-os < /tmp/github_actions_deploy`
4. **Store server IP as secret:** `gh secret set DEPLOY_HOST -R ChonSong/agent-os`
5. **Workflow lives in:** `.github/workflows/build-and-deploy.yml` (push to main) and `.github/workflows/ssh-deploy.yml` (manual dispatch)

Workflow uses `webfactory/ssh-agent@v0.8.0` to inject the SSH key, then runs:
```bash
ssh "${USER}@${HOST}" "cd /opt/data/hermes-sync/projects/agent-os && docker compose pull && docker compose up -d"
```

**agent-os repos:** `ChonSong/agent-os` (monorepo), `ChonSong/nanobot` (fork of HKUDS/nanobot), `ChonSong/hermes-agent`
**Images:** `ghcr.io/chonsong/agent-os-dashboard`, `ghcr.io/chonsong/agent-os-nanobot`
**Dashboard port:** 9119

## Known Issues ✅ RESOLVABLE — May 24 Update

### Scripts Location

> **2026-05-24:** Scripts DO exist on disk — at `/tmp/hermes-sync/scripts/`, NOT at `/opt/data/hermes-sync/`.
> The read-only mount `/opt/data/hermes-sync/` is bypassed by running from `/tmp/hermes-sync/` (pre-configured).
> All `❌ MISSING` labels below are stale — the files exist in `/tmp/hermes-sync/scripts/`.

| File | Status |
|------|--------|
| `scripts/roadmap_engine.py` | ✅ In `/tmp/hermes-sync/scripts/` (1126 lines) |
| `scripts/roadmap.py` | ✅ In `/tmp/hermes-sync/scripts/` (429 lines) |
| `scripts/reporters.py` | ✅ In `/tmp/hermes-sync/scripts/` (518 lines) |
| `scripts/hermes-sync-backup.py` | ✅ In `/tmp/hermes-sync/scripts/` |
| `scripts/planner.py` | ❌ Missing — NOT in `/tmp`, inlined into roadmap_engine.py |
| `scripts/executor.py` | ❌ Missing — NOT in `/tmp`, inlined into roadmap_engine.py |
| `scripts/research.py` | ❌ Missing — NOT in `/tmp`, inlined into roadmap_engine.py |
| `scripts/self_improvement.py` | ❌ Deleted May 8 auto-sync cleanup |
| `scripts/learnings_scanner.py` | ❌ Missing — NOT in `/tmp` |
| `scripts/skill_author.py` | ❌ Missing — NOT in `/tmp` |

### Running the Engine (Updated)

```bash
# CORRECT — run from /tmp/hermes-sync
cd /tmp/hermes-sync && python3 scripts/roadmap_engine.py --phase all

# WRONG — /opt/data/hermes-sync is read-only mount
cd /opt/data/hermes-sync && python3 scripts/roadmap_engine.py  # fails
```

The engine is pre-configured to redirect writable outputs to `/tmp/hermes-sync/` while reading sources from `/opt/data/hermes-sync/`. No manual workaround needed — the directory `/tmp/hermes-sync/` already exists and is populated.

### Openclaw Monorepo Not Cloned

`proj-005` (`ChonSong/openclaw`) was never cloned. All 9 `task-openclaw-*` tasks fail immediately at the lint gate with:
```
[Errno 2] No such file or directory: PosixPath('/tmp/hermes-sync/projects/openclaw')
```
The lint gate checks for the openclaw repo directory before any patch is applied. **Fix required:** clone the correct repo or re-point the project path:
   ```bash
   cd /tmp/hermes-sync && git clone https://github.com/ChonSong/agent-os.git projects/openclaw
   ```
   The `repo` field in roadmap.json correctly reads `ChonSong/agent-os` — only the clone step uses the wrong name.

### Read-only filesystem

`/opt/data/hermes-sync` is mounted read-only in the cron container. See `references/read-only-fs-workaround.md` for the working approach (WORKSPACE_TMP redirect pattern). All writable ops (snapshots, reports, git push, clone/fetch) fail on the mount.

## Running

```bash
# From container cron (correct path)
cd /tmp/hermes-sync && python3 scripts/roadmap_engine.py --phase all

# From host SSH (also works)
ssh -i /home/hermeswebui/.hermes/container_key sean@172.19.0.1 \
  "cd /tmp/hermes-sync && python3 scripts/roadmap_engine.py --phase all"

## Execution Environment

**Critical: filesystem must be read-write.** The engine requires both the workspace dir and the hermes-sync root to be writable for:
- `git clone` of target repos into `workspace/projects/`
- `git fetch` / `git pull` on existing checkouts
- `git commit` + `git push` of roadmap updates at end of session

If `/opt/data/hermes-sync` is read-only (common in sandboxed cron environments), the engine detects this at startup and falls back to `/tmp/hermes-sync` as a transit sandbox, syncing back to the ro mount at session end via `hermes-sync-backup.py`. Do NOT run against a ro mount and expect meaningful Phase 2 output — all clone/fetch/push operations will silently fail and Phase 2 will report "0 tasks completed" with no explanation.

**Path resolution order:**
1. `--workdir PATH` argument → sets `WORKSPACE_TMP` (the workspace root used for projects/, plans/, etc.)
2. `HERMES_SYNC` is always `Path("/opt/data/hermes-sync")` and must be writable
3. If `HERMES_SYNC` is ro but `--workdir /tmp` is specified → engine runs in transit mode, syncs via backup script on success

## Common Pitfalls

1. **Read-only mount silently kills execution.** Clone fails, fetch fails, push fails — but the engine prints no error, just skips. Phase 2 ends with "0 tasks completed" and no indication that the filesystem was the cause. Always verify `HERMES_SYNC` is writable before expecting Phase 2 task execution.
2. **Already-completed tasks reported as done.** If "What We Completed" lists tasks with `completed` dates from previous sessions (e.g. 2026-05-01), the executor is including `done` tasks in its result output. Check `roadmap.todo_tasks()` filter — it should exclude `status == "done"` tasks. Also check `_execute_task` result recorder for off-by-one in task state transition logic.
3. **TODO scanner deduplication.** Scanning the same repo twice in one session produces duplicate learnings. The 50-finding cap on `_scan_todos` is per-session total, not per-repo. If scanning multiple projects, ensure findings are deduplicated by `{project_id, file, lineno}` before adding to roadmap.
4. **self_improvement.py script deleted.** The `_run_self_improvement()` call in Phase 1 prints "Script not found, skipping" — the improvement loop is silently broken. Either restore from git commit `9e5982d` or accept that Phase 1 will skip self-improvement until the script is re-authored.
5. **GitHub token not in ~/.netrc.** `_scan_github_issues` silently returns no findings when no token is found. The `~/.netrc` lookup looks for `password` field on the `github.com` machine entry. Without it, GitHub issue scanning contributes nothing to Phase 1.
6. **Task selection has no precondition check.** The engine picks tasks based on priority/effort but never verifies `local_path` exists or is a git repo before scheduling. If a repo wasn't cloned, the task will fail at execution time. Add a `verify_task_preconditions()` check before Phase 2 task dispatch.

8. **TODO/FIXME scan dedup failure inflates learnings 10x.** `_scan_todos` deduplicates by `{project_id, file, lineno}` but only within a single scan pass. When the same repo is scanned multiple times in one session (e.g., once in `_scan_todos` and once in `_check_coverage_gaps`), the same finding from the same file+lineno is added twice. Over a full Phase 1 run this can produce 350+ entries instead of ~35. Fix: maintain a session-wide deduplication set (or dict keyed on project_id+file+lineno) across all scan passes before adding findings to the roadmap's `learnings[]` list.

9. **Ideas table gets duplicate rows from repeated coverage-gap scans.** When `_check_coverage_gaps` runs across multiple projects in one session, identical ideas ("Add test suite for openclaw monorepo") can be added multiple times if the same gap is detected across multiple passes. Fix: deduplicate ideas by `content` field before persisting, or check for existence before `roadmap.add_idea()`.

10. **Stale task results from prior sessions pollute "What We Completed".** The "What We Completed" section in Phase 3 reports includes tasks whose `result` field was set by a previous session's failed/blocked run. These are not tasks completed THIS session — they're historical artifacts. Fix: filter `roadmap.completed_tasks()` to only include tasks with a `completed` timestamp from the current session, or add a `session_id` field to task results and filter on that.

8. **Clone destination path uses `HERMES_SYNC` (read-only mount).** The `git clone` call in Phase 1 uses `cwd=HERMES_SYNC / "workspace" / "projects"` — the read-only mount. In the cron container, all clones silently fail. The fix (applied 2026-05-25): use `cwd=WORKSPACE_TMP / "projects"` for clone operations. This affects all Phase 1 clone and fetch calls that use a `cwd` parameter. The skill's WORKSPACE_TMP workaround handles outputs but not the clone `cwd` — both need fixing.

9. **"No test framework detected" is unactionable.** When `_execute_test()` can't find a framework, it returns this generic message without listing what it checked (e.g., `pytest.ini`, `pyproject.toml`, `package.json`, `jest.config.ts`, `vitest.config.ts`). Helpful error should show which paths were checked and what files exist in the repo root.

## Verification Checklist

- [ ] `HERMES_SYNC` path exists and is writable (run `test -w /opt/data/hermes-sync`)
- [ ] `workspace/projects/` exists or can be created
- [ ] GitHub token present in `~/.netrc` (for issue scanning)
- [ ] `scripts/self_improvement.py` exists (for self-improvement loop) or accept skip
- [ ] `--phase all` runs all three phases end-to-end
- [ ] Report appears in `workspace/plans/nightly-reports/report-YYYY-MM-DD.md`

---

## References

See `references/read-only-fs-workaround.md` for the read-only filesystem workaround.
See `references/implementation-notes.md` for the May 18 implementation fixes (hermes paths, ruff, symlink).
See `references/quality-gap-analysis.md` for the quality gap analysis and 8-step improvement roadmap.
See `references/session-2026-05-24.md` for the May 24 session: openclaw repo never cloned root cause and fix.
See `references/session-2026-05-23.md` for the May 23 session: lint gate false-positive + cross-mount path mismatch.
See `references/session-2026-05-25.md` for the May 25 session: read-only filesystem root cause, Phase 2 precondition gap, and report bug.
See `references/session-2026-05-26.md` for the May 26 session: clone cwd fix, execute_test wrong status, stale task results, repo-transmute empty repo.
See `references/session-2026-05-27.md` for the May 27 session: `_execute_test()` reports but doesn't scaffold, 617 learnings deduplication failure, duplicate ideas, duration=0 bug, and actual script inventory correcting the scripts table.
See `references/self-improvement-pipeline.md` for the self-improvement loop.
