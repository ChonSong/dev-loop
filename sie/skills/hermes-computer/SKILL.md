---
name: hermes-computer
description: "Build and extend hermes-web-computer — Go backend + Svelte 5 SPA tiling AI desktop. Covers architecture, tile development, Hermes agent integration, and migration from agent-os/bytebot/cua."
version: 1.0.0
category: devops
---

# Hermes-Computer Operations

## What It Is

hermes-web-computer is a **tiling AI desktop** where each tile is a Svelte 5 component backed by a Go handler. The layout engine manages split/resize/focus. Tiles communicate through a JSON-RPC multiplexer over WebSocket.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     hermes-web-computer (THE SHELL)                 │
│                                                                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │ Terminal │ │ Browser  │ │ Dashboard│ │ Voice    │ │ Code     │ │
│  │   Tile   │ │   Tile   │ │   Tile   │ │   Tile   │ │  Edit    │ │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ │
│       │             │            │             │             │      │
│       └─────────────┴────────────┴─────────────┴─────────────┘      │
│                            │                                        │
│                  WebSocket (JSON-RPC)                                │
│                            │                                        │
│              ┌─────────────▼─────────────┐                          │
│              │   Go Backend Multiplexer  │                          │
│              └─────────────┬─────────────┘                          │
└────────────────────────────┼────────────────────────────────────────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
  ┌─────────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
  │  hermes-agent  │ │  Docker     │ │  External   │
  │  (THE BRAIN)   │ │  Sandbox    │ │  APIs       │
  └────────────────┘ └─────────────┘ └─────────────┘
```

## Quick State Overview (June 2026)

**Version:** v1.4 near-complete (HEAD `8328ad2`)
**Server:** ✅ Running on host port 3005 (HTTP 200, PID confirmed)
**Backend:** 29 Go source files, 14 packages
**Frontend:** 36 Svelte 5 components + 11 store files
**E2E tests:** 18 spec files, 2,322 lines — ✅ CI passes, ❌ local runs fail (missing libglib-2.0.so.0 in container)
**CI:** 4-phase GitHub Actions (lint+build → e2e×2 shards → a11y → visual) + nightly Lighthouse

**Key remaining gaps:**
1. LLM router is dead code (nothing imports it) — MCP client IS wired (lazy init, 8 WS handlers), only needs frontend UI
2. No auth/login → single-user only
3. ~~No Cloudflare tunnel for port 3005~~ ✅ Quick tunnel via systemd `cloudflared-hwc.service`. Current URL at `~/.hermes/hwc-tunnel-url.txt` (changes on restart). Named tunnel blocked by expired API token.
4. Visual QA baseline screenshots at `/tmp/hwc-qa/baselines/` (May 23 91-97KB) + copied to Playwright snapshot dir (`e2e/tests/visual/baseline.spec.ts-snapshots/`)
5. Visual QA cron re-created (`fcf273002361`, every 720m, no_agent script `hwc-visual-qa.sh`)
6. Telemetry RingBuffer path hardcoded to `/agent/.telemetry/events.jsonl` — should be state-dir-relative

See `docs/FEATURE-TRACKER.md` for authoritative feature status.

## Repo & Access

- **GitHub**: `github.com/ChonSong/hermes-web-computer` (branch: main)
- **Host** (EndeavourOS, where builds run): `/home/sean/.hermes/hermes-web-computer`
- **Container** (sync/copy): `/home/hermeswebui/.hermes/hermes-web-computer` — syncs from host, use for reading only
- **CRON JOB CONTAINER** (this env runs cron jobs): Code at `/opt/data/hermes-web-computer`, Go at `/usr/bin/go` (go 1.24.4), GOPATH `/opt/data/home/go`
- **Go toolchain**: `/usr/bin/go` (go 1.24.4, system go — builds work despite `go.mod` declaring `go 1.26`)
- **GOPATH**: Always set `GOPATH=/opt/data/home/go` for all go commands in this container env
- **HERMES_HWC_ROOT**: Set `HERMES_HWC_ROOT=/opt/data/hermes-web-computer` when running Go tests (required — tests use this env var to locate the repo root)
- **Stack**: Go 1.25 + Svelte 5 + Vite + Tailwind + xterm.js

## CRITICAL FIRST FIX: WebSocket Connection Bug

**Before ANY feature work, fix this.** The HWC frontend connects to the wrong backend:

- Frontend `ws.ts:139` hardcoded: `ws://localhost:3113/ws` → connects to **agent-os Express** (old server)
- HWC Go backend runs on **port 3005** but receives **NO frontend connections**

This means all HWC frontend traffic goes to agent-os, not to HWC's Go backend. The fix:

1. Update `frontend/src/stores/ws.ts:139` → `ws://localhost:3005/ws`
2. Verify with: `curl -s http://localhost:3005/ | grep -E "title|script"` (should return HWC JS chunks)

**Why this matters:** HWC's Go backend (`ws/multiplexer.go`) has full implementations of LLM Router, MCP Client, Docker Manager, Agent Streamer — but none of them receive any traffic because the frontend is wired to the wrong server. Fix this first.

## Go Toolchain (Container / Cron Job Context)

> **Updated (2026-05-24):** Both the go1.26.0 toolchain at `/opt/data/home/go/pkg/mod/golang.org/toolchain@v0.0.1-go1.26.0.linux-amd64/bin/go` AND the system go at `/usr/bin/go` (1.24.4) are available. Go's forward compatibility treats `go 1.26` in `go.mod` as a minimum, not an exact requirement.

```bash
# Verify toolchain exists
ls /opt/data/home/go/pkg/mod/golang.org/toolchain@v0.0.1-go1.26.0.linux-amd64/bin/go
# → go version go1.26.0

# Build with explicit toolchain (required for phase engine cron job)
cd /opt/data/cache/hermes-web-computer/hermes-web-sync/backend
GOPATH=/opt/data/home/go /opt/data/home/go/pkg/mod/golang.org/toolchain@v0.0.1-go1.26.0.linux-amd64/bin/go build -o /opt/data/cache/hermes-web-computer/hermes-web-sync/bin/hwc-server ./cmd/server/
```

```bash
# Go tests (MUST set HERMES_HWC_ROOT — tests check it)
cd /opt/data/cache/hermes-web-computer/hermes-web-sync/backend
GOPATH=/opt/data/home/go /opt/data/home/go/pkg/mod/golang.org/toolchain@v0.0.1-go1.26.0.linux-amd64/bin/go test ./... -count=1 -timeout=120s
```

## The Three Repos — Clarity on Ownership

There are three repos that sound related but have very different roles. **Do not confuse them:**

| Repo | What it is | Active? | Action |
|------|-----------|---------|--------|
| `hermes-web-computer` | The tiling AI desktop (Go+Svelte5) — **this is what we're building** | ✅ Yes, dev | Work here |
| `agent-os` | Legacy React+Express+Postgres dashboard — still **running in production** on port 3001 | ⚠️ Legacy, live | Maintenance only, not dev target |
| `hermes-computer-planning` | Research + planning docs — no code, no CI, no tests | ❌ Archive | Move useful docs here, archive repo |

### Repositories in the ecosystem (not part of HWC)

| Repo | Owner | What it is |
|------|-------|-----------|
| `hermes-workspace` | outsourc-e (external) | React Electron desktop UI for Hermes Agent — 794MB, completely separate |
| `hermes-sync` | ChonSong | Portable config + skills bootstrap — separate from all three |

- **Canonical SPEC location** (`hermes-computer` SKILL.md): `/home/sean/.hermes/hermes-web-computer/frontend/dist/ILLOGICAL-IMPULSE-DESIGN.md`
- **This env** (container): `/home/hermeswebui/.hermes/hermes-web-computer`
- **Stack**: Go 1.25 + Svelte 5 + Vite + Tailwind + xterm.js
## Quick Start

> **Critical:** The canonical working repo is on the **EndeavourOS host** at `/home/sean/.hermes/hermes-web-computer`. The container at `/home/hermeswebui/.hermes/hermes-web-computer` is a sync/copy. **Always work on the host** for builds, tests, and visual QA. The container is for the WebUI and orchestration only.

### Build + Run on Host (where the code lives)

**SSH key (2026-06-10):** `ssh sean@172.19.0.1` with `~/.ssh/id_ed25519`. Host key already verified. The old `container_key` path at `/home/hermeswebui/.hermes/container_key` is stale — use `~/.ssh/id_ed25519` instead.

```bash
# SSH to host (ONLY works from hermes-webui container, NOT cron container)
ssh sean@172.19.0.1 \
  "cd /home/sean/.hermes/hermes-web-computer/backend && go build -o /tmp/hwc-server ./cmd/server/"

# Verify backend is running
ssh sean@172.19.0.1 \
  "curl -s -o /dev/null -w '%{http_code}' http://localhost:3005/"

# If server needs restarting — use /tmp/hwc-server, NOT ./backend/agent-os
ssh sean@172.19.0.1 \
  "kill \$(ps aux | grep 'hwc-server' | grep -v grep | grep -v 'bash -c' | awk '{print \$2}') 2>/dev/null; sleep 1"
ssh sean@172.19.0.1 \
  "cd /home/sean/.hermes/hermes-web-computer && \
   HERMES_HWC_ROOT=/home/sean/.hermes/hermes-web-computer \
   nohup /tmp/hwc-server server --port 3005 > /tmp/hwc-server.log 2>&1 &"

# Verify rebuild + server
ssh sean@172.19.0.1 \
  "curl -s -o /dev/null -w '%{http_code}' http://localhost:3005/"

# Run Go tests on host
ssh sean@172.19.0.1 \
  "cd /home/sean/.hermes/hermes-web-computer/backend && go test ./... -count=1 -timeout=60s"

# E2E tests on host (requires HWC server running on 3005)
ssh sean@172.19.0.1 \
  "cd /home/sean/.hermes/hermes-web-computer/e2e && \
   npx playwright test smoke.spec.ts --project=chromium --config=playwright.remote.config.ts"

# Visual QA on host (Chrome CLI screenshot, no Playwright needed)
ssh sean@172.19.0.1 \
  "google-chrome-stable --headless --disable-gpu --no-sandbox \
    --virtual-time-budget=30000 --window-size=1440,900 \
    --screenshot=/tmp/hwc-qa/screenshots/quick.png \
    --disable-web-security http://localhost:3005 2>/dev/null && \
  echo 'Screenshot OK' && ls -la /tmp/hwc-qa/screenshots/quick.png"
```

## Core Packages

| Package | Purpose | Status |
|---------|---------|--------|
| `ws/multiplexer.go` | JSON-RPC routing (ui/agent/audio/browser) | ✅ Working |
| `pty/supervisor.go` | PTY lifecycle, ring buffer, checkpoint | ✅ Working |
| `layout/tree.go` | Binary tree layout with delta ops | ✅ Working |
| `security/security.go` | YAML permissions, token-gated execution | ✅ Working |
| `telemetry/telemetry.go` | JSONL ring buffer, async sync, configurable endpoint | ✅ Working — wired into multiplexer, state-dir-relative path, events written for all major operations |
| `audio/bridge.go` | Fun-Audio-Chat binary protocol relay (Opus/Text/Interrupt) | ✅ Working |
| `browser/browser.go` | chromedp wrapper (navigate/screenshot/click/input/back/forward/eval) | ✅ Working — wired into multiplexer, used by apps.launch + 7 route handlers |
| `ws/filesystem.go` | FS handlers (list/read/write/stat/delete) with path sandboxing | ✅ Working |
| `ws/apps.go` | App launch handlers (terminal/editor/preview/browser) | ✅ Working |
| `ws/multiplexer.go` (routeUI) | Dashboard handlers + session CRUD + profiles/skills/crons/memory proxies | ✅ Working |
| `ws/multiplexer.go` (routeAgent) | chat.send → Hermes Agent SSE streaming, five-event token model | ✅ Working |
| `session/store.go` | JSON file-based session store, CRUD + message persistence | ✅ Working |
| `agent/streamer.go` | Go SSE client for Hermes Agent, parses token/reasoning/tool_call/tool_result/stream_end/error events | ✅ Working |
| `profiles.svelte.ts` | ProfileState store: refresh() + getActive() → profileStore | ✅ Working |
| `skills.svelte.ts` | SkillsState store: refresh() + loadContent() → skillsStore | ✅ Working |
| `memory.svelte.ts` | MemoryState store: read() + write() → memoryStore | ✅ Working |
| `crons.svelte.ts` | CronsState store: list/create/update/delete/pause/resume/run | ✅ Working |
| `ProfilePanel.svelte` | Profile list panel with glassmorphism + active indicator | ✅ Working |
| `SkillsPanel.svelte` | Skills list panel grouped by category with filter buttons | ✅ Working |
| `CronPanel.svelte` | Cron job list panel with create form + pause/resume/delete | ✅ Working |
| `MemoryPanel.svelte` | Memory read/write panel with two textareas | ✅ Working |
| `SettingsPanel.svelte` | Settings panel with 7-theme system and 5 functional sections | ✅ Complete | v1.4 | General (font size, default workspace), Appearance (7-theme picker with visual cards, grain toggle, opacity slider), Shortcuts (keyboard reference with 20 shortcuts), Connection (WS status indicator, reconnect, custom WS URL), Advanced (clear cache, reset all settings with confirm) |
| `RightPanel.svelte` | Tabbed panel interface (Chat | Profiles | Skills | Crons | Memory | Settings) | ✅ Working |
| `docker/manager.go` | Docker CLI wrapper — list/stats/start/stop/restart/remove/logs | ✅ Working |
| `xpra/manager.go` | Xpra server lifecycle (start/stop/attach/detach/list, socket+HTTP wait) | ✅ Complete (uncommitted) |
| `xpra/proxy.go` | HTTP reverse proxy + WebSocket bidirectional relay to xpra HTML5 server | ✅ Complete (uncommitted) |
| `llm/router.go` | Multi-provider LLM routing | ❌ Dead code — NOT imported by main.go or any other package |
| `mcp/client.go` | MCP client (stdio JSON-RPC 2.0) | ✅ Wired — lazy init on first `mcp.connect` WS call, 8 route handlers, zero frontend UI |
| `config/manager.go` | Hermes config.yaml read/write, env vars | ✅ Phase 3 |
| `ObservabilityPanel.svelte` | Event feed, health indicators | ✅ Phase 3 |
| `desktop/src/main/index.ts` | Electron main process (window mgmt, tray, app menu, IPC, settings store) | ✅ Phase 5 |
| `desktop/src/preload/index.ts` | Context-isolated electronAPI bridge (IPC invoke handlers) | ✅ Phase 5 |
| `desktop/vite.config.mts` | vite-plugin-electron builds main+preload only | ✅ Phase 5 |
| `CommandPalette.svelte` | Fuzzy search, 8 categories, keyboard nav | ✅ Phase 4 |
| `ConfigPanel.svelte` | Hermes config editor, env var management | ✅ Phase 3 |

## Tile Development

### Adding a New Tile

1. **Create Svelte component** in `frontend/src/components/`
2. **Wire to layout engine** — add content type to `LayoutTree`
3. **Add Go handler** in `backend/ws/multiplexer.go` (routeUI or routeAgent)
4. **Add WS helpers** in `frontend/src/stores/ws.ts` for frontend-to-backend communication
5. **Update security config** if tile needs privileged operations
6. **Add telemetry events** for tile-specific metrics
7. **Update FEATURE-TRACKER.md** — mark tile status, remove from "Remaining for v1.4" if applicable
8. **Add E2E test** in `e2e/tests/` if tile has interactive elements

### Wiring an Existing Orphaned Component as a Tile

When a component exists on disk but isn't reachable from the UI, do a **three-layer wiring audit** before writing any code:

1. **Check Tile.svelte** — Is there a `{:else if node.content === '<type>'}` case rendering this component? If not, add import + case in the switch.
2. **Check Dock.svelte** — Is there a dock item with matching `type` field? If not, add to the `dockItems` array. Decide: is this a **standalone tile** (not `isPanelFeature` — works via `launchNewInstance` + `tileContent` map) or a **panel feature** (`isPanelFeature: true` — dispatches `hwc-dock-panel` event, RightPanel handles)?
3. **Check backend** — Does `apps.go` handle this type? If the tile is frontend-only (uses existing `fs.write` / `ws.send` etc.), skip. If it needs a backend launch handler, add a case to `handleAppsLaunch`.
4. **Update FEATURE-TRACKER.md** — mark tile as ✅ Complete with date and notes.
5. **Verify** — Build frontend (`npm run build` or `go build` backend). No new errors = wiring successful.

**Key distinction:** Standalone tiles (terminal, browser, file-upload) create new layout nodes via `sendOp({ op: "split", content: "<type>" })`. Panel features (profiles, skills, crons, memory) switch RightPanel tabs via `hwc-dock-panel` custom event. If your component is designed as an overlay/helper within another tile (e.g., FileUpload in ChatPanel), make it work as both: standalone mode shows its own full UI, embedded mode exports methods for `bind:this` use by the parent.

### Tile Template

```svelte
<script lang="ts">
  import { send, on } from "../stores/ws"

  let { tileId = "" }: { tileId?: string } = $props()
  let status = $state("idle")

  function handleAction() {
    send({
      protocol: "agent",
      method: "tile.action",
      params: { tile_id: tileId, action: "do_something" }
    })
  }

  // Listen for backend events (cleanup on destroy)
  let cleanupFns: (() => void)[] = []
  $effect(() => {
    cleanupFns.push(
      on("tile.action.result", (data: unknown) => {
        status = (data as { status?: string }).status ?? "error"
      })
    )
    return () => { cleanupFns.forEach(fn => fn()); cleanupFns = [] }
  })
</script>

<div class="w-full h-full bg-gray-950 text-gray-100 flex items-center justify-center">
  <button onclick={handleAction}>Do Something ({status})</button>
</div>
```

**Note:** Use `onclick` not `on:click` (Svelte 5). Use the store's `on()` function for WS events, not `window.addEventListener`.

## Current State Audit (2026-05-11)

### ⚠️ Dead Code — 1 Backend Package Is Not Wired

The following package compiles and has a complete implementation but **nothing imports or uses it**:

| Package | File | Lines | Notes |
|---------|------|-------|-------|
| LLM Router | `backend/llm/router.go` | 638 | Multi-provider routing (OpenAI/Anthropic/Groq/Ollama/LMStudio) |

**MCP Client is NOT dead code** — it's imported in `multiplexer.go`, has a lazy-init field `mcpMgr` created on first `mcp.connect` WS call, and has 8 route handlers (list/connect/disconnect/tools.list/tools.call/resources.list/resources.read/prompts.list/prompts.get). It's fully wired backend-side — only missing frontend UI components.

**Browser and Telemetry are NOT dead code** — both are imported in multiplexer.go and actively used:
- **Browser**: Initialized in `NewMultiplexer()` → used in `apps.go` `apps.launch` handler → 7 route handlers (navigate/screenshot/click/input/back/forward/eval). Imported multiplexer.go:25.
- **Telemetry**: Initialized in `NewMultiplexer()` with state-dir-relative path → events written for session.connected, interrupt, layout.update, approval.granted, pty.write, chat.send, focus.change. Read via observability.events handler. Sync endpoint configurable via `TELEMETRY_ENDPOINT` env var. Imported multiplexer.go:34.

**How to verify:** `grep -rn "m\\.llm\\.\\|m\\.mcp\\." --include="*.go" backend/` — if no results, they're dead. `grep -rn "m\\.browser\\.\\|m\\.telemetry\\.\\|m\\.mcpMgr" --include="*.go" backend/` will show browser, telemetry and MCP are actively wired. See `references/go-backend-wiring-audit.md` for the full 6-layer investigation pattern.

**To wire a dead package:**
1. The package must already be imported in `ws/multiplexer.go` (this is the central wiring point — not main.go)
2. Initialize it in `NewMultiplexer()` and store on `m.*` 
3. Add WebSocket route handlers in `routeUI()` or `routeAgent()` 
4. Add frontend store helpers in `frontend/src/stores/ws.ts`
5. Create/update Svelte components for any new UI

**Telemetry wiring pattern (reference):** Telemetry's RingBuffer is created in `NewMultiplexer()` at a state-dir-relative path. Events are written inline in each handler (session.connected, interrupt, layout.update, approval.granted, pty.write, chat.send, focus.change). The `observability.events` handler reads events via `ReadLast()`. Cloud sync is optional — configure `TELEMETRY_ENDPOINT` env var and call `mux.SetTelemetryEndpoint(endpoint)` before `syncer.Start()`. Syncer has `SetEndpoint()/Endpoint()` methods added June 2026.

### ✅ Fully Implemented (v1.0 + Illogical Impulse redesign)
- WS multiplexer (4 protocols: ui, agent, audio, browser) with read/write loops
- PTY supervisor with 1MB ring buffer, checkpoint, signal handling
- Layout tree (split/mount/unmount/resize/swap/fullscreen with delta ops)
- Security enforcer (YAML config, safe/prompt/block tiers, token gating)
- Telemetry JSONL ring buffer with auto-prune + async HTTP sync
- Audio bridge (Fun-Audio-Chat binary protocol: Opus relay, text, interrupt)
- Filesystem API (list/read/write/stat/delete with path sandboxing, base64 binary)
- App launcher (terminal/editor/preview/browser via PTY + chromedp)
- 4-column frontend (resizable, localStorage persistence, toggleable panels)
- Terminal tile (xterm.js + FitAddon)
- Monaco editor (read-only **with Ctrl+S save/write-back**, dirty indicator)
- File tree (expand, navigate, open files)
- App launcher (command palette for tile types)
- Agent chat UI → **Hermes Agent API** (RightPanel: message history, typing indicators, voice recording via MediaRecorder webm/opus)
- Browser tile (chromedp: navigate, screenshot, click, input, back/forward — screenshot-based viewport)
- 5 Dashboard tiles migrated from agent-os React → Svelte 5:
  - DashOverview (KPI cards, session analytics, event breakdown)
  - DashFileManager (browse, preview, edit, create, delete files)
  - DashSystemStatus (system info, CPU/mem/disk, service status)
  - DashAnalytics (token usage, daily breakdown, model/skill tables)
  - DashObservability (AI event feed, filters, status indicators)
- Command palette (Ctrl+K), Keymap overlay (Ctrl+?)
- **Illogical Impulse glassmorphism redesign:**
  - CSS tokens, Tailwind config with `@theme`, gradient background
  - Floating translucent panels with `backdrop-blur-2xl`, `rounded-2xl`
  - WorkspacePill (top-center, workspace 1-9 dots), Dock (bottom-center, app icons)
  - Monaco dark theme matching purple/violet palette
  - Custom scrollbars, pulseGlow animations
- **Workspace system:** 9 workspaces, each with independent layout tree + floating tiles
- **Full keyboard shortcut map:** Shift+Arrow, Shift+D, Shift+F, Shift+Q, Shift+Alt+Arrow, Shift+Space, Shift+1-9
- **Drag-and-drop:** FileTree → RightPanel (agent context), FileTree → MiddlePanel (editor open)
- **Agent context awareness:** Backend tracks focused tile, provides context scoping
- 10 E2E Playwright tests (Illogical Impulse UI — all passing)
- 17+ Playwright E2E tests (layout, resize, chaos, a11y, perf, workflows)
- 45+ Go backend unit/integration tests (all passing)

### ❌ Not Started (from Hyprland reference)
- **Waybar** — workspace indicators + window title + system tray (wifi/volume/battery/temp/clock). Spec: `docs/WAYBAR-SPEC.md`
- **Clickable workspace indicators** — currently keyboard-only (Shift+1-9), need clickable dots in Waybar
- **Dock pinned apps + running indicators** — dock exists but launches panel, not tiles; no running dot
- **File explorer sidebar** — needs VSCode-style collapsible tree (current FileTree.svelte is basic)
- **Menu bar** — File/Edit/View/Go/Run/Terminal/Help dropdown
- **Bottom terminal panel with tabs** — Terminal/Problems/Output/Ports tabbed sub-panel
- **Workspace→app bindings** — `$brow=firefox` style config, SUPER+1-9 launch bound apps
- **Multi-user support** — Coder integration for team workspaces. Plan: `docs/MULTI-USER-PLAN.md`
### ✅ All Phases Complete (v1.2, 2026-05-24)
All Phase 1-5 features from the 6-phase ROADMAP.md are complete:
- Phase 1 ✅ Sessions + Chat + Streaming
- Phase 2 ✅ Tiling WM + Panel UI
- Phase 3 ✅ Docker/Observability + Config
- Phase 4 ✅ CommandPalette + LLM Router + MCP Client
- Phase 5 ✅ Electron shell

### Current Status: v1.3 — Waybar + Shell Features
### Current Status: v1.4 — Hermes WebUI Replacement Complete

**v1.4 is COMPLETE (2026-05-25) with remaining gaps.** The v1.4 plan (`plans/hwc-v1.4-replace-hermes-webui.md`) replaces Hermes WebUI and migrates agent-os features into HWC. All plan phases 0-5 are done, plus Phase 6 (cost ledger + skills analytics, committed 2026-06-09).

**Remaining gaps (June 2026):**
1. Context meter / message search (deferred)
2. Cloudflare tunnel for HWC port 3005 (needs named tunnel setup)
3. Svelte 5 `effect_orphan` bug — blocks headless Chrome screenshots from container; workaround is host-based QA via SSH
4. SSH to host for visual QA works: `ssh sean@172.19.0.1` (key: `~/.ssh/id_ed25519`)
5. Visual QA cron re-created (`fcf273002361`, every 720m). Script wraps to host: `ssh → bash hwc-host-visual-qa.sh`
6. Fresh baselines captured 2026-06-10: 1440x900 (114KB), 1280x720 (104KB), 1920x1080 (129KB) — host Chrome renders full HWC interface
5. **SettingsPanel is fully wired** — 7-theme system (Illogical Impulse, Catppuccin, Nord, Dracula, Tokyo Night, Everforest, Monokai) with CSS variable switching via `[data-theme]`, visual theme picker, connection status, shortcut reference, persisted to localStorage
5. **2 backend packages are unwired** — llm, mcp (browser and telemetry are actively wired)

| Phase | Steps | Status | Key Commits |
|-------|-------|--------|-------------|
| 0 | Critical fixes: WS connection (:3113→:3005), all managers wired to multiplexer | ✅ | `55fed3f` |
| 1 | DockerPanel, session store path migration, security config path migration | ✅ | `96288c4`, `59aa98c` |
| 2 | FileTree wired to Go fs backend, slash commands, file upload, session search/project grouping, context meter | ✅ | `a35d1e6`→`b6eac64` |
| 3 | Docker containers CRUD, images tab, compose projects | ✅ | `c6cacb9` |
| 4 | Research cards, connection status (reconnect w/ exponential backoff), message search, session projects | ✅ | `0a01317`, `039f8cd` |
| 5 | Xpra escape hatch (native Linux GUI apps via X11→HTML5) | ✅ | `01c1fec` |

Phase 6 (Observability expansion: trace view, cost ledger, skills analytics) and Phase 7 (Multi-user / OIDC auth) are marked "later" in the plan — not started.

**Phase 11 (Waybar + Shell features) — COMPLETED 2026-05-25.** v1.3 tag + 21 post-v1.3 commits through Xpra integration. E2E test results: 43 passed, 36 failed. All failures are test infrastructure issues (stale locators, visual baseline drift, Playwright browser path) — NOT feature brokenness.

Phase state machine:
- **State dir:** `/opt/data/hermes-web-computer-state/` (NOT `/home/hermeswebui/.hermes/` — that path is inaccessible from this container)
- **Tracker:** `PHASE_TRACKER.json` (v1.3 format, 10 phases, all complete)
- **Checkpoints:** `CHECKPOINTS/phase-*.md`
- **Built binary:** `hwc-server` (in state dir root)

### Recommended Build Order (Waybar-first)

**Priority 1 — Waybar + Clickable Workspaces** (from docs/WAYBAR-SPEC.md)
1. Waybar.svelte — top bar with workspace indicators + window title + system tray
2. Clickable workspace indicators (replace WorkspacePill with clickable dots)
3. Window title display in Waybar (subscribe to ui.focus.changed)
4. System tray icons (wifi/volume/battery/temp) — backend metrics integration

**Priority 2 — Dock Refinements**
1. Dock: click to launch tile (not panel)
2. Running indicator dot on dock icons
3. Pin/unpin apps via right-click

**Priority 3 — File Explorer Sidebar**
1. VSCode-style collapsible file tree (SidebarFileTree.svelte)
2. Context menu (new file, rename, delete)
3. Open files in Monaco tile

**Priority 4 — Bottom Terminal Panel**
1. Tabbed terminal sub-panel (Terminal/Problems/Output/Ports)
2. Resizable height

**Priority 5 — Menu Bar**
1. VSCode-style menu bar (File/Edit/View/Go/Run/Terminal/Help)
2. Keyboard shortcut display in menus

### Dock.svelte Bug — handleDockPanelClick Was Undefined

**Symptom:** All Dock panel feature buttons (Files, Profiles, Skills, Crons, Memory) silently did nothing. No error in console.

**Root cause:** The onclick handler referenced `handleDockPanelClick(item)` but this function was never defined. The intent was to call `handleLaunch(item)` for all items (which correctly dispatches `hwc-dock-panel` for panel features and sends `layout.update` for tile apps).

**Fix:** Replace the conditional onclick with direct `handleLaunch()` call:
```svelte
<!-- BEFORE (broken — handleDockPanelClick undefined) -->
onclick={() => { if (item.isPanelFeature) { handleDockPanelClick(item) } else { handleLaunch(item) } }}

<!-- AFTER (correct) -->
onclick={() => handleLaunch(item)}
```

**Verification:** Click Dock → Files, then Dock → Profiles — RightPanel should switch tabs with no console errors.

### Dock → RightPanel Event Routing Gap: `file-manager` Unhandled

**Symptom:** Clicking the Dock's Files (📁) button dispatches `hwc-dock-panel` but the left panel doesn't switch to Files tab.

**Root cause:** The Dock dispatches `hwc-dock-panel` with `{ panel: item.type }` where `item.type` for Files is `"file-manager"`. The RightPanel's `handleDockPanel` event listener handles 8 panel types (`profiles`, `skills`, `crons`, `memory`, `settings`, `config`, `observability`, `containers`) but does NOT handle `"file-manager"`. The left panel has its own independent tab state and doesn't listen for `hwc-dock-panel` at all.

**Bug:** No event bridge from Dock to LeftPanel for switching the Files tab. The left panel's Files button (📁) only switches when clicked directly.

**Fix needed:** Either:
1. Add a `"file-manager"` handler to RightPanel's `handleDockPanel` that delegates to the left panel
2. OR have LeftPanel listen for `hwc-dock-panel` and switch to Files tab when `panel === "file-manager"`
3. OR change the Dock's `"files"` item to dispatch a dedicated `hwc-toggle-files-panel` event that LeftPanel handles

<!-- AFTER (correct) -->
onclick={() => handleLaunch(item)}
```

**Verification:** Click Dock → Files, then Dock → Profiles — RightPanel should switch tabs with no console errors.

### Vite Dev Server Won't Start After npm install

**Symptom:** `npm run dev` fails silently, no output, can't connect to port.

**Root cause:** Installing new devDependencies (e.g., `vitest`, `@playwright/test`) can corrupt `node_modules/.bin/vite` or break the symlink chain. The process appears to start but produces no output and binds no port.

**Debugging steps:**
1. Check if `node_modules/.bin/vite` exists: `ls node_modules/.bin/vite`
2. Check vite version: `node_modules/.bin/vite --version`
3. If both missing → node_modules is broken, do clean reinstall

**Fix — clean reinstall:**
```bash
cd /home/sean/.hermes/hermes-web-computer/frontend
rm -rf node_modules
npm install --include=dev
npx vite --host  # should now work, verify port 5173
```

**Alternative if reinstall is slow:** Try `npx vite --host` directly (it uses the bundled vite in `node_modules/.bin/`). If it starts, the bin links are working. The difference is that `npm run dev` goes through the npm script runner which may fail differently.

**Port 5173 vs 5174:** The Vite config defaults to port 5173. The container had port 5174 forwarded — always verify which port the dev server actually binds with `curl -s -o /dev/null -w "%{http_code}" http://localhost:5173`.

### Cross-Panel Test — Left Panel Emoji-Only Button Targeting

**Symptom:** `page.getByRole('button', { name: 'Files' })` throws strict mode violation — resolves to 3 elements (Dock's `aria-label="Files"` button, Dock's Profiles button, etc.).

**Root cause:** The left panel uses emoji-only buttons (`📁` for Files, `💬` for Sessions, `🚀` for Apps) without text labels or `aria-label`. The Dock has a separate Files button with `aria-label="Files"` that collides on name-based selectors.

**Fix — target the left panel container specifically:**
```typescript
// Click the left panel's Files tab (📁 is the 2nd button in the sidebar)
const leftPanel = page.locator('.rounded-2xl.shadow-panel').first()
const filesButton = leftPanel.locator('button').nth(1)
await filesButton.click()
```

**Alternative — use the Dock's Files button with exact matching:**
```typescript
await page.getByRole('button', { name: /^Files$/ }).click()
// OR
await page.getByRole('button', { name: 'Files', exact: true }).click()
```

**Important:** The Dock's Files button dispatches `hwc-dock-panel` with `{ panel: "file-manager" }`. If the RightPanel doesn't handle `"file-manager"`, the click will do nothing. The RightPanel handles: `profiles`, `skills`, `crons`, `memory`, `settings`, `config`, `observability`, `containers` — but NOT `file-manager`. Use the left panel's 📁 button directly for cross-panel file tests.

### Playwright Config for Container (No Browser Installed in PATH)

**Symptom:** Playwright can't launch Chromium — executable not found. The default Playwright install path (`/opt/hermes/.playwright`) is permission-denied in the container.

**Root cause:** Playwright v1.x self-manages browser binaries and downloads to `$HOME/.cache/ms-playwright/`. In the container, `$HOME` is `/opt/hermes` which has restrictive permissions. The binary also needs `PLAYWRIGHT_BROWSERS_PATH` set to a writable location before calling `npx playwright install`.

**Solution — install Chromium to a writable path:**
```bash
# Set writable browser cache BEFORE install
PLAYWRIGHT_BROWSERS_PATH=/opt/data/hermes-web-computer/.playwright \
  npx playwright install chromium

# Then run tests using the same env var
PLAYWRIGHT_BROWSERS_PATH=/opt/data/hermes-web-computer/.playwright \
  npx playwright test --reporter=list
```

**Verification:**
```bash
PLAYWRIGHT_BROWSERS_PATH=/opt/data/hermes-web-computer/.playwright \
  npx playwright test --reporter=list 2>&1 | tail -5
# Should show "Chrome Headless Shell ... downloaded" then test run
# NOT "permission denied"
```

**Key env var:** `PLAYWRIGHT_BROWSERS_PATH` must be set on BOTH `install` AND `test` commands. Without it on `test`, Playwright still looks in the default (broken) path.

### Svelte 5 aria-label for Unambiguous Button Targeting

### Svelte 5 aria-label for Unambiguous Button Targeting

**Symptom:** Playwright's `button:has-text("⚙️")` matches multiple elements (⚙️ tab in RightPanel AND "⚙️ General" button inside SettingsPanel content).

**Solution:** Add `aria-label` to the tab bar button:
```svelte
<button
  onclick={() => activeTab = "settings"}
  aria-label="Settings tab"
>
  ⚙️
</button>
```
Then target with: `page.click('button[aria-label="Settings tab"]')` in tests.

**Why this matters:** Svelte 5 renders all panel content simultaneously (via `{#if}` blocks). The ⚙️ button inside `SettingsPanel.svelte` is always in the DOM even when the tab isn't active. `button:has-text("⚙️")` matches the first one in DOM order — which is the "General" sub-button, not the tab button.

### Playwright Test File Naming — Don't Put Tests in Root Directory

**Symptom:** Playwright test hangs or can't find tests.

**Rule:** Place all test files under `./tests/` subdirectory. Playwright's `testDir` defaults to project root; if tests are scattered in random subdirectories or root, `test --reporter=list` hangs.

**Correct structure:**
```
frontend/
  tests/
    e2e/
      app.spec.ts
      sessions.spec.ts
  playwright.config.ts  ← testDir: './tests/e2e'
```

### Subagent Timeout Pattern

When using `delegate_task` for multi-file Svelte + Go changes, subagents **consistently hit the 600s timeout** even after completing all file writes. The timeout means "didn't finish summarizing", not "didn't finish coding".

**Always check the filesystem after a subagent timeout:**
```bash
cd /home/sean/.hermes/hermes-web-computer && git status --short
```
If files are modified or new files exist, the work is done. Review diffs, fix any issues (especially import block corruption in `multiplexer.go` from duplicate patches), and commit. Don't re-run the task.

**Pattern observed:** Subagents make 20-40 API calls, modify 6-16 files, then time out. The code changes are always complete; the summary/response generation is what times out.

**Phase 5 observation (Electron build):** Even when the subagent completes all file writes, it times out before the terminal output (build stdout/stderr) is shown to the orchestrator. This means the orchestrator sees empty stdout and might incorrectly assume the build failed. Always verify with:
```bash
cd /home/sean/.hermes/hermes-web-computer && git status --short  # files on disk
cd /home/sean/.hermes/hermes-web-computer/desktop && npx vite build  # rebuild to confirm
```

**Go build verification after subagent:** Always run `go build -o /tmp/hwc-server ./cmd/server/` after multi-agent patches. Common issues:
- Import block corruption (duplicate `import (` or removed imports like `nhooyr.io/websocket`)
- Unused `uuid` import if the subagent doesn't use it
- For persistent issues, fix the import block by writing the entire import block cleanly rather than patching.

### Dock Panel Feature Pattern

Dock items with `isPanelFeature: true` (Profiles, Skills, Crons, Memory, Settings) don't create tiles — they switch the RightPanel tab. The pattern:

**In Dock.svelte `handleLaunch`:**
```typescript
function handleLaunch(item: DockItem) {
  if (item.isPanelFeature) {
    window.dispatchEvent(new CustomEvent('hwc-dock-panel', { detail: { panel: item.type } }))
    activeApp = activeApp === item.id ? null : item.id
    return
  }
  // ... tile creation for non-panel features
}
```

**In RightPanel.svelte:**
```typescript
onMount(() => {
  const handleDockPanel = (e: Event) => {
    const detail = (e as CustomEvent).detail as { panel: string }
    if (detail.panel === "profiles") activeTab = "profiles"
    else if (detail.panel === "skills") activeTab = "skills"
    else if (detail.panel === "crons") activeTab = "crons"
    else if (detail.panel === "memory") activeTab = "memory"
    else if (detail.panel === "settings") activeTab = "settings"
  }
  window.addEventListener("hwc-dock-panel", handleDockPanel)
  return () => window.removeEventListener("hwc-dock-panel", handleDockPanel)
})
```

RightPanel's tab content uses `{#if activeTab === "profiles"}<ProfilePanel />{/if}` blocks. RightPanel must import all panel components at the top.

### Workspace Store with localStorage Persistence

The workspace system uses a Svelte writable store that auto-saves to localStorage:

```typescript
import { writable, get } from "svelte/store"

export const workspaceStore = writable<WorkspaceState>(initialState)

// Auto-save on every change
workspaceStore.subscribe((state) => {
  try {
    localStorage.setItem("hwc-workspaces-v1", JSON.stringify(state))
  } catch {}
})

// In components, use $derived for reactivity:
let wsState = $derived($workspaceStore)  // NOT let $ws = $state(...)
```

**Critical:** Never use `$` prefix for variable names (e.g., `let $ws = ...`) — Svelte 5 reserves `$` for runes and store subscriptions. Use `let wsState = $derived($workspaceStore)` instead.

### Git: Update Already-Pushed Commits (rebase + force-push)

When a commit has already been pushed to origin but needs to be updated (e.g., FEATURE-TRACKER.md update missed the original commit, or amend needed):

```bash
# 1. Make your changes
git add <files>
git commit --amend --no-edit

# 2. Rebase to get latest remote
git pull --rebase origin main
# → If conflict: resolve, git add, git commit -m "merge", git rebase --continue

# 3. Force push (needed since rebasing rewrites history)
git push --force-with-lease origin main
```

**Common scenario:** Phase commit was pushed, but FEATURE-TRACKER.md update was a separate commit. Amend the phase commit to include the tracker update, pull --rebase (may conflict on the tracker), resolve with `--theirs` (take our phase version), then force-push. Commit hash changes — update PHASE_TRACKER.json accordingly.

### Discord notification failure (HTTP 403)
**Symptom:** `urllib.request.urlopen` returns `HTTP Error 403: Forbidden` when posting to Discord REST API v10.
**Root cause:** Missing `User-Agent` header (required by Discord API). Cloudflare proxy in front of Discord API also returns 403 for auth failures. Auth failure from Discord (bad token) also returns 403 — both look identical without the User-Agent header.

**Fix — always include `User-Agent: Hermes-Bot` header:**
```python
req = urllib.request.Request(
    f'https://discord.com/api/v10/channels/{channel}/messages',
    data=json.dumps({'content': msg}).encode(),
    headers={
        'Authorization': f'Bot {token}',
        'Content-Type': 'application/json',
        'User-Agent': 'Hermes-Bot'   # REQUIRED — Discord rejects requests without this
    },
    method='POST'
)
urllib.request.urlopen(req, timeout=15)
```

**Token location:** Stored in `/opt/data/.env` as `DISCORD_BOT_TOKEN` and `DISCORD_CHANNEL_ID` in this container env. On other hosts, check `/home/sean/.hermes/.env` or `/home/hermeswebui/.hermes/.env`. Use `grep DISCORD_BOT_TOKEN <path>` to locate without reading full file.

**Full working pattern (container cron job):**
```python
import urllib.request, json

env_text = open('/opt/data/.env').read()
lines = env_text.split('\n')
token = channel = None
for line in lines:
    if line.startswith('DISCORD_BOT_TOKEN='):
        token = line.split('=', 1)[1]
    if line.startswith('DISCORD_CHANNEL_ID='):
        channel = line.split('=', 1)[1]

url = f'https://discord.com/api/v10/channels/{channel}/messages'
data = json.dumps({'content': msg}).encode()
req = urllib.request.Request(url, data=data, headers={
    'Authorization': f'Bot {token}',
    'Content-Type': 'application/json',
    'User-Agent': 'Hermes-Bot'   # REQUIRED — Discord rejects without this
}, method='POST')
resp = urllib.request.urlopen(req, timeout=15)
print(f"Success: {resp.status}")
```

### Discord notification failure (HTTP 403)

For completing multiple remaining features (tile animations, workspace persistence, agent output drag, Lighthouse audit), use the **Persistent Phase Engine** pattern from the `autonomous-cron-pipeline` skill:

1. State directory: `/opt/data/hermes-web-computer-state/`
2. Tracker: `PHASE_TRACKER.json` with phase status and checkpoints (current_phase + phases[].status + phases[].commit)
3. Checkpoints: `CHECKPOINTS/phase-{id}.md`

This pattern survives context compaction, session timeouts, and agent restarts. See `autonomous-cron-pipeline` skill for full architecture.

## Migration Strategy

### From agent-os (React → Svelte 5)

1. Use repo-transmute v2 to extract component blueprints
2. Migrate top 3 pages first: Agent Status, Session History, System Metrics
3. Wire migrated tiles to Go backend (replace Express API routes)
4. Test with vision verification

### From hermes-webui (Python/vanilla JS → Go/Svelte5)

**Confirmed 2026-05-25:** HWC replaces hermes-webui entirely. This is the primary goal alongside replacing agent-os.

| Feature from hermes-webui | HWC status | Action needed |
|---------------------------|-----------|---------------|
| Workspace file browser + inline preview | ❌ stub | Wire FileTree.svelte + add preview |
| Slash commands (`/` registry, 1302 lines) | ❌ missing | Add to frontend store |
| Onboarding wizard | ❌ missing | Add first-run flow |
| Session projects/tags | 🔶 partial | Expand sidebar sessions panel |
| Provider/model discovery | 🔶 partial | Wire profiles + model picker |
| Voice input | 🔶 partial | Wire MediaRecorder → backend |
| Session search | ⚪ not started | Add search to sessions panel |
| File upload | ✅ Complete | 2026-06-10 | Upload tile (standalone dock + ChatPanel drag-drop); writes to /tmp/uploads/ via fs.write |

### From agent-os (container management)

| Feature | HWC status | Notes |
|---------|-----------|-------|
| Nanobot (8900/8901/9120) | ⚪ not wired | HWC docker/manager.go exists, nanobot is higher-level |
| Hermes agent at 8642 | ⚪ not wired | HWC agent/streamer.go exists but frontend connects to agent-os |
| Session persistence (Postgres 5432) | ✅ JSON file store | Works, no Postgres needed |
| Cloudflare tunnel `fe36ddb5` | ✅ running | Keep tunnel, point to HWC |

### Inspiration Repositories (confirmed 2026-05-25)

The complete set of repos driving HWC development:
1. `outsourc-e/hermes-workspace` — React/Electron desktop (source for features-list extraction)
2. `ChonSong/features-list` — 629 components extracted from hermes-workspace via repo-transmute
3. `ChonSong/agent-os` — current live system (container management + nanobot at 8900/8901/9120)
4. `nesquena/hermes-webui` — Python/vanilla JS chat UI (being replaced by HWC)
5. `VoltAgent/awesome-agent-skills` (~1117 skills) + mattpocock/0xNyk/vercel-labs/expo skill repos

**Do NOT revive Byterover.** XPra is valid (not rejected).

## Key Protocols

### JSON-RPC Envelope

```json
{
  "protocol": "ui|agent|audio",
  "method": "layout.update|pty.write|tool.execute|...",
  "params": {...},
  "id": "request_id",
  "ts": 1234567890
}
```

### Server Events

```json
{
  "protocol": "ui|agent|audio",
  "event": "layout.delta|pty.output|approval.required|...",
  "data": {...},
  "ts": 1234567890
}
```

### Layout Operations

| Op | Description |
|----|-------------|
| `split` | Convert leaf to split with two children |
| `mount` | Add new leaf to tree |
| `unmount` | Remove leaf, merge with sibling |
| `resize` | Change relative size of child |
| `swap` | Swap positions of two leaves |
| `fullscreen` | Toggle fullscreen for leaf |

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Cmd/Ctrl+K` | Command palette |
| `Cmd/Ctrl+?` | Keymap overlay |
| `Shift+Arrow` | Focus adjacent tile |
| `Shift+Alt+Arrow` | Resize tile borders |
| `Shift+D` | Cycle layout modes (master-stack, even-split, columns, rows) |
| `Shift+F` | Toggle fullscreen on focused tile |
| `Shift+Q` | Close focused tile |
| `Shift+Space` | Toggle floating/tiled mode on focused tile |
| `Shift+1-9` | Switch workspace (each workspace has independent layout tree) |
| `Shift+Alt+1-9` | Move focused tile to another workspace (toggles floating mode) |
| `Ctrl+B` | Toggle left panel |
| `Ctrl+Shift+B` | Toggle right panel |

## Docker Compose

```yaml
services:
  agent-os:
    build: ../backend
    ports: ["3001:3001"]
    networks: [agent-net]
    volumes:
      - ../state:/agent/.state
      - ../telemetry:/agent/.telemetry

  hermes:
    image: nousresearch/hermes-agent:latest
    network_mode: host

  fun-audio:
    build: ../bridge
    network_mode: host
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  caddy:
    image: caddy:latest
    ports: ["80:80", "443:443"]
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - ../frontend/dist:/srv/frontend
```

## Validation Criteria

| Component | Metric | Target |
|-----------|--------|--------|
| Layout Engine | p99 layout render | <50ms |
| Security | Blocked `rm -rf` halts + red border | Works |
| Telemetry | Events written + synced | Works |
| Tile Engine | Recursive layout, keyboard nav, border states | Works |
| Audio Bridge | Opus relay + interrupt | Works |
| Integration | `docker compose up` → full flow | Works |
| Interrupt | Shift+Space to amber border | <100ms |

## Visual QA Pipeline
## Visual QA Pipeline

hermes-computer has a persistent gap: visual verification requires either Chrome on the host (SSH) or fixing the Svelte 5 `effect_orphan` bug.

### The Loop

```
Reference screenshot(s) or URL
        ↓
Generate tile/component
        ↓
Serve the frontend (Go backend + static dist on port 3005 [new] or 3113 [old/tunneled])
        ↓
Chrome headless → screenshot (900× virtual-time-budget tuned per app)
        ↓
Vision model → similarity score vs reference (threshold: ≥0.85)
        ↓ fail
Fix specific CSS/token differences (targeted, not wholesale)
        ↓
Re-screenshot → re-compare (iterate until pass)
        ↓ pass
Commit
```

### Chrome Headless Screenshot Prerequisites

**CRITICAL — virtual-time-budget tuning:** The default `virtual-time-budget=5000` (5s) is almost always too short — JavaScript doesn't execute, resulting in a WHITE screenshot. Tune per app:
- HWC (Svelte SPA): `30000` (30s) minimum
- agent-os (React, slower): `60000` (60s)

**Chrome binary:** Always `/usr/bin/google-chrome-stable` on the EndeavourOS host — NOT `chromium`, `chromium-browser`, or any other variant.

**Command pattern (SSH to host, all on one line):**
```bash
ssh sean@172.19.0.1 \
  "google-chrome-stable --headless --disable-gpu --no-sandbox \
    --virtual-time-budget=30000 --window-size=1440,900 \
    --screenshot=/tmp/hwc-qa/screenshots/current.png \
    --disable-web-security http://localhost:3005 2>/dev/null && echo CAPTURED"
```

**Python subprocess pattern (escaping the remote command in double-quotes):**
```python
f"ssh -i {SSH_KEY} -o StrictHostKeyChecking=no -o LogLevel=ERROR sean@172.19.0.1 \\\"{cmd}\\\""
```
Where `cmd` is the chrome command WITHOUT outer quotes. Python handles the inner quoting.

### Server Detection — Which Port?

Two servers may be running simultaneously on the host:
- **Port 3005 (NEW):** `agent-os server --port 3005` — serves hermes-web-computer frontend (Go backend + Svelte SPA). Title tag: `<title>Agent-OS v1.2</title>`. JS chunk: `index-D*.js` (hash changes per build).
- **Port 3113 (OLD/TUNNELED):** Legacy agent-os or SSH port-forwarded tunnel. No title tag or returns empty.

**Detect by HTTP response:**
```bash
curl -s http://localhost:3005/ | grep -E "title|script.*src"  # Returns JS chunk → HWC
curl -s http://localhost:3113/ | grep -E "title|script.*src"  # Returns empty → tunnel or old server
```

**Detect by process:**
```bash
ps aux | grep "agent-os.*--port 3005" | grep -v grep  # NEW server process
ss -tlnp | grep 3005                                  # NEW server port binding
```

**Always check port 3005 first** — if nothing on 3005, fall back to 3113. If neither responds, start the server:
```bash
ssh sean@172.19.0.1 \
  "cd /home/sean/.hermes/hermes-web-computer/backend && \
   HERMES_HWC_ROOT=/home/sean/.hermes/hermes-web-computer \
   nohup ./agent-os server --port 3005 > /tmp/hwc-server.log 2>&1 &"
```

### Visual QA Workflow
1. **Capture reference screenshot** — navigate to the reference URL or use a stored reference image
2. **Detect running server** — check ports 3005 and 3113, start if needed
3. **Capture screenshot** — chrome headless with tuned `virtual-time-budget`
4. **Vision compare**: use `vision_analyze` or `browser_vision` (annotate=true) to score similarity
5. **Fix**: targeted CSS/token changes, not rewrites
6. **Re-verify**: re-screenshot and compare
7. **Commit only after pass**

### Prerequisites (Install First)

```bash
# 1. Install Chromium for Playwright
apt-get install -y chromium
export CHROMIUM_PATH=/usr/bin/chromium

# 2. Install Playwright browsers
cd /home/hermeswebui/.hermes/hermes-web-computer/frontend
npx playwright install chromium --with-deps

# 3. Start the Go backend serving static files
cd /home/hermeswebui/.hermes/hermes-web-computer/backend
HERMES_HWC_ROOT="/home/hermeswebui/.hermes/hermes-web-computer" \
  /tmp/hwc-server &
# verify: curl -s -o /dev/null -w "%{http_code}" http://localhost:3113/
```

### Visual QA Workflow

1. **Capture reference screenshot** — navigate to the reference URL or use a stored reference image
2. **Start backend** if not running: `HERMES_HWC_ROOT=... /tmp/hwc-server &`
3. **Run Playwright screenshot**: `npx playwright test e2e/tests/visual/ --update-snapshots`
4. **Vision compare**: use `browser_vision` (annotate=true) to analyze what differs
5. **Fix**: targeted CSS/token changes, not rewrites
6. **Re-verify**: re-screenshot and compare
7. **Commit only after pass**

### For New Tiles

Always start with a visual reference (screenshot, URL, or key visual elements from ILLOGICAL-IMPULSE-DESIGN.md). The reference drives the generation — without it, the output is unconstrained.

### Reference: `references/visual-qa-pipeline.md`

See `references/visual-qa-pipeline.md` for the full pipeline script, threshold guidelines, and multi-layer verification fallback (DOM inspection → snapshot → vision, using each sparingly).

**Recent fix (2026-05-24):** The top bar (WorkspacePill) was `#65626c` instead of `#1c1c1d`. Fixed with inline style `style="background-color: #1c1c1d; opacity: 0.95;"` — class-based Tailwind (`bg-black/40`) couldn't hit the exact pixel. Full analysis in `references/visual-qa-top-bar-fix.md`.

## Container Browser Execution Model

**Chrome headless works in the container** with LD_LIBRARY_PATH pointing to pre-extracted Chrome libs at `/home/hermeswebui/.local/chrome-libs/` (124 .so files: libglib-2.0, libnss3, libX11, libcairo, libpango, etc.). Chrome 148 binary at `~/.hermes/hermes-web-computer/.playwright/chromium-1223/chrome-linux64/chrome`.

**However, the HWC Svelte 5 SPA does NOT render in headless Chrome** from the container — the app crashes immediately with `effect_orphan` runtime error. Root cause: `layout.svelte.ts` uses `createSubscriber` + `$state` runes, but `ws.ts` calls `layoutState.setLayout()` (which assigns `$state`) on the first WebSocket event, before any component has subscribed (which would happen inside its render context). Svelte 5 throws `effect_orphan` because `$state` is mutated outside component initialization. Result: blank white page (4-8KB screenshots vs 91-97KB for working captures).

Fix needed: defer the first `setLayout()` call until a component subscribes, or use Svelte stores instead of `createSubscriber` + `$state` for the layout state.

**Fallback: SSH to host.** When Chrome-in-container can't render the SPA, the host has working `google-chrome-stable`:

```bash
# From the hermes-webui container (NOT cron container):
ssh sean@172.19.0.1 \
  "google-chrome-stable --headless --disable-gpu --no-sandbox \
    --virtual-time-budget=30000 --window-size=1440,900 \
    --screenshot=/tmp/hwc-qa/screenshots/current.png \
    --disable-web-security http://localhost:3005 2>/dev/null && echo CAPTURED"
```

**Note (2026-06-10):** SSH key path `/home/hermeswebui/.hermes/container_key` may not exist. The key at `~/.ssh/id_ed25519` exists but may not be authorized on the host (Permission denied for sean@172.19.0.1). SSH auth needs re-verification.

**Always-available verification (no browser required):**

When Chromium isn't available, fall back to **layered verification**:

1. **DOM inspection** — examine CSS classes, computed styles via browser_console
2. **HTTP response inspection** — verify `index.html` links to correct CSS bundle, JS chunks have expected hashes
3. **Built CSS audit** — `grep` the built CSS file for design tokens (faster than screenshot):
   ```bash
   grep -c "backdrop-blur-xl\|bg-\\[\\#12121a\\]\|border-white/10" \
     /home/hermeswebui/.hermes/hermes-web-computer/frontend/dist/assets/*.css
   ```
4. **Source audit** — verify glassmorphism classes in component files match spec
5. **SSH to host** — if Chrome-in-container fails the SPA, `ssh sean@172.19.0.1` has working `google-chrome-stable`

### Scripts for Host-Side Execution

| Script | Purpose | Runs on |
|--------|---------|---------|
| `scripts/visual-qa.sh` | Chrome CLI screenshot + ImageMagick diff vs baseline | Host (EndeavourOS) |
| `scripts/setup-xpra.sh` | Install xpra (AUR), create systemd user service, start on :10 with HTML5 on 9453 | Host (EndeavourOS) |
| `scripts/install-browser-deps.sh` | Install Chromium + Playwright on EndeavourOS | Host |
| `scripts/run-e2e-on-host.sh` | Wrapper to run E2E suite on host with results copied back | Host |

### Canonical Paths (Host vs Container)

**On the EndeavourOS host** the repo lives at `/home/sean/.hermes/hermes-web-computer`. The container maps it differently:

| Context | Path |
|---------|------|
| Host shell (builds, Go, Chrome) | `/home/sean/.hermes/hermes-web-computer` |
| Container (this env, read-only sync) | `/home/hermeswebui/.hermes/hermes-web-computer` |
| Backend port (direct) | `localhost:3005` (new HWC server, Go+Svelte5) |
| Backend port (tunnel) | `localhost:3113` (legacy SSH tunnel, verify with curl first) |
| Cron QA screenshot dir (host) | `/tmp/hwc-qa/` |
| Built frontend dist (host) | `/home/sean/.hermes/hermes-web-computer/frontend/dist/` |

**The HWC backend runs on the host** at port 3005, started by `agent-os process` via `./agent-os server --port 3005`. The frontend SPA is served from `frontend/dist/`. The old server at port 3113 is no longer reliable for visual QA — always use port 3005.

### Pre-Commit Visual QA Checklist

- [ ] Go backend builds: `go build -o /tmp/hwc-server ./cmd/server/` (on host)
- [ ] Backend health: `curl -s -o /dev/null -w "%{http_code}" http://localhost:3113/` returns 200
- [ ] Run visual QA on host: `bash /home/sean/.hermes/hermes-web-computer/scripts/visual-qa.sh` (or Python: `python3 /home/sean/.hermes/hermes-web-computer/e2e/scripts/visual_compare.py --compare`)
- [ ] Check diff output — if > 1%, fix CSS/tokens before committing
- [ ] Commit only after visual pass

### Baseline Screenshots

Baselines live on the **host** at `/tmp/hwc-qa/baselines/`. Fresh baselines captured **2026-06-10** from host Chrome:

| Resolution | Size | Notes |
|-----------|------|-------|
| 1440x900 | 114KB | Canonical — shows full HWC with terminal, chat, sidebar, dock |
| 1280x720 | 104KB | Alternative |
| 1920x1080 | 129KB | Widescreen |

The HWC Visual QA cron job (`fcf273002361`) runs every 12h via container script → SSH to host → `bash ~sean/.hermes/scripts/hwc-host-visual-qa.sh`. The host script captures a fresh screenshot and compares file-size against baseline. Tolerance: <10% diff = PASS. The container script at `~/.hermes/scripts/hwc-visual-qa.sh` is a thin wrapper that SSHs to the host and delegates.

Container-side Chrome (with LD_LIBRARY_PATH) produces blank screenshots (4-8KB) due to the Svelte 5 `effect_orphan` bug — always use host-side QA until fixed.

### Critical Prerequisite Check

Before attempting any visual QA:

```bash
# Verify Chromium is installed — use google-chrome-stable (already on host!)
which google-chrome-stable || echo "NOT FOUND"

# Verify Go backend can build and serve static files
ssh sean@172.19.0.1 \
  "cd /home/sean/.hermes/hermes-web-computer/backend && go build -o /tmp/hwc-server ./cmd/server/"

# Start server (if not already running)
ssh sean@172.19.0.1 \
  "curl -s -o /dev/null -w '%{http_code}' http://localhost:3113/"

# Quick screenshot capture (no Playwright needed — Chrome CLI works)
ssh sean@172.19.0.1 \
  "google-chrome-stable --headless --disable-gpu --no-sandbox \
    --virtual-time-budget=10000 --window-size=1440,900 \
    --screenshot=/tmp/hwc-qa/screenshots/quick.png \
    --disable-web-security http://localhost:3113 2>/dev/null && \
  echo 'Screenshot OK' && ls -la /tmp/hwc-qa/screenshots/quick.png"
```

**Note:** `google-chrome-stable` is installed at `/usr/bin/google-chrome-stable` on the host — **not** `chromium`, `chromium-browser`, or any other Chromium variant. Use this exact path/binary name.

## Pitfalls

- **Generate and commit without verification** — This is the default failure mode. Every tile that gets committed without a visual QA pass is a tile that probably looks wrong. Always run visual QA before commit, even if just a quick `browser_vision` check against the spec.
- **PTY output flow** — Must forward to both ring buffer AND output channel
- **Security default** — Default to "safe" tier, not "block"
- **Static file serving** — Check absolute path first to avoid stale dist dirs. The `Router()` in `multiplexer.go` checks a list of paths in order:
  ```go
  distPaths := []string{
      "./frontend/dist",  // ← MUST be first when running from project root
      "/opt/data/hermes-web-computer/frontend/dist",
      "../frontend/dist",
      "../../frontend/dist",
  }
  ```
  If none match, the server returns 404 for all routes except `/ws` and `/health`. The server binary runs from the project root (`~/hermes-web-computer`), so `./frontend/dist` is the only path that works from there. Always add `./frontend/dist` first when adding a new dist path.
- **Svelte 5 syntax** — `onclick` not `on:click`, `$props()` not `export let`, `$state()` not `$:`
- **Svelte 5 `{/* */}` comments** — Svelte 5.55+ fails to compile `{/* */}` in template sections. Use `<!-- -->` or strip them.
- **Svelte 5 `effect_orphan` crash (two sources)** — The `https://svelte.dev/e/effect_orphan` error occurs when `$state`/`$effect`/`$derived` is used outside component initialization. Two common triggers in HWC:
  - **Source 1 (definitive, blocks visual QA):** `layout.svelte.ts` uses `createSubscriber` + `$state` runes. `ws.ts` calls `layoutState.setLayout()` (which assigns `$state`) on the first WebSocket event (line 197), but NO component has subscribed via the getters yet (which would happen inside its render context). Svelte 5 throws `effect_orphan` because `$state` is mutated before any component establishes an effect context. This happens consistently when loading HWC from a non-localhost origin (e.g., Docker bridge IP). Fix: defer the first `setLayout()` call until `layoutState.tree` is accessed by a component, or replace `createSubscriber` with a plain Svelte store.
  - **Source 2:** Tests that import `layout.svelte.ts` at module level before any component mounts.
- **Svelte 5 `effect_orphan` blocks visual QA** — Until fixed, container-based screenshot capture via Chrome headless produces blank white images (4-8KB). The `hwc-visual-qa.sh` script detects this via size heuristic (<10KB = WARN). The only working visual QA path is host-side Chrome via SSH.
- **Tailwind v4 config** — Uses CSS-based `@theme` directive in `frontend/src/styles/glass.css`, NOT `tailwind.config.js`. Add custom colors, shadows, animations via `@theme` block in CSS.
- **Illogical Impulse design system** — Glassmorphism theme: `backdrop-blur-xl bg-[#12121a]/90 border-white/10 rounded-2xl shadow-panel`. Active tiles get `border-glass-border-active ring-1 ring-purple-500/20`. Workspace pill (top-center), floating dock (bottom-center). Full spec: `ILLOGICAL-IMPULSE-DESIGN.md` in planning repo.
- **AGENTS.md pattern** — Every repo in the ecosystem should have an `AGENTS.md` for AI agent consumption: what it is, key files, quick commands, integration points. Create alongside README rewrites.
- **Svelte 5 `$state(prop)` anti-pattern** — Can't initialize `$state()` with a prop. Use `$state("")` + `$effect(() => { val = prop })`.
- **Svelte 5 handler param naming** — Don't name handler params the same as `$state` variables (causes shadowing).
- **Subagent timeouts** — Subagents complete code changes but timeout before commit. Always `git status --short` after timeout — work is on disk. Common issue: import block corruption in multiplexer.go (duplicate `import (` or removed imports). Fix by writing the import block cleanly. Always verify with `go build -o /tmp/hwc-server ./cmd/server/`.
- **WebSocket routing** — Route ordering matters: `/ws` before `/`
- **Layout tree** — Max depth 3, lazy-mount Monaco/xterm on viewport entry
- **Path sandboxing** — `sanitizePath()` in `ws/filesystem.go` strips `../` traversal and joins with `allowedRoot`. Default `allowedRoot` is `/opt/data/hermes-web-computer` in container env, `/home/sean/.hermes/hermes-web-computer` on host. `HERMES_HWC_ROOT` env var overrides. Tests MUST set `HERMES_HWC_ROOT=/opt/data/hermes-web-computer` to match the actual repo root.
- **Playwright selectors** — Avoid `getByText('Agent')` strict mode violations (matches multiple elements). Use `getByRole('heading', {name:'Agent'})` or `getByRole('textbox', {name:'Type a message...'})` for unique selectors.
- **Integration test timeouts** — WebSocket tests on httptest need 15-30s context timeouts, not 5s. PTY startup adds latency.
- **Go test mock sessions** — Use `drainEvents(sess)` helper that reads from `sess.send` channel (buffered, non-blocking) instead of trying to intercept `Send()` calls.
- **Go `write_file` lint false-positive** — When creating Go files in the ws/ package, the linter may report `undefined: Multiplexer` even though `go build` succeeds. This is a linter bug in the file write context. Always verify with `go build ./...` and `go vet ./...` — if those pass, the file is correct.
- **Layout pty_id location** — `layout.initial` event nests `pty_id` inside `data.tree.pty_id`, not at root level. Integration tests must assert this structure.
- **Svelte 5 duplicate script blocks** — If a merge or subagent creates a second `<script>` block after `</style>`, the build fails with `error TS2591: script_duplicate`. Fix by removing the second block entirely and ensuring all variables live in the first `<script lang="ts">` at the top of the file.
- **Layout state persists across WebSocket connections** — The `m.layout` object in `multiplexer.go` is a shared singleton. When a browser connects and splits the layout, `m.layout` becomes a split. When a new browser connects (or the same browser reconnects), `m.layout` is still a split, so trying to split again fails with "cannot split a split node". **Fix:** Reset `m.layout = layout.NewRoot("xterm")` at the start of each new WebSocket session in `HandleWebSocket`. This was the root cause of chat tiles not appearing after clicking "+ New Chat" a second time — the backend had already been split from the first click.
- **Browser tile requires Chromium** — On Linux, the browser tile needs `chromium` installed. The backend looks for `google-chrome` in `$PATH` by default. Set `CHROMIUM_PATH=/usr/bin/chromium` env var when starting the server. Install with `apt-get install -y chromium`.
- **browser_id propagation in layout tree** — When a browser tile is launched, `apps.launch.response` returns a `browser_id`. This must flow through `layout.update` (split/mount op) into the `LayoutTree.BrowserID` field. Without it, the Browser.svelte component has no CDP endpoint to connect to. Ensure `BrowserID` is copied in `applySplit` and `applyMount` in `tree.go`, and passed in the frontend's `layout.update` message.
- **WebSocket debug logging pattern** — For debugging event flow across Svelte modules, use `globalThis` with a type assertion to store event arrays: `const win = globalThis as typeof globalThis & { __wsEvents?: Event[] }; if (!win.__wsEvents) win.__wsEvents = []; win.__wsEvents.push(event)`. This avoids TypeScript `window.__wsEvents` errors. Access from browser console as `window.__wsEvents`.
- **Debug WebSocket event handler registration** — Add logging to the `on()` function to confirm handlers are registered: `console.log('[WS] Handler registered for', event, 'total:', handlers.get(event)?.size)`. This reveals if event names don't match between send and receive.
- **Port conflict with hermes-webui (3001)** — HWC backend defaults to port 3005 (new server) or 3113 (old/tunneled). If that or any other port is in use, change it in THREE places:
  1. `backend/cmd/server/main.go` — `port = "3005"` (or desired port)
  2. `frontend/src/stores/ws.ts` — `export function connect(url: string = "ws://localhost:3005/ws")`
  3. `frontend/vite.config.ts` — proxy target `ws://localhost:3005` (secondary, dev server proxies optional)

  The frontend connects **directly** to the WebSocket URL from `ws.ts`, not through the Vite proxy. Update `ws.ts` first and always. Never kill or repurpose the hermes-webui port (3001).

- **Two-server confusion (3005 vs 3113):** The host may run `agent-os server --port 3005` (HWC, Go+Svelte5) while an SSH tunnel forwards `localhost:3113` to a different service. Always `curl` the title tag to identify which server is serving which content. Screenshot comparison between different servers produces meaningless results. Verify you're screenshots against the right server.
- **findLeaf safe split pattern** — When splitting a layout to add a tile, don't split "root" directly if it's already a split node. Use a recursive `findLeaf()` to locate the first leaf node, then split that. This avoids "cannot split a split node" errors:
  ```typescript
  function findLeaf(node: LayoutTree, path: string): string | null {
    if (node.type === 'leaf') return path
    if (node.children) {
      for (const child of node.children) {
        const found = findLeaf(child, child.id)
        if (found) return found
      }
    }
    return null
  }
  const targetId = layoutState.tree ? findLeaf(layoutState.tree, layoutState.tree.id) : "root"
  sendOp({ op: "split", target_id: targetId ?? "root", direction: "v", content: "chat", size: 0.5 })
  ```
- **ChatPanel streaming state** — ChatPanel should NOT manage its own streaming state (local `streaming`, `streamingContent` vars + manual `on("chat.streaming")`/`on("chat.reply")` cleanup). It should use `sessionStore.send()` which handles the five-event accumulation model. ChatPanel reads live buffer via `sessionStore.getBuf(sid)` in its `$derived` message list. See `references/agent-streaming.md`.
- **Go import block corruption in multi-agent patches** — When patching `multiplexer.go` with multiple agents in the same session, the `import (...)` block can get corrupted (duplicate `import (` keyword, removed imports like `nhooyr.io/websocket`). Always verify with `go build -o /tmp/hwc-server ./cmd/server/`. If `import (...)import (` appears, fix by writing the entire import block cleanly.
- **Session tile UI pattern** — Chat tile uses `ChatPanel.svelte` + `sessions.svelte.ts` store. `SessionsPanel` handles session CRUD and calls `sessionStore.select(id)`. `ChatPanel` tile reacts to `sessionStore.activeSession` and streams tokens via the five-event model (`chat.token`/`chat.reasoning`/`chat.tool_call`/`chat.tool_result`/`chat.reply`). Both use `$state`/`$derived`/`$effect`. Optimistic user messages added to store before send. `chat.error` shows error state. Full pattern in `references/agent-streaming.md`.
- **ChatPanel streaming pattern** — Uses `on()` cleanup functions returned from WS event listeners, stored in an array and run in `$effect` cleanup. Streaming content shown live while `chat.streaming` events arrive. `chat.reply` finalizes message; `chat.error` shows error state.

## Repo Ecosystem — Critical Production Topology

The ChonSong ecosystem has 6 repos that are **all different things**. Before planning, investigating, or consolidating, understand what's actually running:

```
ACTIVE DEVELOPMENT:
  hermes-web-computer  → tiling AI desktop (Go+Svelte5), dev, port 5174
  seans-reporepo       → catalog of all ChonSong repos, cron Mon 9am

LIVE PRODUCTION:
  agent-os             → React dashboard (port 3001 via Cloudflare tunnel)
                          ACTIVE system, not legacy — runs cron, serves sessions,
                          manages Docker — do NOT treat as migration source

EXTERNAL (not ChonSong):
  hermes-workspace     → outsourc-e/React Electron app (794MB, separate product)
  nesquena/hermes-webui → Python vanilla-JS, 5303 tests, full feature set
                          This IS the production web UI for Hermes Agent.
                          Clone with: git clone --depth 1 https://github.com/nesquena/hermes-webui.git /tmp/hermes-webui

ARCHIVE CANDIDATE (docs only):
  hermes-computer-planning → all content moved to hermes-web-computer/docs/
```

**The canonical source of truth for hermes-webui features is `/tmp/hermes-webui/`** after cloning. Key files to read:
- `ARCHITECTURE.md` — full tech spec (1640 lines, authoritative)
- `api/streaming.py` — SSE engine, agent thread runner, cancel support
- `api/models.py` — session model, in-memory store, FTS index management
- `api/routes.py` — all HTTP route handlers (~9772 lines)
- `static/panels.js` — cron, skills, memory, workspace, profiles panels
- `README.md` — features, quick start, Docker setup

**The canonical source of truth for features-list is `/opt/data/features-list/`** (already cloned locally).

## Ecosystem Investigation Workflow (Before Planning)

When starting work that touches multiple repos, map the ecosystem first:

```bash
# 1. Check what's actually running (critical — don't assume)
curl -s http://localhost:3001/health 2>/dev/null && echo "agent-os: LIVE on 3001"
curl -s http://localhost:8787/health 2>/dev/null && echo "hermes-webui: LIVE on 8787"

# 2. Check all ChonSong repos
ls -d /opt/data/hermes-*/

# 3. Check hermes-web-computer backend packages
ls /home/sean/.hermes/hermes-web-computer/backend/

# 4. Clone external references as needed
git clone --depth 1 https://github.com/nesquena/hermes-webui.git /tmp/hermes-webui

# 5. Check features-list COMBINATORIAL.md (may be empty/missing)
wc -l /opt/data/features-list/COMBINATORIAL.md 2>/dev/null
```

**What NOT to do:**
- Don't merge `agent-os` into `hermes-web-computer` — they're different stacks (React+Express+Postgres vs Go+Svelte5) and `agent-os` is live in production
- Don't archive `agent-os` without knowing it can be retired (check if cron jobs, sessions, or observability data would be lost)
- Don't call `nesquena/hermes-webui` "legacy" — it has 5303 tests and is more mature than anything else in the ecosystem

**What TO do:**
- Move planning docs from `hermes-computer-planning` into `hermes-web-computer/docs/` then archive the planning repo
- Study `nesquena/hermes-webui` for proven patterns (sessions, streaming, profiles, skills, cron, memory)
- Treat `hermes-web-computer` as the **new tiling desktop** being built, separate from the existing products

## Repo Consolidation

The three-repos structure (`hermes-web-computer` / `agent-os` / `hermes-computer-planning`) reflects a real division: new dev target, old running system, and research docs. Merging all three into one repo would destroy the distinction and create confusion.

Archive candidates:
- `hermes-computer-planning` — docs-only, no code, no CI, no tests. Safe to archive after moving content to `hermes-web-computer/docs/`.
- `agent-os` — NEVER archive while cron jobs, observability, or active sessions depend on it.

## Reference Files

- `references/ssh-host-access.md` — SSH connection details, path mapping, verified host key

## Testing

### Backend (Go)

45+ tests across filesystem handlers, app protocol, WebSocket integration, layout engine, security, and benchmarks.

```bash
cd backend && go test ./... -count=1 -timeout=120s
```

Key patterns:
- `mockSession` with buffered `send` channel + `drainEvents()` for event capture
- `setupTestServer()` + `connectWS()` for integration tests
- `readEventsUntil()` with context timeouts for async WebSocket responses
- `sanitizePath` tests verify path sandboxing (not rejection) for absolute paths

## E2E Testing (Playwright)

17+ Playwright tests across 6 categories (Chromium only).

```bash
npx playwright test e2e/tests/01-layout.spec.ts  # single test
npx playwright test e2e/tests/workflows/          # workflow suite
```

### Running from Container (SSH to Host)

The container lacks `libglib-2.0.so.0` required by Chromium browsers. Use the remote config to run E2E tests on the host:

```bash
cd ~/.hermes/hermes-web-computer/e2e

# Ensure HWC server is running on host port 3005
ssh sean@172.19.0.1 \
  "curl -s -o /dev/null -w '%{http_code}' http://localhost:3005/"

# Run smoke tests via SSH (HWC server must be running)
ssh sean@172.19.0.1 \
  "cd ~/.hermes/hermes-web-computer/e2e && \
   npx playwright test smoke.spec.ts --project=chromium --config=playwright.remote.config.ts"

# Run full suite
ssh sean@172.19.0.1 \
  "cd ~/.hermes/hermes-web-computer/e2e && \
   npx playwright test --project=chromium --config=playwright.remote.config.ts"
```

The remote config (`playwright.remote.config.ts`) uses `baseURL: 'http://172.19.0.1:3005'` to point at the host's HWC server. Test fixes like the smoke spec URL regex (`/:3005\//` instead of `/localhost:3005/`) make the same tests work locally and remotely.

### PLAYWRIGHT_BROWSERS_PATH

Before running E2E tests, check for a stale `PLAYWRIGHT_BROWSERS_PATH` env var:

```bash
echo $PLAYWRIGHT_BROWSERS_PATH
```

If set to a non-existent path (e.g., `/opt/data/...`), Playwright can't find browsers. Fix with `unset PLAYWRIGHT_BROWSERS_PATH` or update to the current project path. See `e2e-testing` skill for the full trap description.

Config: `playwright.config.ts` with auto-start Go backend via `webServer`.

### Test Categories

| Category | Files | Description |
|----------|-------|-------------|
| Functional | `01-layout`, `02-resize` | Layout renders, column resizing |
| Workflows | `workflows/*.spec.ts` | File edit, multi-terminal pipeline, chat context, session recovery, cross-panel |
| Chaos | `chaos/*.spec.ts` | Concurrent tabs, server disconnect recovery |
| A11y | `a11y/keyboard.spec.ts` | Tab navigation, focus rings, keyboard shortcuts |
| Visual | `visual/baseline.spec.ts` | Baseline screenshots for regression |
| Perf | `perf/load-time.spec.ts` | TTFB, DCL, paint timings, bundle size |

### Selector Cheat Sheet

| Target | Selector | Why |
|--------|----------|-----|
| Terminal tile | `div.rounded-2xl` | Unique rounded-2xl class on Tile component (NOT `border-blue-500` — that class was removed in v1.4 theme refactor) |
| Left panel tabs (v1.4 icon-only) | `getByRole('button', { name: '📁' })` | v1.4 LeftPanel uses icon-only tabs; `getByText('📁 Files')` fails because only the emoji is visible, not the text label |
| Left panel tab (text label, v1.3) | `getByRole('button', { name: 'Files' })` | v1.3 had text labels; v1.4 icon-only broke these selectors |
| Agent heading (v1.3) | `getByRole('heading', { name: 'Agent' })` | Replaced in v1.4 by tab button `getByRole('button', { name: '💬 Chat' })` |
| Right panel tab (v1.4) | `getByRole('button', { name: '💬 Chat' })` | RightPanel uses tab buttons with emoji+text, not heading elements |
| Dock 📁 button | `getByRole('button', { name: '📁' })` | Dock uses `aria-label="Files"` on icon-only Dock button; unambiguous when LeftPanel tabs use the same pattern |
| Chat input | `getByRole('textbox', { name: 'Type a message...' })` | Distinguishes from xterm textarea |
| Resize handles | `.cursor-ew-resize` | Unique class on ResizeHandle |
| Main container | `div.h-screen` or `.bg-gray-950` | Root layout div |

### Common Pitfalls

- `getByText('Agent')` strict mode violation — matches "Agent-OS v1.2", "Agent" heading, and agent message text. Use `getByRole('heading', {name:'Agent'})` instead.
- `getByRole('textbox')` strict mode violation — matches both xterm helper textarea and chat input. Use specific `name` param.
- `div[tabindex="0"]` doesn't match — Tile uses `border-blue-500` class for identification, not tabindex.
- Disconnected state test: page connects immediately on server start, so "Disconnected" state is never visible. Test the connected state instead.
- Baseline visual tests: use `--update-snapshots` after intentional UI changes.
- Concurrent tab tests: use `context.newPage()` to open tabs in same browser context.
- Chaos server-death test: use `test.skip()` since `webServer` manages the lifecycle. Test disconnect via `context.setOffline()` instead.

### E2E Selector Pattern: Icon-Only Tabs (v1.4 Breaking Change)

When a UI redesign changes from text labels to icon-only buttons, selectors that use text content break silently. The fix pattern:

```typescript
// BEFORE (v1.3 — text labels)
await expect(page.getByText('📁 Files')).toBeVisible()
await expect(page.getByText('🚀 Apps')).toBeVisible()

// AFTER (v1.4 — icon-only)
await expect(page.getByRole('button', { name: '📁' })).toBeVisible()
await expect(page.getByRole('button', { name: '🚀' })).toBeVisible()
```

**Rule:** When `getByText` fails for elements that should exist, check if the text was removed in a UI redesign. Use `getByRole('button', { name: 'emoji' })` for icon-only buttons. The `name` attribute on buttons is the accessible name, which matches the emoji character.

### E2E Playwright Browser Path in Containerized Environments

**Problem:** Playwright downloads browsers to `$HOME/.cache/ms-playwright/` which is `/opt/hermes/.playwright` — a permission-denied path in the container. Tests fail with "Executable doesn't exist at /opt/hermes/.playwright/chromium_headless_shell-...".

**Fix — install Chromium to a writable path:**
```bash
# Set writable browser cache BEFORE install and test
PLAYWRIGHT_BROWSERS_PATH=/opt/data/hermes-web-computer/.playwright \
  npx playwright install chromium

PLAYWRIGHT_BROWSERS_PATH=/opt/data/hermes-web-computer/.playwright \
  npx playwright test 01-layout.spec.ts --reporter=line
```

**Pre-installed browsers** may already exist at `/opt/data/.playwright/` or can be installed to `/opt/data/.cache/playwright/`:
```bash
# Install to writable cache
PLAYWRIGHT_BROWSERS_PATH=/opt/data/.cache/playwright npx playwright install chromium

# Run tests using that cache
PLAYWRIGHT_BROWSERS_PATH=/opt/data/.cache/playwright npx playwright test 01-layout.spec.ts

# Or use pre-existing cache at /opt/data/.playwright/ if it exists
PLAYWRIGHT_BROWSERS_PATH=/opt/data/.playwright \
  npx playwright test 01-layout.spec.ts 02-resize.spec.ts
```

The `PLAYWRIGHT_BROWSERS_PATH` env var must be set on BOTH `install` AND `test` commands. Without it on `test`, Playwright looks in the default (broken) path. Both `/opt/data/.cache/playwright` and `/opt/data/.playwright` are valid writable locations in this container.

- **Staged Changes Survive Sessions — Always Check git Status Before Assuming Work is Needed** — When resuming from a prior session (e.g., after a timeout or interrupted Phase N), **always run `git status --short` before assuming work is needed.** A prior session may have staged or uncommitted changes but died before committing. These persist across sessions.

  **Examples from this codebase:**
  - `backend/xpra/manager.go` and `backend/xpra/proxy.go` — fully implemented (512+ lines, wired into multiplexer.go) but never committed. The FEATURE-TRACKER listed them as "Not Created". They existed on disk all along.
  - Phase 12: `01-layout.spec.ts` and `02-resize.spec.ts` were modified but uncommitted.

  **Pattern:**
  ```bash
  cd /opt/data/hermes-web-computer && git status --short
  ```

  **Before implementing any feature the tracker says is missing**, first check: does the code already exist on disk? The FEATURE-TRACKER can be wrong or stale.  Don't build what's already built.

- `references/svelte5-store-reactivity-investigation.md` — Svelte 5 store reactivity investigation
- `references/svelte5-effect-orphan-investigation.md` — Svelte 5 `effect_orphan` crash investigation: `layout.svelte.ts` `$state` set outside component init before subscriber mounts. Blocks headless Chrome screenshots in container.
- `references/hermes-webui-tunnel-restore.md`
- `references/svelte5-store-reactivity-investigation.md` — Svelte 5 store reactivity investigation
- `references/svelte5-effect-orphan-investigation.md` — Svelte 5 `effect_orphan` crash investigation: `layout.svelte.ts` `$state` set outside component init before subscriber mounts. Blocks headless Chrome screenshots in container.
- `references/hermes-webui-tunnel-restore.md` — hermes.codeovertcp.com tunnel restore: credentials reconstruction, watchdog setup, run commands, discovery via Cloudflare API

## Related Skills

- `repo-transmute` — Migration engine for converting repos to tiles
- `hermes-agent` — Hermes Agent configuration and usage
- `svelte-development` — Svelte 5 development patterns

## References

- `references/visual-qa-scripts.md` — Visual QA scripts created 2026-05-23: `scripts/visual-qa.sh` (Chrome CLI capture + ImageMagick diff), `scripts/run-visual-qa.sh` (host-side cron runner), `e2e/scripts/visual_compare.py` (PIL pixel-diff with thresholds), `e2e/tests/visual-baseline.spec.ts` (Playwright test suite). All live in the hermes-web-computer repo.
- `references/ecosystem-map.md` — ChonSong repo ecosystem: hermes-web-computer vs agent-os vs hermes-computer-planning vs external (hermes-workspace). Clear ownership, archive recommendations.
- `references/integration-roadmap.md` — Master 6-phase plan for building the "best of all worlds" product: all features from hermes-webui + agent-os + hermes-workspace unified in Go+Svelte5. Source-of-truth per feature, phase order, parity checklist.
- `references/illogical-impulse-tokens.md` — Illogical Impulse design tokens: colors, glassmorphism patterns, Tailwind @theme config, component class patterns
- `references/component-dependencies.md` — Full dependency map, per-tile backend/frontend requirements, WS protocol extensions
- `references/browser-tile-debugging.md` — Browser tile debug session: app type mismatch root cause, browser_id propagation flow, WebSocket message sequence, Chromium setup, debug console commands
- `references/svelte5-vite-gotchas.md` — Svelte 5 `class:` directive `/` bug, Discord REST 403 with User-Agent, Vite foreground build block, dist/ timestamp trap, Go /tmp permission, HERMES_HWC_ROOT for tests
- `references/xpra-integration.md` — Xpra escape hatch: architecture, lazy-start pattern, graceful degradation, display:10 decision, SSH tunnel note
- `references/phase-engine-container-env.md` — Phase engine cron job: container paths, HERMES_HWC_ROOT for tests, Go toolchain, build commands, phase completion checklist
- `references/testing-patterns.md` — Go backend testing patterns
- `references/playwright-tests.md` — E2E test config, categories, run commands
- `references/theming-patterns.md` — 7-theme CSS variable system, Svelte 5 theme store (`$state` + `$effect`), `[data-theme]` attribute switching, SettingsPanel architecture per section, theme picker visual cards, connection status display, adding a new theme, key files, gotchas
- `references/playwright-selectors.md` — Selector cheat sheet, common pitfalls, bulk fix patterns