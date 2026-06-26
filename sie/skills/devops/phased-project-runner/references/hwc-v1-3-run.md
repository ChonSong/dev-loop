# HWC Phase Run Reference (Updated 2026-07-08)

## Environment

| Item | Path |
|------|------|
| Project source | `/opt/data/hermes-web-computer/` |
| State dir | `/opt/data/hermes-web-computer-state/` |
| Server binary | `/opt/data/hermes-web-computer-state/hwc-server` |
| Server port | 3005 |
| hermesURL | `http://localhost:8787` (changed in commit `86a2ead`) |
| Frontend WS URL | `ws://localhost:3005/ws` (fixed in v1.4) |

**The `/home/hermeswebui/.hermes/hermes-web-computer/` path does NOT contain the source code** — that path only has runtime state (sessions/, telemetry/). The full git repo (backend/, frontend/, .git/) is at `/opt/data/hermes-web-computer/`. See `phased-project-runner` SKILL.md pitfalls for the authoritative path discussion.

## Git State (as of 2026-07-08)
- HEAD: `86a2ead` (fix(agent): rewrite handleToolExecute + update hermesURL default)
- Latest tag: v1.4 at `01e1781`
- 4 commits ahead of v1.4 tag

## Phase Summary
- v1.3: All 10 phases (0-9) complete
- v1.4: Phases 0-5 claimed complete in plan doc, but many checkbox items unchecked
- PHASE_TRACKER.json: claims all 15 phases complete (likely inaccurate for v1.4 items)

## Server Status
- Server was DOWN on host at time of audit (port 3005 not listening)
- Binary exists at state dir (14.6MB, built May 28)
- Start command: `HERMES_HWC_ROOT=/home/hermeswebui/.hermes/hermes-web-computer nohup ./agent-os server --port 3005 > /tmp/hermes-web-computer.log 2>&1 &`

## Cron Jobs (all paused as of 2026-07-08)
- `4d2609ce31ba` — canary watch (14:00/18:00/22:00)
- `ecb3846b907b` — rebuild+deploy (16:00/20:00)
- `4285b8696203` — nightly build health (19:00)

## E2E Tests
- 18 spec files, ~50+ tests
- 3 pre-existing failures: contrast.spec.ts, concurrent.spec.ts, ws-flood.spec.ts
- Playwright config: baseURL `http://localhost:3005`

## Visual QA
- Scripts at `scripts/visual-qa.sh` and `scripts/run-visual-qa.sh`
- **BUG: Both scripts target port 3113 (wrong) — should be 3005**
- Baseline screenshots at `/tmp/hwc-qa/baselines/` (from May 23, stale)

## Key Findings from 2026-07-08 Audit
1. v1.4 plan doc (`plans/hwc-v1.4-replace-hermes-webui.md`) says "all phases done" but many steps unchecked
2. FEATURE-TRACKER.md last updated 2026-05-29, references HEAD `30dc005` (behind actual HEAD `86a2ead`)
3. Cloudflared tunnel on host points to `backend:3001` (agent-os), NOT HWC on port 3005
4. Hermes gateway running on port 8787; agent-os backend on port 3001

## Lessons Learned (from validation runs)
- Spec doc §12-type "open items" sections lag behind implementation — always cross-reference spec against actual code
- When PHASE_TRACKER's last phase is already a validation pass, skip redundant validation
- Checkpoint files may use .json OR .md extensions — check both
- Different numbering schemes between git history and checkpoint files are common — discover actual numbering from files
- Cron jobs that always produce [SILENT] should be removed or replaced with low-frequency health checks

## Phase 14 Completion (2026-05-26 18:50 UTC)

Git SHA: `01e178138d70404f211cf22232522607fc4f03cd` (tagged v1.4)
Previous tag: v1.3 at `43532a0`

### Section 12 Verification — All Passed

All 5 WAYBAR-SPEC.md Section 12 open items already implemented:
- System tray real data: `GET /api/system/metrics` returns live CPU/mem/wifi/battery/volume/temp
- Middle-click dock: `Dock.svelte:121` — `e.button === 1` launches new instance
- Terminal drag persistence: `BottomPanel.svelte:57-66` — persists to localStorage
- Voice button capture: `RightPanel.svelte:43-86` — MediaRecorder + audioStatus state
- Monaco editor theme: `Monaco.svelte:17-72` — `illogical-impulse` custom theme

## Phase 15 Validation Run 1 (2026-05-28 06:45 UTC)

Git SHA: `01e178138d70404f211cf22232522607fc4f03cd`

Validation pass — all 14 phases were already complete.

### Build & Test Results
- **Go tests:** 7 packages PASS (audio, layout, security, session, ws + 3 no-test) — 68+ tests across all packages
- **Frontend build:** PASS — built to `frontend/dist/` in 1m 20s (221KB gzip JS, 3.7MB Monaco code-split)
- **Playwright core:** 14/14 PASS (8 smoke + 1 layout + 1 resize + 4 pipeline)
- **Playwright browser path fix:** `PLAYWRIGHT_BROWSERS_PATH=/opt/data/hermes-web-computer/.playwright` was required — the default `/opt/hermes/.playwright` lacked the headless shell
- **Playwright module collision fix:** Root `node_modules/` and `e2e/node_modules/` both had playwright — symlinked `@playwright`, `playwright`, `playwright-core` from e2e to root

### Server Health
- Server binary: `/opt/data/hermes-web-computer-state/hwc-server` (14MB, pre-compiled)
- Server on port 3005: `GET /` > 200 (SPA renders), `GET /api/system/metrics` > 200 (CPU 35%, mem 90%, wifi, battery 100%)
- Previously running server PID needed to be detected before starting a new instance

### Waybar Features Verified
- 9 clickable workspace dots + clock + agent status in floating pill
- System tray: wifi/battery/volume/temperature with dim/muted/critical states
- Dock: 11 app launchers, purple running dot, right-click pin/unpin
- FileTree: collapsible tree, rename/delete/copy-path context menu
- BottomPanel: Terminal/Problems/Output/Ports tabs, drag-to-resize, localStorage persistence
- MenuBar: File/Edit/View/Go/Run/Terminal/Help with Alt+F/E/V/G/R/T/H shortcuts
- Full solid #191919 dark theme with JetBrains Mono

### Phase Tracker State
`PHASE_TRACKER.json`: 15 phases total, status: "complete", current_phase: 15
- `total_phases` was 14 but 15 phases existed (off-by-one from unplanned Phase 8 restart and Phase 15 validation). When adding a validation phase, update `total_phases` to match.
- Checkpoint written: `/opt/data/hermes-web-computer-state/CHECKPOINTS/phase-15-DONE.json`

### Project State — Terminal
All v1.3 and v1.4 features implemented and tagged. No planned future phases.
The cron job should be disabled (see Project Retirement in the skill).

## Phase 15 Validation Run 2 (2026-05-28 07:09 UTC)

Same Git SHA: `01e178138d70404f211cf22232522607fc4f03cd`

Second wake-up of the cron job. Phase 15-DONE.json already existed.
Found all phases complete. No new commits to validate. Reported `[SILENT]`.

Confirmed: the cron fires every 30 minutes, finds nothing to do, and emits [SILENT].
This is the terminal-state pattern — the cron should be removed or replaced with a daily health check.

## Phase 15 Validation Run 3 (2026-05-28 08:34 UTC)

Same Git SHA: `01e178138d70404f211cf22232522607fc4f03cd`

Third wake-up. PHASE_TRACKER: `current_phase: 15, status: "complete"`.
All 15 phases (0-14 feature + 15 validation) complete. No new commits since v1.4 tag.

Produced a full status report (not [SILENT]) — documented build state, Go tests status, frontend build, server binary, git state, and the terminal-state conclusion. Recommended new phases be added for v1.5+ before the cron can do further work.

Confirmed pattern: when the PHASE_TRACKER's LAST phase is already a validation pass, entering a NEW validation pass is redundant. The skill should check whether validation has already run and skip to terminal-state reporting directly, rather than recommending another round of Go tests + Playwright.

**Lesson: spec-doc cross-referencing catches stale docs.** The WAYBAR-SPEC.md §12 listed 5 items as "open/deferred". ALL were already implemented — the doc had not been updated during feature development. This pattern (spec doc §12-type sections lagging behind implementation) is common enough to warrant a dedicated step in the completion verification workflow. The `phased-project-runner` skill now includes this step.

## Phase 15 Validation Run 4 (2026-05-28 10:30 UTC)

Same Git SHA: `01e178138d70404f211cf22232522607fc4f03cd`

Third wake-up. PHASE_TRACKER: `current_phase: 15, status: "complete"`.
All 15 phases (0-14 feature + 15 validation) complete. No new commits since v1.4 tag.

Produced a full status report (not [SILENT]) — documented build state, Go tests status, frontend build, server binary, git state, and the terminal-state conclusion. Recommended new phases be added for v1.5+ before the cron can do further work.

Confirmed pattern: when the PHASE_TRACKER's LAST phase is already a validation pass, entering a NEW validation pass is redundant. The skill should check whether validation has already run and skip to terminal-state reporting directly, rather than recommending another round of Go tests + Playwright.

## v1.4 Initial State (Affects E2E Selectors)

Initial tiles: 3 (Dock + Waybar tile + right panel)
Left panel: icon-only tabs (📁 🚀 💬)
Middle panel aria-label: "Editor area — drop files to open"

## Checkpoint Files Present

```
phase-0.md through phase-9.md
phase-10-DONE.json / phase-10-STARTING.json
phase-11-DONE.json / phase-11-DONE.md / phase-11-STARTING.json
phase-12-DONE.json / phase-12-DONE.md
phase-13-DONE.json
phase-14-DONE.json / phase-14-STARTING.json
phase-15-DONE.json
phase-N-COMPLETE.json
```
