# Three-Column Layout Design — hermes-web-computer v1.2

## Origin

User requested (2026-05-11): "three column layout. left file manager/application launcher(switch between), middle applications (tiling), right agent interaction(text or voice)."

## Existing Codebase Audit

**Backend** (`/opt/data/hermes-web-computer/backend/`):
- `ws/multiplexer.go` — WS router with 4 protocol routes: `ui`, `agent`, `audio`, and health/static
- `pty/supervisor.go` — PTY sessions with ring buffer, output channels
- `layout/tree.go` — Binary tree split/mount/unmount (designed for free-form tiling, NOT fixed grid)
- `security/security.go` — Tiered YAML permissions
- `telemetry/telemetry.go` — Telemetry
- `audio/bridge.go` — Fun-Audio-Chat WebSocket relay
- **NO file system API** — no `/api/fs`, no FS WebSocket methods
- **NO application registry** — no app discovery mechanism

**Frontend** (`/opt/data/hermes-web-computer/frontend/src/`):
- `App.svelte` — Full-screen flex container rendering `<Tile node={$layout.tree} />`
- `Tile.svelte` — Recursive layout renderer with split/focus (binary tree)
- `Terminal.svelte` — xterm.js wrapper with PTY stream sync
- `Monaco.svelte` — Code editor component
- `CommandPalette.svelte` — Command palette
- `KeymapOverlay.svelte` — Keyboard shortcuts overlay
- `stores/ws.ts` — Svelte store managing WS connection, layout mutations, PTY output buffers
- **No file manager, no sidebar, no agent chat UI, no fixed column layout**

## Design Decisions (Recommended, Not Yet Confirmed)

### Q1: Layout Model
**Decision:** Ditch binary tree for the root layout. Use CSS grid for 3 fixed columns. Middle column can still use binary tree for internal tiling.
**Rationale:** Binary tree is designed for free-form splits. Three-column is fundamentally a fixed grid. CSS `grid-template-columns: 280px 1fr 360px` is simpler and more performant.

### Q2: File System API
**Decision:** Route FS operations through existing WebSocket multiplexer as `{protocol: "ui", method: "fs.list", params: {path: "/host/project"}}`.
**Rationale:** Keeps "one wire" principle (single WS connection). Backend uses Go's `os.ReadDir`. No new HTTP endpoints needed.

### Q3: File Manager / App Launcher Toggle
**Decision:** Tabbed sidebar — two tabs: "Files" and "Apps". Files is primary view (80%), Apps is secondary.
**Rationale:** Cleanest UX, single-click toggle, no state complexity.

### Q4: Application Launcher Contents
**Decision:** Auto-discover from backend at startup: PTY sessions (terminals), Monaco editors (open files), registered app instances. Quick-launch: "New Terminal", "New Editor", "Run Command".
**Rationale:** No manual registry needed. Backend already tracks these.

### Q5: Agent Panel
**Decision:** Both text and voice with toggle. Default text (lower latency). Voice activates Fun-Audio-Chat stream. Shows chat history with Hermes (text) and Fun-Audio-Chat (voice transcript + audio playback).
**Rationale:** Leverages existing `audio` protocol route and Hermes `agent` route.

### Q6: Middle Column Tiling
**Decision:** Middle column starts with single tile. Split via `Shift+D` (horizontal), `Shift+V` (vertical), or drag borders. Max 4 tiles (2×2 grid).
**Rationale:** Usable limit beyond 2×2. Existing Tile component can be constrained to middle column.

### Q7: Column Widths
**Decision:** Resizable with drag handles. Default: 280px left, 1fr middle, 360px right. Min: 200px / 400px / 280px. Store in localStorage.
**Rationale:** Flexible defaults with user control. Persistence via localStorage avoids backend state.

## Recommended Execution Order

1. CSS grid layout — Replace App.svelte with 3-column grid
2. Backend file API — Add FS commands to WebSocket multiplexer
3. Left column — Tabbed sidebar with file tree + app launcher
4. Middle column — Existing Tile component, constrained to middle column
5. Right column — Agent chat UI with text input + voice toggle
6. Resize handles — Drag-to-resize column widths

## Status

**Pending user confirmation.** Design decisions presented but not yet locked. User was in "relentless questioning" loop when session ended (max tool iterations reached).
