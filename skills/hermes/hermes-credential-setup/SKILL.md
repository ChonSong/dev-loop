---
name: hermes-credential-setup
title: Hermes Credential & Env Var Management
description: >
  How to add, update, and manage API keys and environment variables in Hermes Agent —
  the protected .env file, Bitwarden secrets manager, shell_init_files fallback,
  and environment passthrough configuration.
---

# Hermes Credential & Env Var Management

## The Protected .env File

`~/.hermes/.env` is a **protected system file**. The agent **cannot** write to it via `patch`, `write_write`, or any tool. The security layer blocks all writes. This is by design — the file contains API keys and the system treats it as a root-of-trust boundary.

**User must add keys manually.** Provide the exact `KEY=value` line and tell the user to run:

```bash
echo 'KEY=value' >> ~/.hermes/.env
```

Or edit `~/.hermes/.env` directly.

Then restart the gateway so the new key is loaded:

```bash
hermes gateway restart
```

## Available Programmatic Paths (and their limits)

| Method | Works? | Notes |
|---|---|---|
| `patch`/`write_file` on `~/.hermes/.env` | ❌ Blocked | Protected file, write denied |
| `hermes env set KEY VALUE` | ❌ No such command | Doesn't exist |
| `hermes secrets ...` | ⚠️ Limited | Only supports Bitwarden Secrets Manager |
| `hermes config set ...` | ⚠️ No env section | config.yaml has no env key storage |
| `config.yaml `env_passthrough`` | ⚠️ Forward-only | Only passes vars that ALREADY exist in the Hermes process environment — doesn't set new ones |
| `config.yaml `shell_init_files`` | ✅ Works | Sources a shell script in terminal sessions — but only affects `terminal()` tool shells, NOT the Hermes process itself. `bb`, `browse`, etc. run from terminal() WILL see the var. |

## When to Use Each Path

### Path 1: User adds to `.env` (preferred for persistent services)
When a credential is needed by Hermes internals (gateway, cron jobs, MCP servers) or by CLI tools invoked through terminal():

1. Give the user the exact line to add
2. User runs `echo 'KEY=value' >> ~/.hermes/.env`
3. User restarts gateway: `hermes gateway restart`

### Path 2: shell_init_files (fallback for terminal-only tools)
When the credential is only needed by CLI tools run through `terminal()` (not by Hermes internals):

1. Write a source file: `/workspace/.env.d/<name>.sh` with `export KEY=value`
2. Add to `config.yaml` → `terminal.shell_init_files`
3. No gateway restart needed — takes effect on next shell_init load

This is a **workaround**, not a permanent fix. The `.env` file is still the canonical location.

### Path 3: workspace .env (workspace-scoped tools)
Write to `/workspace/.env` for tools that source from the workspace directory. This is NOT loaded by Hermes automatically — only useful for project-specific dotenv loading.

## Bitwarden Secrets Manager

If the user uses Bitwarden Secrets Manager, configure it in `config.yaml`:

```yaml
secrets:
  bitwarden:
    enabled: true
    access_token_env: BWS_ACCESS_TOKEN
    project_id: "<bitwarden-project-id>"
```

Then reference secrets in config as `$BITWARDEN_SECRET_NAME`. See `hermes secrets --help` for setup.

## Common Credentials Pattern

When the user provides a new API key mid-session:

1. **Acknowledge** that you'll note it needs to be added
2. **Tell the user** the exact command to run (never try to write it yourself)
3. **Use shell_init_files as a temporary bridge** so work can continue without restarting
4. **Remind about restart** when the session concludes

## Pitfalls

- `hermes env set` does NOT exist — don't invent it
- `env_passthrough` doesn't CREATE variables — it only forwards pre-existing ones from the parent process environment
- `shell_init_files` only affects terminal() shells — not the Hermes gateway process, not cron jobs, not browser sessions
- Don't store secrets in workspace scripts or commit them to git — always redirect to `~/.hermes/.env`
- The security scanner redacts secrets in tool output — `cat ~/.hermes/.env` will show `***` for values
