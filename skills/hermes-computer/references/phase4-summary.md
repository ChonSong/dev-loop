# Phase 4 Summary — CommandPalette, LLM Router, MCP Client (2026-05-14)

## What was built

### `backend/llm/router.go` — 638 lines
Multi-provider LLM router:
- Providers: OpenAI, Anthropic, Groq, Ollama, LM Studio
- `Chat()` — synchronous chat
- `StreamChat()` — SSE streaming with provider-specific parsing
- `RegisterModel()`, `GetModel()`, `ListModels()` — model registry
- Provider-specific request/response handling (Anthropic uses `messages` array, OpenAI uses `model`)
- Base URL + API key per provider, configurable

### `backend/mcp/client.go` — 725 lines
Full MCP (Model Context Protocol) client connecting to MCP servers via stdio:
- JSON-RPC 2.0 protocol over stdio (`exec.Cmd`)
- `Manager` struct: connect/disconnect multiple servers
- `Client` struct: per-server MCP operations
- `Initialize()` — protocol version negotiation
- `ListTools()`, `CallTool()` — tool operations
- `ListResources()`, `ReadResource()` — resource operations
- `ListPrompts()`, `GetPrompt()` — prompt operations
- `SubscribeToNotifications()` — server→client push
- `SetRequestHandler()` — handle server requests

### MCP WS handlers in `backend/ws/multiplexer.go` (+253 lines)
7 new `routeUI` cases:
- `mcp.list` — list connected servers
- `mcp.connect` — connect to MCP server (name + command)
- `mcp.disconnect` — disconnect server
- `mcp.tools.list` — list tools on a server
- `mcp.tools.call` — call a tool with args
- `mcp.resources.list` / `mcp.resources.read`
- `mcp.prompts.list` / `mcp.prompts.get`

4 agent protocol handlers:
- `agent.mcp.list` / `agent.mcp.connect` / `agent.mcp.disconnect`
- `agent.mcp.tools.list` / `agent.mcp.tools.call`
- `agent.mcp.resources.list` / `agent.mcp.resources.read`
- `agent.mcp.prompts.list` / `agent.mcp.prompts.get`

### `frontend/src/components/CommandPalette.svelte` — 237 lines
Full fuzzy-search command palette:
- 8 categories: Layout, Terminal, Navigation, Session, Files, LLM, Skills, Settings
- Fuzzy match scoring: exact (100) > starts-with (80) > word-boundary (60) > contains (40) > char-by-char
- Category tabs for filtering
- Keyboard navigation: ↑↓ select, ↵ execute, esc close
- Dynamic commands from sessions + skills (live from stores)
- Footer hints
- `Ctrl+K` opens palette

### `frontend/src/stores/ws.ts` — MCP helpers (+37 lines)
- `mcpList()` → `agent.mcp.list`
- `mcpConnect(name, command, args?)` → `agent.mcp.connect`
- `mcpDisconnect(name)` → `agent.mcp.disconnect`
- `mcpToolsList(serverName)` → `agent.mcp.tools.list`
- `mcpToolsCall(serverName, toolName, toolArgs?)` → `agent.mcp.tools.call`
- Same pattern for resources and prompts

## Integration points

- MCP client uses global `mcp.GetManager()` singleton from `backend/mcp/client.go`
- The `routeUI` cases in multiplexer.go call `mcpMgr.ListTools()`, `mcpMgr.CallTool()`, etc.
- Frontend `ws.ts` uses `send()` (not `wsCall()`) for agent protocol — agents use `protocol: "agent"`, UI uses `protocol: "ui"`
- CommandPalette reads from `sessionStore`, `profileStore`, `skillsStore` for dynamic commands

## Verification
```bash
cd /opt/data/hermes-web-computer/backend && go build -o /tmp/hwc-server ./cmd/server/  # must pass
cd /opt/data/hermes-web-computer/frontend && npm run build  # must pass
```