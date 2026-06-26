---
name: native-mcp
description: "MCP client: connect servers, register tools (stdio/HTTP)."
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [MCP, Tools, Integrations]
    related_skills: [mcporter]
---

# Native MCP Client

Hermes Agent has a built-in MCP client that connects to MCP servers at startup, discovers their tools, and makes them available as first-class tools the agent can call directly. No bridge CLI needed -- tools from MCP servers appear alongside built-in tools like `terminal`, `read_file`, etc.

## When to Use

Use this whenever you want to:
- Connect to MCP servers and use their tools from within Hermes Agent
- Add external capabilities (filesystem access, GitHub, databases, APIs) via MCP
- Run local stdio-based MCP servers (npx, uvx, or any command)
- Connect to remote HTTP/StreamableHTTP MCP servers
- Have MCP tools auto-discovered and available in every conversation

For ad-hoc, one-off MCP tool calls from the terminal without configuring anything, see the `mcporter` skill instead.

## Prerequisites

- **mcp Python package** -- optional dependency; install with `pip install mcp`. If not installed, MCP support is silently disabled.
- **Node.js** -- required for `npx`-based MCP servers (most community servers)
- **uv** -- required for `uvx`-based MCP servers (Python-based servers)

Install the MCP SDK:

```bash
pip install mcp
# or, if using uv:
uv pip install mcp
```

## Quick Start

Add MCP servers to `~/.hermes/config.yaml` under the `mcp_servers` key:

```yaml
mcp_servers:
  time:
    command: "uvx"
    args: ["mcp-server-time"]
```

The MCP server subprocess inherits a **filtered environment** (see Security section). `$HOME` inside the subprocess may differ from what you expect in the shell — always use fully-resolved absolute paths for the `command` binary.

Restart Hermes Agent, or trigger discovery from within the running agent. On connect it will:
1. Connect to the server
2. Discover available tools
3. Register them with the prefix `mcp_{server_name}_*`
4. Inject them into all platform toolsets

You can then use the tools naturally -- just ask the agent to use them.

## Configuration Reference

Each entry under `mcp_servers` is a server name mapped to its config. There are two transport types: **stdio** (command-based) and **HTTP** (url-based).

### Stdio Transport (command + args)

```yaml
mcp_servers:
  server_name:
    command: "npx"             # (required) executable to run
    args: ["-y", "pkg-name"]   # (optional) command arguments, default: []
    env:                       # (optional) environment variables for the subprocess
      SOME_API_KEY: "value"
    timeout: 120               # (optional) per-tool-call timeout in seconds, default: 120
    connect_timeout: 60        # (optional) initial connection timeout in seconds, default: 60
```

### HTTP Transport (url)

```yaml
mcp_servers:
  server_name:
    url: "https://my-server.example.com/mcp"   # (required) server URL
    headers:                                     # (optional) HTTP headers
      Authorization: "Bearer sk-..."
    timeout: 180               # (optional) per-tool-call timeout in seconds, default: 120
    connect_timeout: 60        # (optional) initial connection timeout in seconds, default: 60
```

### All Config Options

| Option            | Type   | Default | Description                                       |
|-------------------|--------|---------|---------------------------------------------------|
| `command`         | string | --      | Executable to run (stdio transport, required)     |
| `args`            | list   | `[]`    | Arguments passed to the command                   |
| `env`             | dict   | `{}`    | Extra environment variables for the subprocess    |
| `url`             | string | --      | Server URL (HTTP transport, required)             |
| `headers`         | dict   | `{}`    | HTTP headers sent with every request              |
| `timeout`         | int    | `120`   | Per-tool-call timeout in seconds                  |
| `connect_timeout` | int    | `60`    | Timeout for initial connection and discovery      |

Note: A server config must have either `command` (stdio) or `url` (HTTP), not both.

## How It Works

### Startup Discovery

When Hermes Agent starts, `discover_mcp_tools()` is called during tool initialization:

1. Reads `mcp_servers` from `~/.hermes/config.yaml`
2. For each server, spawns a connection in a dedicated background event loop
3. Initializes the MCP session and calls `list_tools()` to discover available tools
4. Registers each tool in the Hermes tool registry

### On-Demand Discovery (Hot-Reload)

The CLI (`hermes gateway run`) polls config.yaml changes. If `mcp_servers` content changed, it calls `discover_mcp_tools()` to connect new servers without a full restart. You can also trigger discovery manually from within the running agent:

```python
from tools.mcp_tool import discover_mcp_tools
tools = discover_mcp_tools()
print(f"Registered {len(tools)} MCP tools")
```

### Tool Naming Convention

MCP tools are registered with the naming pattern:

```
mcp_{server_name}_{tool_name}
```

Hyphens and dots in names are replaced with underscores for LLM API compatibility.

Examples:
- Server `filesystem`, tool `read_file` → `mcp_filesystem_read_file`
- Server `github`, tool `list-issues` → `mcp_github_list_issues`
- Server `my-api`, tool `fetch.data` → `mcp_my_api_fetch_data`

### Auto-Injection

After discovery, MCP tools are automatically injected into all `hermes-*` platform toolsets (CLI, Discord, Telegram, etc.). This means MCP tools are available in every conversation without any additional configuration.

### Connection Lifecycle

- Each server runs as a long-lived asyncio Task in a background daemon thread
- Connections persist for the lifetime of the agent process
- If a connection drops, automatic reconnection with exponential backoff kicks in (up to 5 retries, max 60s backoff)
- On agent shutdown, all connections are gracefully closed

### Idempotency

`discover_mcp_tools()` is idempotent -- calling it multiple times only connects to servers that aren't already connected. Failed servers are retried on subsequent calls.

## Transport Types

### Stdio Transport

The most common transport. Hermes launches the MCP server as a subprocess and communicates over stdin/stdout.

```yaml
mcp_servers:
  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/projects"]
```

The subprocess inherits a **filtered** environment (see Security section below) plus any variables you specify in `env`.

### HTTP / StreamableHTTP Transport

For remote or shared MCP servers. Requires the `mcp` package to include HTTP client support (`mcp.client.streamable_http`).

```yaml
mcp_servers:
  remote_api:
    url: "https://mcp.example.com/mcp"
    headers:
      Authorization: "Bearer sk-..."
```

If HTTP support is not available in your installed `mcp` version, the server will fail with an ImportError and other servers will continue normally.

## Security

### Environment Variable Filtering

For stdio servers, Hermes does NOT pass your full shell environment to MCP subprocesses. Only safe baseline variables are inherited:

- `PATH`, `HOME`, `USER`, `LANG`, `LC_ALL`, `TERM`, `SHELL`, `TMPDIR`
- Any `XDG_*` variables

All other environment variables (API keys, tokens, secrets) are excluded unless you explicitly add them via the `env` config key. This prevents accidental credential leakage to untrusted MCP servers.

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      # Only this token is passed to the subprocess
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_..."
```

### Credential Stripping in Error Messages

If an MCP tool call fails, any credential-like patterns in the error message are automatically redacted before being shown to the LLM. This covers:

- GitHub PATs (`ghp_...`)
- OpenAI-style keys (`sk-...`)
- Bearer tokens
- Generic `token=`, `key=`, `API_KEY=`, `password=`, `secret=` patterns

## Pitfalls

### Binary not found despite being on PATH

Stdio MCP servers run in a filtered environment. `HOME` may point somewhere unexpected inside the container (e.g. `/home/hermeswebui/.hermes/home` instead of `/home/hermeswebui`). **Always use a fully-resolved absolute path** for the `command` — verify with `readlink -f` or `realpath`:

```bash
# Wrong — resolves against $HOME which the subprocess may not share
command: ~/.local/bin/my-mcp-server

# Right — verified absolute path
command: /home/hermeswebui/.local/bin/my-mcp-server
```

### Edited the wrong config.yaml

`get_hermes_home()` returns the directory that `load_config()` reads from. This may differ from what `~/.hermes` resolves to inside the container. To find the authoritative path:

```python
from hermes_cli.config import get_config_path
print(get_config_path())  # the actual file
```

Verify the edit took effect:

```python
config = load_config()
print(list(config.get("mcp_servers", {}).keys()))
```

If empty, you're editing the wrong file.

### MCP tools registered in one-shot Python process but gone in the agent

MCP server connections live in the asyncio event loop of the process that called `discover_mcp_tools()`. They do NOT survive across process boundaries. Running `python3 -c "..."` registers tools in that script's process only — when it exits, connections die. Always trigger discovery from within the running agent's process, or restart the agent.

### Some Hermes platforms don't call discover_mcp_tools() at startup

The CLI gateway auto-discovers MCP tools on startup and hot-reloads on config changes. The Hermes WebUI (`server.py`) **does not** — if you're in a WebUI session, you need to trigger discovery manually from within the running agent or ensure the gateway is running alongside it.

## Pitfalls

### Binary Path Must Be Resolvable in Filtered Environment

When configuring a stdio MCP server, the `command` binary path is resolved in the MCP subprocess's **filtered environment** (see Security section above). The subprocess only inherits `PATH`, `HOME`, `USER`, `LANG`, `LC_ALL`, `TERM`, `SHELL`, `TMPDIR`, and `XDG_*` variables plus any `env` overrides.

This means:
- **Use absolute paths** to the binary, not relative paths or bare command names (unless they're on the inherited `PATH`)
- `~` expansion does NOT happen in the subprocess — `/home/user/.local/bin/tool` works, `~/.local/bin/tool` does not
- The `$HOME` inside the subprocess may differ from the calling agent's `$HOME` — verify with `echo $HOME` before hardcoding paths
- If the binary is only installed in a custom location (e.g., `~/.local/bin/`), copy it to a location that exists in the filtered environment or specify the absolute path

```yaml
# GOOD: absolute path
mcp_servers:
  truenas:
    command: /home/user/.local/bin/truenas-mcp

# BAD: relative path or ~ alias
  truenas:
    command: "~/.local/bin/truenas-mcp"   # fails — no ~ expansion
```

### "Command not found" Despite Binary Being Installed

If the MCP server fails with "command not found" but the binary exists at the path you specified, check:
1. Is the path absolute? (relative paths resolve against the filtered `PATH`)
2. Is the binary at that exact path from the subprocess's perspective? (`/proc/<pid>/root` may differ)
3. Does the binary have execute permissions? (`chmod +x`)

## Troubleshooting

### "MCP SDK not available -- skipping MCP tool discovery"

The `mcp` Python package is not installed. Install it:

```bash
pip install mcp
```

### "No MCP servers configured"

No `mcp_servers` key in `~/.hermes/config.yaml`, or it's empty. Add at least one server.

**Pitfall — WebUI dual config files:** In Hermes WebUI deployments, `$HOME` may differ from `get_hermes_home()`. The config file that `load_config()` reads is `get_hermes_home() / "config.yaml"`, which may be a different file than `~/.hermes/config.yaml`. Always verify with:

```python
from hermes_cli.config import load_config
print(list(load_config().get('mcp_servers', {}).keys()))
```

If it shows an empty list despite adding `mcp_servers` to the file you edited, you are editing the wrong file. Check `get_hermes_home()` and write to that path instead.

### "Failed to connect to MCP server 'X'"

Common causes:
- **Command not found**: The `command` binary isn't on PATH **in the subprocess's filtered environment**. Use a fully-resolved absolute path (see Pitfalls).
- **Package not found**: For npx servers, the npm package may not exist or may need `-y` in args to auto-install.
- **Timeout**: The server took too long to start. Increase `connect_timeout`.
- **Port conflict**: For HTTP servers, the URL may be unreachable.

### "MCP server 'X' requires HTTP transport but mcp.client.streamable_http is not available"

Your `mcp` package version doesn't include HTTP client support. Upgrade:

```bash
pip install --upgrade mcp
```

### Tools not appearing

- Check that the server is listed under `mcp_servers` (not `mcp` or `servers`)
- Ensure the YAML indentation is correct
- Run `discover_mcp_tools()` from within the running agent to check for connection errors (log messages with the retry chain appear)
- Tool names are prefixed with `mcp_{server}_{tool}` -- look for that pattern

### Connection keeps dropping

The client retries up to 5 times with exponential backoff (1s, 2s, 4s, 8s, 16s, capped at 60s). If the server is fundamentally unreachable, it gives up after 5 attempts. Check the server process and network connectivity.

## Examples

### Time Server (uvx)

```yaml
mcp_servers:
  time:
    command: "uvx"
    args: ["mcp-server-time"]
```

Registers tools like `mcp_time_get_current_time`.

### Filesystem Server (npx)

```yaml
mcp_servers:
  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/documents"]
    timeout: 30
```

Registers tools like `mcp_filesystem_read_file`, `mcp_filesystem_write_file`, `mcp_filesystem_list_directory`.

### GitHub Server with Authentication

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_xxxxxxxxxxxxxxxxxxxx"
    timeout: 60
```

Registers tools like `mcp_github_list_issues`, `mcp_github_create_pull_request`, etc.

### TrueNAS Management Server

```yaml
mcp_servers:
  truenas:
    command: /home/hermeswebui/.local/bin/truenas-mcp
    args: ["--truenas-url", "192.168.1.102", "--api-key", "your-api-key"]
    timeout: 120
    connect_timeout: 30
```

See `references/truenas-mcp-setup.md` for full setup details.

### Remote HTTP Server

```yaml
mcp_servers:
  company_api:
    url: "https://mcp.mycompany.com/v1/mcp"
    headers:
      Authorization: "Bearer sk-xxxxxxxxxxxxxxxxxxxx"
      X-Team-Id: "engineering"
    timeout: 180
    connect_timeout: 30
```

### Multiple Servers

```yaml
mcp_servers:
  time:
    command: "uvx"
    args: ["mcp-server-time"]

  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]

  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_xxxxxxxxxxxxxxxxxxxx"

  company_api:
    url: "https://mcp.internal.company.com/mcp"
    headers:
      Authorization: "Bearer sk-xxxxxxxxxxxxxxxxxxxx"
    timeout: 300
```

All tools from all servers are registered and available simultaneously. Each server's tools are prefixed with its name to avoid collisions.

## Sampling (Server-Initiated LLM Requests)

Hermes supports MCP's `sampling/createMessage` capability — MCP servers can request LLM completions through the agent during tool execution. This enables agent-in-the-loop workflows (data analysis, content generation, decision-making).

Sampling is **enabled by default**. Configure per server:

```yaml
mcp_servers:
  my_server:
    command: "npx"
    args: ["-y", "my-mcp-server"]
    sampling:
      enabled: true           # default: true
      model: "gemini-3-flash" # model override (optional)
      max_tokens_cap: 4096    # max tokens per request
      timeout: 30             # LLM call timeout (seconds)
      max_rpm: 10             # max requests per minute
      allowed_models: []      # model whitelist (empty = all)
      max_tool_rounds: 5      # tool loop limit (0 = disable)
      log_level: "info"       # audit verbosity
```

Servers can also include `tools` in sampling requests for multi-turn tool-augmented workflows. The `max_tool_rounds` config prevents infinite tool loops. Per-server audit metrics (requests, errors, tokens, tool use count) are tracked via `get_mcp_status()`.

Disable sampling for untrusted servers with `sampling: { enabled: false }`.

## Notes

- MCP tools are called synchronously from the agent's perspective but run asynchronously on a dedicated background event loop
- Tool results are returned as JSON with either `{"result": "..."}` or `{"error": "..."}`
- The native MCP client is independent of `mcporter` -- you can use both simultaneously
- Server connections are persistent and shared across all conversations in the same agent process
- The CLI gateway hot-reloads `mcp_servers` config changes automatically; the WebUI does not -- trigger `discover_mcp_tools()` manually in WebUI sessions
