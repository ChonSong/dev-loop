# Repo Task Rotation Template (T1-T6)

Concrete, repo-specific alternative to the generic work-continuation pattern. Use when you have verified repo paths, exact test/build commands, and want a deterministic task queue rather than open-ended discovery.

## Structure

```
Task Queue (top of this list that hasn't been done this cycle):
T1 — Run tests and fix ONE failure
T2 — Build + fix warnings
T3 — Lint sweep
T4 — Dependency hygiene
T5 — Remove tracked build artifacts
T6 — Lightweight GitHub PR check
```

Each task has exact commands for the repo type. Pick the top undone task. Execute, verify, commit, log.

## Template Fields Per Repo

```
## R<N> — <Project Name>
- **Path:** <verified absolute path>
- **Stack:** <language, framework>
- **Test cmd:** <exact test command with flags>
- **Lint cmd:** <exact lint command>
- **Format cmd:** <exact format command>
- **Build cmd:** <exact build command>
```

### Go Backend Examples
```yaml
Test:   cd <path>/backend && go test ./... -count=1 -timeout=120s
Build:  cd <path>/backend && go build ./...
Vet:    cd <path>/backend && go vet ./...
Format: cd <path>/backend && gofmt -s -w .
Deps:   cd <path>/backend && go mod tidy && go mod verify
```

### Python Project Examples
```yaml
Test:   <venv>/bin/python -m pytest <paths>
Lint:   <venv>/bin/python -m ruff check .
Format: <venv>/bin/python -m ruff format .
Build:  <venv>/bin/pip install -e .
```

## Verified Repo Definitions

### R1 — hermes-web-computer (HWC)
- **Path:** `/home/hermeswebui/.hermes/hermes-web-computer` (also found at `/opt/data/hermes-web-computer` on some container builds)
- **Stack:** Go 1.26 backend + Svelte 5 frontend
- **Test cmd:** `cd /opt/data/hermes-web-computer/backend && go test ./... -count=1 -timeout=120s`
- **Build cmd:** `cd /opt/data/hermes-web-computer/backend && go build ./...`
- **Vet cmd:** `cd /opt/data/hermes-web-computer/backend && go vet ./...`
- **Format cmd:** `cd /opt/data/hermes-web-computer/backend && find . -path ./.gopath -prune -o -name '*.go' -print | xargs gofmt -s -w`
- **Deps cmd:** `cd /opt/data/hermes-web-computer/backend && go mod tidy && go mod verify`
- **Frontend:** `cd /opt/data/hermes-web-computer/frontend && npm run build 2>/dev/null` (if node_modules/ exists)
- **Last commit:** bd4894e
- **Pitfall — gofmt and .gopath:** `gofmt -s -w .` walks into `.gopath/` (local module cache) and hits permission errors on read-only vendor files. Always exclude `.gopath` with `find . -path ./.gopath -prune`. The backend Go source files are under `backend/`; `cd` into that dir first.
- **Pitfall — Go on PATH:** Go availability varies by container image build. Always `which go` first. Fall back to the toolchain path (see cron-job-patterns SKILL.md §4) if not found.
- **Pitfall — /workspace/ not mounted:** The repo may be at `/home/hermeswebui/.hermes/hermes-web-computer` (auto-continue cron container, 2026-06-11), `/opt/data/hermes-web-computer` (other containers), or `/workspace/hermes-web-computer` (workstation). Always verify with `cd /path && git log --oneline -1 2>/dev/null` before using.

### R2 — gto-wizard-clone (GTO)
- **Path:** `/workspace/gto-wizard-clone`
- **Stack:** Python monorepo (hatchling, requires-python >=3.12) + Node (turborepo)
- **Test cmd:** `cd /workspace/gto-wizard-clone && python -m pytest packages/poker-core/tests -x -q --tb=short`
- **Lint cmd:** `cd /workspace/gto-wizard-clone && python -m ruff check . 2>/dev/null`
- **Format cmd:** `cd /workspace/gto-wizard-clone && python -m ruff format . 2>/dev/null`
- **Test count (2026-06-11):** 368 poker-core tests (full suite may include solver tests on different schedules)
- **Last commit:** 24cafdd

- **Pitfall — ruff E402 structural:** The ruff check shows E402 (module-level import not at top of file) in `apps/solver/cfr/engine.py`, `apps/solver/service.py`, and `apps/api/services/redis_bridge.py`. These are caused by `sys.path.insert(0, ...)` at module level — a deliberate design pattern for standalone module resolution. Do NOT attempt to "fix" by reordering imports; it would break runtime path resolution.
- **Pitfall — Next.js build artifacts tracked in git (sw.js + workbox-*.js):** The files `apps/web/public/sw.js` and `apps/web/public/workbox-*.js` are auto-generated service worker files by Next.js. They contain build-specific hash references (e.g., `rf_BVcDxno85ULBFOLdE1/_buildManifest.js` vs `-EGngIqnjZ5cnIjlMFBl7/_buildManifest.js`) that change on every build. These files should NEVER be git-tracked. If `git status` shows them as modified, the build ran and regenerated them with new hashes.
  - **Fix:** Add to `.gitignore`, then `git rm --cached`:
    ```
    # Next.js build artifacts (service worker)
    apps/web/public/sw.js
    apps/web/public/workbox-*.js
    ```
  - **Verification:** `git status` should no longer show these as modified or untracked.
  - **Why not just revert?** The next build will regenerate them again. Untracking is the only stable fix.
- **Pitfall — test environment:** Requires `.env` for DATABASE_URL. If missing: `echo "DATABASE_URL=sqlite:///tmp/test.db" > .env`
- **Pitfall — repo path migration:** Prior sessions used `/tmp/gto-wizard-clone` (tmpfs, wiped on restart). As of 2026-06-11, the canonical path is `/workspace/gto-wizard-clone` which persists across container restarts. The `/tmp` variant should be considered legacy.

## 24-Hour Skip Window

Each repo+task combo must be logged with a timestamp. Before starting, read the log file at `/opt/data/auto-continue-log.md`:

```
read_file("/opt/data/auto-continue-log.md")
```

If the same `T<N>` on the same repo was done within the last 24 hours, skip it. This prevents redundant T1-T3 runs from being repeated every 30-minute cron cycle when nothing has changed.

If the log file doesn't exist, this is a fresh cycle — all tasks are available.

**Log format:**
```markdown
## <timestamp> UTC — R<N> T<N> (<description>)
- **Repo:** <path>
- **What:** <action taken>
- **Files:** <changed file list>
- **Verified:** <outcome of build/test/verification>
- **Next:** <next task in rotation>
```

**Canonical log path:** `/workspace/data/auto-continue-log.md` (fall back to `/opt/data/auto-continue-log.md` if `/workspace/` is not mounted in the container). This session (2026-06-11) found the log at `/workspace/data/auto-continue-log.md` — the `/workspace/` mount WAS present in this container build.

## Commit Convention

```bash
git -C <repo> add -A && git -C <repo> commit -m "auto: <repo-label> T<N> — <description>"
```

Examples: `auto: HWC T3 — go vet fixes` / `auto: GTO T1 — fix flaky solver test`

## GitHub PR Check (T6)

Safe pattern using curl-to-file (avoids tirith pipe-to-interpreter filter):

```bash
curl -s -o /tmp/gh-pulls.json "https://api.github.com/search/issues?q=repo:<owner>/<repo>+is:open+is:pr"
```
Then read the file with `read_file("/tmp/gh-pulls.json")`. If `total_count > 0`, review the diff. Only comment via API if there's a clear, safe issue (typo, docs, test fix). Never create PRs.

If `total_count` is 0 with `search_type: "lexical"` and no rate-limit headers, the query was valid but found nothing — no action needed. No rate limit check required for unauthenticated searches (60 req/hr limit; at 30-min cron intervals, the limit won't be hit).

## Empty Queue Protocol — All Tasks Done This Cycle

When all T1-T6 tasks for the current repo are already completed in this cycle (per `/opt/data/auto-continue-log.md`):

1. **Check the other repo** — the alternation rule (R1→R2→R1→R2) may have tasks pending on the sibling repo
2. **If both repos fully done** — report `[SILENT]` to suppress delivery, and append a no-op entry to the log so the settled-state detector (cron-job-patterns §10-cycle rule) has a record
3. **Do NOT skip the log update** — even a no-op cycle should be timestamped. Without it, the 24h skip window has no anchor and the next cycle re-scans fresh.

### No-Op Log Entry Format
```markdown
## 2026-06-11 05:32 UTC — R1/R2 all tasks done
- **Repo:** <both>
- **What:** No-op — all T1-T6 tasks already done this cycle
- **Next:** <next repo in rotation>
```

### Pitfall — not finding work doesn't mean the session is done
The agent still owes the user a complete turn. After scanning both repos and finding no work:
1. Output `[SILENT]` as the response payload (this suppresses cron delivery)
2. Write the no-op log entry so the 24h window starts
3. Do NOT return an empty response — every tool call result must be processed and acted upon

## Hard Safety Rules

| ✅ Always safe | ❌ Never |
|---|---|
| Fixing tests, build warnings, lint | Features, auth, credentials |
| Formatting, dep hygiene | Security config, infra |
| Removing tracked build artifacts | Pushing to remotes (local commits only) |
| .gitignore updates | Design decisions |

## Related

- `cron-job-patterns` SKILL.md → "Work-Continuation Pattern (Self-Triage)" section — generic pattern
- This file — concrete task rotation with repo-specific commands and 24h skip
- `autonomous-cron-pipeline` → `references/auto-continue-execution-pattern.md` — 4-phase discovery+execution pattern
