# Cron Delivery Fixes — June 2026

## context-budget-audit: `deliver: origin` → `deliver: local`

**Symptom:** Job ran successfully (`last_status: ok`) but had delivery error:

```
last_delivery_error: "no delivery target resolved for deliver=origin"
```

**Root cause:** The job was created from a WebUI chat session that was later closed or expired. At run time, `deliver: origin` tried to resolve the creating session as the delivery target but found it didn't exist.

**Fix:** Changed from `deliver: origin` to `deliver: local`. The output still appears in the cron log.

```yaml
# BEFORE
deliver: origin

# AFTER
deliver: local
```

**Lesson:** `deliver: origin` is not reliable for cron jobs unless the creating session is guaranteed to persist (CLI gateway session). For WebUI-created jobs, use `deliver: local`.

## Pattern: Detecting This Failure

When auditing cron jobs, look for:
```json
"last_status": "ok",
"last_delivery_error": "no delivery target resolved for deliver=origin"
```

This combination means the job succeeds but its output is lost. The fix is always `deliver: local`.

## MCP Server Setup (related: context7, github, time, postgres)

Adding MCP servers via CLI:
```bash
# Stdio MCP (npx-based)
hermes mcp add <name> --command npx --args -y <package-name> [connection-string-or-args]

# Stdio MCP (uvx-based)
hermes mcp add <name> --command uvx --args <package-name>

# Stdio MCP with env vars
hermes mcp add <name> --command npx --args -y <package> --env KEY=VALUE

# Pipe "y" to auto-confirm all tools
echo "y" | hermes mcp add <name> --command npx --args -y <package>
```

Useful MCP servers added June 2026:
| Server | Package | Tools |
|---|---|---|
| context7 | `@upstash/context7-mcp` | `resolve-library-id`, `query-docs` |
| github | `@modelcontextprotocol/server-github` | 26 tools (PRs, issues, repos, etc.) — needs `GITHUB_PERSONAL_ACCESS_TOKEN` env |
| time | `mcp-server-time` (uvx) | `get_current_time`, `convert_time` |
| postgres | `@modelcontextprotocol/server-postgres` | `query` (read-only SQL) — needs connection string |

Enabling bundled plugins:
```bash
hermes plugins enable disk-cleanup
```
