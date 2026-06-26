# Adding MCP Servers — Worked Examples

## Context7 MCP (Upstash)

Adds version-specific library documentation to your agent's context. Two tools: `resolve-library-id` and `query-docs`.

### Setup

```bash
# Check MCP SDK is available in Hermes venv
/home/sc/.hermes/hermes-agent/venv/bin/python -c "import mcp; print('ok')"

# Add via CLI
echo y | hermes mcp add context7 --command npx --args -y @upstash/context7-mcp@latest
```

### Verification

```bash
hermes mcp list
# Should show: context7 | npx -y @upstash/context7-mcp@latest | all | enabled
```

### Usage

After a `/reset` (WebUI) or new session, the tools `mcp_context7_resolve_library_id` and `mcp_context7_query_docs` become available. Append "use context7" to prompts for best results:

> "Create a Next.js 15 app with App Router. use context7"

## GitHub MCP Server

Adds PR/issue/repo management tools.

```bash
echo y | hermes mcp add github --command npx --args -y @modelcontextprotocol/server-github
```

Requires `GITHUB_TOKEN` environment variable to be set in the subprocess. Since Hermes filters env vars, pass it explicitly:

```bash
echo y | hermes mcp add github --command npx --args -y @modelcontextprotocol/server-github --env GITHUB_TOKEN=ghp_xxxx
```

## Filesystem MCP Server

Adds filesystem read/write tools scoped to a directory.

```bash
echo y | hermes mcp add filesystem --command npx --args -y @modelcontextprotocol/server-filesystem /home/sc
```

## Common Pitfalls

### `--args` must be last

```bash
# ✓ Correct
hermes mcp add X --command npx --args -y @npm/package

# ✗ Wrong — --timeout after --args is interpreted as an argument to npx
hermes mcp add X --command npx --args -y @npm/package --timeout 120
```

### Interactive confirmation blocks automation

Always pipe `echo y |` when running from a script or agent context. Without it, the CLI waits for user input.

### Tools don't appear after adding

The CLI adds the config and connects on-the-fly during `hermes mcp add`, but **WebUI sessions** need a session restart (`/reset`) to discover the tools. CLI gateway sessions auto-detect on next session start.

### `patch`/`write_file` can't edit config.yaml

These tools are blocked from modifying Hermes config files. Always use `hermes mcp add` from the terminal tool instead.

### Binary not found for stdio servers

MCP subprocesses inherit a FILTERED environment — only `PATH`, `HOME`, `USER`, `LANG`, `LC_ALL`, `TERM`, `SHELL`, `TMPDIR`, and `XDG_*` vars pass through. Use absolute paths for custom binaries (e.g., `/home/user/.local/bin/truenas-mcp`), not relative or `~` aliases.
