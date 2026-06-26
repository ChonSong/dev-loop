# React Patterns from agent-os Session (May 2026)

## Docker exec PTY Terminal Pattern

Adding a terminal to a React app backed by Docker (no node-pty needed):

**Backend** (Express + Socket.IO):
```typescript
const exec = await container.exec({
  AttachStdin: true, AttachStdout: true, AttachStderr: true,
  Tty: true, Cmd: ['/bin/bash'],
  Env: [`COLUMNS=${cols}`, `LINES=${rows}`, 'TERM=xterm-256color'],
});
const stream = await exec.start({ hijack: true, stdin: true, stream: true });
// Demultiplex: Docker exec uses 8-byte headers [stream_type(1)][padding(3)][size(4)]
```

**Frontend** (xterm.js + Socket.IO):
```typescript
const socket = io();
socket.emit('terminal:create', { container: 'agent-os-backend', cols: 80, rows: 24 });
socket.on('terminal:data', ({ data }) => term.write(data));
term.onData((data) => socket.emit('terminal:stdin', { sessionId, data }));
```

## SSE Chat Pattern

Replace broken xterm/PTY chat with SSE streaming:

```typescript
const res = await fetch('/api/agent/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ text, session_id, stream: true }),
});
const reader = res.body.getReader();
while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  // Parse SSE chunks: data: {"choices":[{"delta":{"content":"x"}}]}
}
```

## Theme System Pattern

CSS variables + `data-theme` attribute for multi-theme support:

```css
[data-theme='matrix'] {
  --theme-bg: #020804;
  --theme-text: #d8ffe3;
  --theme-accent: #00ff41;
  /* ... */
}
[data-theme] .theme-bg { background-color: var(--theme-bg) !important; }
```

Components should use `.theme-bg`, `.theme-text`, `.theme-border` etc. instead of hardcoded hex values.

## Tool Call Rendering Pattern

Parse tool calls from message content and render with expandable details:

```typescript
function parseToolCalls(content: string) {
  const simpleToolPattern = /\{[^{}]*"name"\s*:\s*"([^"]+)"[^{}]*"input"\s*:\s*(\{[^{}]*\})[^{}]*\}/g;
  // Extract name + input JSON, remove from text to avoid double-rendering
}
```

## MCP Server Management Pattern

REST CRUD + test endpoint for MCP server connections:
- `GET/POST/PATCH/DELETE /api/mcp/servers`
- `POST /api/mcp/servers/:name/test` — tests stdio (spawn + --help) or HTTP (fetch /health)
- `POST /api/mcp/servers/:name/tools` — discovers tools by server name pattern

## Hardcoded Color Audit

agent-os has 305 instances of hardcoded `bg-[#FFF5E6]`, `text-[#111827]`, `border-[#F0E6D8]` etc.
New components should use theme utility classes. Existing components need gradual migration.
