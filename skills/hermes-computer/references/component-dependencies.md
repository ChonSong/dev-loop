# Component Dependencies Map (2026-05-11 audit)

## Dependency Chain

```
hermes-web-computer/
├── Backend (Go)
│   ├── ws/multiplexer.go ← central hub, imports all below
│   │   ├── pty/supervisor.go ← PTY lifecycle, ring buffer, checkpoint
│   │   ├── layout/tree.go ← binary tree layout ops (split/mount/unmount/resize/swap/fullscreen)
│   │   ├── security/security.go ← tiered YAML permissions, token gating
│   │   ├── telemetry/telemetry.go ← JSONL ring buffer, async sync
│   │   ├── audio/bridge.go ← Fun-Audio-Chat WS relay (Opus/Text/Interrupt) ✅ complete
│   │   ├── ws/filesystem.go ← FS handlers (list/read/write/stat)
│   │   └── ws/apps.go ← App launch (terminal/editor/preview)
│   └── cmd/server/main.go ← entry point, wires everything
│
├── Frontend (Svelte 5)
│   ├── stores/ws.ts ← WebSocket store, event handlers, FS/app helpers
│   ├── App.svelte ← 3-column grid shell (LeftPanel | MiddlePanel | RightPanel)
│   ├── components/
│   │   ├── Tile.svelte ← recursive layout renderer (xterm/monaco/welcome/empty)
│   │   ├── Terminal.svelte ← xterm.js + FitAddon, reads from ptyOutputs store
│   │   ├── Monaco.svelte ← monaco-editor, fs.read response listener, NO write-back
│   │   ├── LeftPanel.svelte ← tabbed Files/Apps, fsRead + appsLaunch
│   │   ├── MiddlePanel.svelte ← <Tile node={$layout.tree} />
│   │   ├── RightPanel.svelte ← chat UI, chatSend(), NO agent backend
│   │   ├── FileTree.svelte ← WS-driven directory listing
│   │   ├── AppLauncher.svelte ← launch cards (terminal/editor/preview)
│   │   ├── ResizeHandle.svelte ← drag-to-resize columns
│   │   ├── CommandPalette.svelte ← Ctrl+K
│   │   └── KeymapOverlay.svelte ← Ctrl+?
│   └── main.ts ← calls ws.connect()
│
└── E2E (Playwright)
    ├── 01-layout.spec.ts → 02-resize.spec.ts (functional)
    ├── workflows/ (file-edit, cross-panel, chat-context, recovery, pipeline)
    ├── chaos/ (concurrent-tabs, network, ws-flood, server-death)
    ├── a11y/ (contrast, screen-reader, keyboard)
    ├── visual/ (baseline, regression)
    └── perf/ (load-time)
```

## Critical Dependencies for New Tiles

### Browser Tile
- **Needs**: chromedp or playwright-go in Go backend
- **Backend handler**: `browser.navigate`, `browser.screenshot`, `browser.click`, `browser.type` in multiplexer.go
- **Frontend**: New BrowserTile.svelte component with iframe for page rendering + control bar
- **Security**: Add browser domain to security config (URL allowlisting)

### Voice Tile
- **Backend**: Already complete (audio/bridge.go handles Opus/Text/Interrupt)
- **Frontend**: VoiceTile.svelte needed with:
  - `navigator.mediaDevices.getUserMedia({ audio: true })`
  - MediaRecorder → chunk encoding → WS `audio.stream`
  - `<audio>` element for playback of Opus responses
  - Record/stop/playing state UI
- **Protocol**: `audio.stream` (opus chunk), `audio.interrupt`, `audio.text` (TTS input)

### Dashboard Tile
- **Source**: agent-os React pages (22 pages, 11 themes)
- **Migration**: repo-transmute v2 → extract AST + screenshots → LLM → Svelte 5 → vision verify
- **Key pages**: Agent Status, Session History, System Metrics, MCP Servers
- **Backend**: Replace Express API routes with Go handlers in multiplexer.go
- **Data**: Replace PostgreSQL queries with in-memory or HTTP calls to Hermes

### Agent Chat (completion)
- **Backend**: Add HTTP client to routeAgent's `chat.send` → `http://host.docker.internal:8642/api/chat`
- **Streaming**: Server-Sent Events or WebSocket relay from Hermes to frontend
- **Frontend**: Already has message list + input, just needs real responses

## WS Protocol Extensions Needed

| Tile | Methods (client→server) | Events (server→client) |
|------|------------------------|----------------------|
| Browser | `browser.navigate`, `browser.screenshot`, `browser.click`, `browser.type` | `browser.loaded`, `browser.screenshot.response`, `browser.error` |
| Voice | `audio.stream`, `audio.interrupt`, `audio.text` | `audio.response`, `audio.status` |
| Dashboard | `dashboard.metrics`, `dashboard.sessions` | `dashboard.metrics.update`, `dashboard.sessions.update` |
| Agent Chat | `chat.send` (already exists) | `chat.reply` (already exists, just needs real impl) |
