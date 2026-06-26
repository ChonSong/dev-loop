# Agent-OS New Features (May 2026)

## Terminal (`/terminal`)
- Full PTY terminal via Docker exec + xterm.js (no node-pty needed)
- Backend: Socket.IO event handlers (`terminal:create`, `terminal:stdin`, `terminal:resize`, `terminal:close`)
- `TerminalDemux` class demultiplexes Docker exec 8-byte header stream
- Default container: `agent-os-backend`

## Memory (`/memory`)
- Browse, view, edit agent memory files via file API
- Searches `/opt/data/memory`, `/opt/data`, `/home/sean/.hermes`
- Uses `api.browseDirectory`, `api.readFileContent`, `api.writeFile`

## MCP (`/mcp`)
- Manage MCP (Model Context Protocol) servers
- Backend endpoints: `GET/POST/PATCH/DELETE /api/mcp/servers`, `POST /api/mcp/servers/:name/test`, `POST /api/mcp/servers/:name/tools`
- Store: `mcpServers` array with `MCPServerRecord` type
- Default servers: filesystem (stdio), github (stdio)
- Tool discovery by server name (known patterns: filesystem, github, postgres, slack, fetch)

## Dashboard (`/dashboard`)
- Aggregated metrics: KPI cards (sessions, messages, tokens, uptime, containers, events)
- Live container stats via Socket.IO `docker:containers` event
- Event breakdown (7-day window), recent sessions table
- Root redirect changed from `/containers` → `/dashboard`

## Chat Improvements (`/chat`)
- Replaced broken xterm/PTY with SSE-based full-page chat
- `ToolCallRenderer` component: parses and renders tool calls with expandable details
- ChatPanel integrates ToolCallRenderer for tool call display

## Sidebar Navigation (updated)
New items: Dashboard (Home), Memory (Brain), Terminal, MCP (Plug)

## Docker exec PTY Terminal Pattern

When adding a terminal to a Docker-based app, use Docker exec instead of node-pty:

```typescript
// Backend (Express + Socket.IO)
const exec = await container.exec({
  AttachStdin: true, AttachStdout: true, AttachStderr: true,
  Tty: true, Cmd: ['/bin/bash'],
  Env: [`COLUMNS=${cols}`, `LINES=${rows}`, 'TERM=xterm-256color'],
});
const stream = await exec.start({ hijack: true, stdin: true, stream: true });
// Demultiplex Docker's 8-byte header format: [stream_type(1)][padding(3)][size(4)]
```

Advantages: No native binary compilation, works in unified Docker image, leverages existing Docker socket access.

## Dark Theme Overrides

Hardcoded light colors in existing components are overridden via `[data-theme='xxx']` selectors appended to `index.css`. For new components, use `.theme-bg`, `.theme-text`, `.theme-border` etc. instead of hardcoded hex values.

## Backend API Endpoints Added

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/mcp/servers` | List MCP servers |
| POST | `/api/mcp/servers` | Create MCP server |
| PATCH | `/api/mcp/servers/:name` | Update MCP server |
| DELETE | `/api/mcp/servers/:name` | Delete MCP server |
| POST | `/api/mcp/servers/:name/test` | Test connection |
| POST | `/api/mcp/servers/:name/tools` | Discover tools |
| Socket.IO | `terminal:create` | Create PTY session |
| Socket.IO | `terminal:stdin` | Send input |
| Socket.IO | `terminal:resize` | Resize terminal |
| Socket.IO | `terminal:close` | Close session |
