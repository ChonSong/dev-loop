# agent-os Frontend Pages (2026-05-09)

## All 22 Pages

| Route | Component | Status | Description |
|-------|-----------|--------|-------------|
| `/` | RootRedirect | ✅ | Redirects to `/dashboard` |
| `/dashboard` | DashboardPage | ✅ NEW | KPI cards, live container stats, events, sessions table |
| `/containers` | ContainerPage | ✅ | Bento grid, real-time Socket.IO stats, Docker control |
| `/sessions` | SessionsPage | ✅ | PG-backed history, search, copy messages |
| `/cron` | CronPage | ✅ | Create/manage scheduled agent jobs |
| `/profiles` | ProfilesPage | ✅ | Profile CRUD, soul.md editor |
| `/memory` | MemoryPage | ✅ NEW | Browse, view, edit agent memory files |
| `/mcp` | MCPPage | ✅ NEW | Server management: add, test, scan tools, toggle |
| `/terminal` | TerminalPage | ✅ NEW | xterm.js + Socket.IO Docker exec PTY |
| `/analytics` | AnalyticsPage | ✅ | Token/session/model analytics from PG |
| `/files` | FileExplorerPage | ✅ | Full CRUD file browser |
| `/tools` | ToolManagerPage | ✅ | Toolset management |
| `/settings` | SettingsPage | ✅ | Interactive settings + ThemePicker |
| `/config` | ConfigPage | ✅ | Raw config editor |
| `/chat` | ChatPage | ✅ NEW | Full-page SSE chat (replaced broken xterm/PTY) |
| `/env` | EnvPage | ✅ | Environment variable management |
| `/logs` | LogsPage | ✅ | Real-time log streaming via Socket.IO |
| `/models` | ModelsPage | ✅ | Model info, options, assignment |
| `/docs` | DocsPage | ✅ | Documentation |
| `/observability` | ObservabilityPage | ⚠️ | Events display — no data (observability not wired) |
| `/appstore` | AppStorePage | ⚠️ | Plugin store UI — rudimentary backend |

## New Components

| Component | Description |
|-----------|-------------|
| `ThemeContext.tsx` | Theme provider, 11 themes, localStorage persistence |
| `ToolCallRenderer.tsx` | Parse and render tool calls with expandable details |
| `ThemePicker` | In SettingsPage — button grid for 11 themes |

## Backend API Endpoints Added

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/mcp/servers` | List MCP servers |
| POST | `/api/mcp/servers` | Create MCP server |
| PATCH | `/api/mcp/servers/:name` | Update MCP server |
| DELETE | `/api/mcp/servers/:name` | Delete MCP server |
| POST | `/api/mcp/servers/:name/test` | Test connection |
| POST | `/api/mcp/servers/:name/tools` | Discover tools |
| Socket.IO | `terminal:create` | Create Docker exec PTY session |
| Socket.IO | `terminal:stdin/data/resize/close` | Terminal I/O |
