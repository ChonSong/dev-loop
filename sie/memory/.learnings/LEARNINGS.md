## [LRN-008-study-page-visual-gaps]
**Priority:** high
**Status:** pending
**Area:** frontend
**Recurrence-Count:** 3
**Pattern-Key:** study-page-reference-drift
**Logged:** 2026-06-22

The /study postflop page structure matches the reference (board cards, pot, position bar, action buttons) but three specific visual gaps prevent it from matching the GTO Wizard original:

1. Action buttons show pot% in parens (e.g., "2.0 (36%)") but the REFERENCE shows GTO frequency chips. Need to display GTO-recommended frequency % next to each action button as a colored micro-chip (green for GTO, red for suboptimal).

2. After user selects an action, no GTO comparison overlay appears. The reference shows the user's pick vs GTO recommendation with color coding (green=correct, red=incorrect) and EV difference.

3. The "Check vs GTO" button/flow is missing from the postflop mode. The reference shows a clear comparison mode where the user's action is evaluated against the solver's recommendation.

4. Preflop mode: hand matrix cell colors don't match reference. Reference uses: red=raise, blue=call, gray=fold. Live page uses: red=raise, dark gray=fold, NO blue for call actions.

## [LRN-010-code-quality-audit-gap]
**Priority:** high
**Status:** pending
**Area:** infra
**Recurrence-Count:** 1
**Pattern-Key:** deployment-health-vs-code-quality
**Logged:** 2026-06-22

HWC telemetry code review (session 9ae87791c9b0) found 11 issues (2 P0, 1 P1, 8 P2/P3) — none caught by the autonomous HWC Health Audit cron. The audit checked deployment health (port up, binary fresh, git status) but never source code quality: no go vet, no go test -race, no coverage check, no env var cross-reference against docs, no doc-file-exists checks. Every issue would have been caught by adding `go vet ./...`, `go test -race ./...`, and a grep for os.Getenv vs documented env vars. Fix: the HWC Health Audit was upgraded 2026-06-22 to include checks 7-12. Save this pattern as a reusable code-quality-audit skill for any language.
## [LRN-009-coach-cron-rate-limited]
**Priority:** critical
**Status:** pending
**Area:** infra
**Recurrence-Count:** 9
**Pattern-Key:** coach-cron-429
**Logged:** 2026-06-22

Coach and Player cron jobs were pinned to openrouter/owl-alpha which hits HTTP 429 rate limits on every run. 9 consecutive coach failures. Both pinned to deepseek-v4-flash via opencode-go on 2026-06-22 22:50. Monitor next 24h for stability.

## [LRN-011-rsi-meta-problem-fix]
**Priority:** high
**Status:** resolved
**Area:** infra
**Recurrence-Count:** 1
**Pattern-Key:** rsi-meta-problem-coverage-scan
**Skill-Authored:** false
**Logged:** 2026-06-22

The remaining RSI meta-problem was: no autonomous loop has the question "what should I be checking that I'm not checking?" baked in. Each loop optimizes for its local goal, and no loop scans the system for coverage blind spots. Fix applied 2026-06-22:

1. **SIE cron prompt upgraded with Phase 0** — before processing .learnings/ entries, the SIE now proactively scans all projects in the master checkpoint, checks what audits exist and what they cover, identifies gaps (uncovered project, deployment-only audit, stale review), and seeds .learnings/ entries for each gap found. The Python pipeline then processes these entries.

2. **SIE skill updated to v1.1.0** — Phase 0 documented as an LLM-driven coverage scan that runs before Phases 1-4.

3. **HWC Health Audit prompt upgraded with Meta-Reflection** — after completing all checks, the audit asks itself "is there anything this audit should be checking that it doesn't currently?" and seeds a .learnings/ entry if it finds a gap.

This makes the SIE the meta-loop it was designed to be: it doesn't just process what it's told — it discovers what it should be checking. The next SIE run at 2026-06-23 00:00 will exercise Phase 0 for the first time.

## [LRN-012-gto-wizard-code-quality-audit-gap]
**Priority:** high
**Status:** pending
**Area:** infra
**Recurrence-Count:** 1
**Pattern-Key:** deployment-health-vs-code-quality
**Logged:** 2026-06-23

Phase 0 scan found gto-wizard-clone has health audit (gto-wizard-health-check, 11 endpoint checks) and QA sweep (every 4h) but NO code quality checks: no `tsc --noEmit`, no `go vet`, no race detection (`go test -race`), no coverage check, no env var cross-reference, no doc drift check. The coach-development-loop reviews commits but does not run static analysis. This is the LRN-010 pattern recurring: deployment health ≠ code quality. Fix: add a code-quality-audit cron job for gto-wizard-clone that runs `npx tsc --noEmit`, `go vet ./...`, `go test -race ./...`, and `go test -cover ./...` on a schedule (e.g., every 12h).

## [LRN-013-cluster-mine-queue-no-audit]
**Priority:** high
**Status:** pending
**Area:** infra
**Recurrence-Count:** 1
**Pattern-Key:** project-with-zero-autonomous-oversight
**Logged:** 2026-06-23

Phase 0 scan found cluster-mine-queue (status: complete) has NO health audit and NO code quality checks. No cron job references this project. While the project is marked complete, the absence of any autonomous oversight means regressions (e.g., broken queries, stale dependencies, bitrot) will go undetected. The project's health field says "query_verified" but no cron verifies this. Fix: add a lightweight health check cron that runs the project's test suite and verifies query correctness, or mark the project as "archived" in the master checkpoint to exclude it from coverage requirements.

## [LRN-014-energy-aware-task-router-no-audit]
**Priority:** high
**Status:** pending
**Area:** infra
**Recurrence-Count:** 1
**Pattern-Key:** project-with-zero-autonomous-oversight
**Logged:** 2026-06-23

Phase 0 scan found energy-aware-task-router (status: complete, phase 7, 75 tests pass) has NO health audit and NO code quality checks. No cron job references this project. The `energy-router-dev-build` job that once existed is not present in the current jobs.json — it was removed or renamed. While the project is complete, the "75_pass_0_error_0_fail" health status is unverified by any autonomous loop. Fix: add a lightweight cron that runs `go test ./...` in the project repo, or mark the project as "archived" in the master checkpoint to exclude it from coverage requirements.

## [LRN-015-hwc-audit-missing-systemd-service-check]
**Priority:** high
**Status:** pending
**Area:** infra
**Recurrence-Count:** 1
**Pattern-Key:** deployment-health-vs-systemd-consistency
**Logged:** 2026-06-23

HWC Health Audit meta-reflection (session 2026-06-23) found: the audit checks port health (HTTP 200 on :3005) but never verifies the server is managed by systemd as intended. The binary is running and responding, but `hwc-server.service` is **inactive** — no journald entries, no boot-time auto-start, no crash recovery. The currently running process was started manually (or by a mechanism not tracked by systemd). If the process dies, nothing restarts it. Fix: add `systemctl is-active hwc-server.service` (or `systemctl --user is-active` if user-instance) to the audit. If the port is up but the service is inactive, flag it as a reliability risk: the process is running outside systemd supervision.

## [LRN-016-server-manual-start-bypassing-systemd]
**Priority:** high
**Status:** pending
**Area:** infra
**Recurrence-Count:** 1
**Pattern-Key:** server-manual-start-bypassing-systemd
**Logged:** 2026-06-24

Coach found: two projects (gto-wizard-clone, polytopia-clone) where the Player started the production server manually (npx next start, serve dist) instead of using the configured systemd service. In gto-wizard, the next-server was unmanaged — no auto-restart, deploy script's systemctl restart silently failed, serving stale build. In polytopia, a stale serve dist process on port 3001 blocked the systemd service from binding to its configured port.

The fix: a reusable check for the coach would be: after verifying a server is running on the expected port, run `systemctl --user is-active <service-name>` and verify the MainPID matches the listening process. If mismatched, escalate: the process is running outside systemd supervision. This check should be added to every project's health audit and the Player should be disciplined to always start servers via systemctl, never manually.

## [LRN-017-hwc-audit-missing-go-version-check]
**Priority:** high
**Status:** pending
**Area:** infra
**Recurrence-Count:** 1
**Pattern-Key:** hwc-audit-toolchain-version-drift
**Logged:** 2026-06-24

HWC Health Audit meta-reflection found: the audit runs `go vet`, `go test -race`, and `go test -cover` but never verifies the Go toolchain version satisfies the `go.mod` directive. Currently `go.mod` requires `go 1.26` but the system has `go1.22.5` — builds will fail with confusing errors. The audit should add `head -3 backend/go.mod | grep "^go "` and `go version`, comparing the installed version against the required version. If the installed toolchain is older, flag a CRITICAL: builds from source will fail on this host.

## [LRN-018-hwc-audit-wrong-binary-path]
**Priority:** high
**Status:** pending
**Area:** infra
**Recurrence-Count:** 1
**Pattern-Key:** hwc-audit-binary-target-mismatch
**Logged:** 2026-06-24

HWC Health Audit meta-reflection found: the audit checks `backend/myserver` freshness, but the Makefile's `build` target produces `backend/agent-os`. The `backend/myserver` file (1.5MB smaller, built with go1.26 on June 13) is a stale artifact from a different (possibly manual or CI) build. The canonical binary path `backend/agent-os` exists, was built June 14 with go1.26, and matches the running PID 611. The audit should check `backend/agent-os` (the Makefile target) instead of `backend/myserver`.

## [LRN-019-hwc-audit-zero-test-packages-not-flagged]
**Priority:** medium
**Status:** pending
**Area:** infra
**Recurrence-Count:** 1
**Pattern-Key:** hwc-audit-coverage-blind-spots
**Logged:** 2026-06-24

HWC Health Audit meta-reflection found: the audit reports per-package coverage percentages but does not explicitly flag packages with ZERO test files. 11 of 16 backend packages have no tests: agent, browser, cmd/server, config, docker, llm, mcp, pty, state, telemetry, xpra. These are core code paths — browser automation, Docker management, LLM routing, MCP client, PTY supervisor, session state, telemetry — with zero automated verification. A coverage gap report listing zero-test packages would be more actionable than aggregate coverage numbers. Fix: the audit should enumerate packages with `[no test files]` and flag them as untested code paths.

## [LRN-020-polytopia-clone-deployment-only-audit]
**Priority:** high
**Status:** pending
**Area:** infra
**Recurrence-Count:** 3
**Pattern-Key:** deployment-health-vs-code-quality
**Logged:** 2026-06-25

Phase 0 scan found polytopia-clone (status: active) has only a basic URL health check via deploy-verify.sh (every 30min, checks hex.codeovertcp.com returns 200) and a Polytopia deploy loop script, but NO dedicated health audit and NO code quality checks. No `tsc --noEmit`, no `go vet`, no race detection, no coverage check, no env var cross-reference, no doc drift check. The coach-development-loop reviews commits but does not run static analysis. This is the LRN-010/LRN-012 pattern recurring for the 3rd time: deployment health ≠ code quality. The `code-quality-audit` skill at devops/code-quality-audit defines what to include. Fix: add a dedicated health audit + code quality checks for polytopia-clone, modeled on the code-quality-audit skill's Node/TypeScript section (npx tsc --noEmit, npx eslint, vitest coverage, env var audit).

## [LRN-021-hermes-webui-dev-uncovered]
**Priority:** high
**Status:** pending
**Area:** infra
**Recurrence-Count:** 3
**Pattern-Key:** project-with-zero-autonomous-oversight
**Logged:** 2026-06-25

Phase 0 scan found hermes-webui-dev (status: blocked, last_review: null) has NO dedicated health audit and NO code quality checks. The only autonomous check is deploy-verify.sh confirming dev.codeovertcp.com returns HTTP 502 (down). No cron job specifically monitors or attempts to restore this service. The project is blocked on a 502 error with no recovery mechanism. This is the LRN-013/LRN-014 pattern recurring for the 3rd time: project with zero autonomous oversight. Fix: either (a) add a health audit cron that checks dev.codeovertcp.com with diagnostics (systemd service status, nginx logs, port health) and attempts recovery, or (b) mark the project for decommissioning in the master checkpoint if the service is intentionally dead. A project with `last_review: null` is invisible to freshness checks entirely.

## [LRN-022-hwc-audit-go-version-mismatch]
**Priority:** high
**Status:** pending
**Area:** infra
**Recurrence-Count:** 1
**Pattern-Key:** hwc-audit-build-toolchain-drift
**Logged:** 2026-06-25

HWC Health Audit meta-reflection found: `backend/go.mod` declares `go 1.26` but the installed Go toolchain is `go1.22.5 linux/amd64`. This mismatch causes `go test -cover ./...` to emit repeated `go: no such tool "covdata"` errors for all packages without test files (11 of 16 packages), and silently degrades coverage tooling — those packages' coverage can't be measured. If the codebase ever uses Go 1.26-specific language features (min/max builtins, improved slices maps, range-over-func), the build would fail silently or produce incorrect binaries on the 1.22.5 toolchain. The audit runs `go vet` and `go test` but never checks whether the toolchain version satisfies go.mod's requirement. Fix: add a Go toolchain version check (`go version | grep -oP 'go\\d+\\.\\d+'` vs `go mod edit -json | jq -r .GoVersion || grep '^go ' go.mod`), and flag any mismatch. If mismatch exists, either (a) install the correct Go toolchain via `go install golang.org/dl/go1.26@latest && go1.26 download`, or (b) use `GOTOOLCHAIN=auto` with toolchain directive in go.mod.

## [LRN-023-refqa-uncovered]
**Priority:** high
**Status:** pending
**Area:** infra
**Recurrence-Count:** 1
**Pattern-Key:** project-with-zero-autonomous-oversight
**Logged:** 2026-06-27

Phase 0 scan found refqa (status: active, last_review: null) has NO dedicated health audit and NO code quality checks. No cron job references this project by name. The only autonomous interaction is via the player-development-loop which implements AGENTS.md tasks — not a health audit. The project has all 3 backlog tasks implemented and verified (parser.py, runner.py w/ comparator, cli.py), health is "all_modules_import_0_regressions_parser_validated", but this status is unverified by any autonomous loop. There are no unit tests (0 found by pytest). The project's `last_review` is null, meaning it has never undergone a formal review. This is the LRN-013/LRN-014/LRN-021 pattern recurring for the 4th time: a project with zero autonomous oversight. Fix: (a) add a health audit cron that runs `pytest --cov=refqa --cov-report=term`, `ruff check .`, and `mypy refqa/` on a schedule (e.g., every 12h), and (b) perform an initial review to set `last_review`.