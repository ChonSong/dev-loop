# Hermes Web Computer — Phase Plan (Concrete Example)

> Created 2026-05-11. 4 chained cron jobs to complete v1.0 tiles autonomously.

## Context

hermes-web-computer is a Go backend + Svelte 5 frontend running as a tiling web desktop.
70% functional (terminal, layout tree, security, telemetry, filesystem API, 3-column UI).
30% stubs (agent chat echoes, browser navigation is log.Printf, voice bridge exists but no UI).

## Phase 1: Complete 90%-done features (Editor save + Agent chat + Voice UI)

**Cron ID**: `c16d0e348f14` | **Deliver**: telegram

Tasks:
1. Monaco.svelte — add Ctrl+S / Cmd+S save via `fs.write` WS method
2. RightPanel.svelte — add voice toggle (mic record/stop buttons)
3. ws.ts store — add `audio.start()` and `audio.stop()` WS methods
4. Backend: wire `chat.send` to real Hermes API (HTTP POST to host.docker.internal:8642)
5. Frontend: capture mic via MediaRecorder API → send Opus via `audio.stream`
6. Test: `go test ./backend/...` passes
7. Test: `npx playwright test e2e/tests/01-layout.spec.ts` passes
8. Commit + push to main

Completion marker: `/tmp/hermes-computer-phase-1.done`

## Phase 2: Browser tile (chromedp)

**Cron ID**: `e4c5b202cba3` | **Deliver**: telegram

Tasks:
1. Create `backend/browser/browser.go` — chromedp wrapper (navigate/screenshot/interact)
2. Add WS protocol methods: `browser.navigate`, `browser.screenshot`, `browser.click`, `browser.input`
3. Create `frontend/src/components/Browser.svelte` — URL bar, back/forward, navigation controls
4. Update Tile.svelte for `content === 'browser'`
5. Update apps.go for browser app type
6. Commit + push

Completion marker: `/tmp/hermes-computer-phase-2.done`

## Phase 3: Dashboard migration via repo-transmute

**Cron ID**: `47290d3e5de5` | **Deliver**: telegram

Tasks:
1. Extract 4-6 key React components from agent-os
2. Convert to Svelte 5 runes syntax
3. Create new Svelte components in frontend/src/components/
4. Wire API calls to Go backend
5. Update Tile.svelte for dashboard tile types
6. Run `npm run build` to verify
7. Commit + push

Completion marker: `/tmp/hermes-computer-phase-3.done`

## Phase 4: Polish and test coverage

**Cron ID**: `6250c0614c37` | **Deliver**: telegram

Tasks:
1. Implement `tool.execute` handler in backend
2. Implement `fs.watch` (optional)
3. Add E2E tests for Browser tile
4. Add E2E tests for Voice recording/playback
5. Run full `npx playwright test` suite
6. Update PLAN.md and APPLICATION-PLAN.md
7. Commit + push

Completion marker: `/tmp/hermes-computer-phase-4.done`
