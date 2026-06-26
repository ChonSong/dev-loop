# Python uv Workspace + Docker Multi-Stage Build

## The Problem

The agent-os monorepo has three Python packages under `packages/`:
- `packages/nanobot/` → `nanobot-ai`
- `packages/observability/` → `agent-os-observability`
- `packages/agent-adapter/` → `agent-os-agent-adapter`

The Dockerfile `py-deps` stage copies these packages but they weren't being installed because:
1. The root `pyproject.toml` had no `dependencies` section
2. `uv sync --frozen` only installs what's in the lockfile — local packages were not locked

## The Fix

### Root pyproject.toml

The root must declare the workspace packages as dependencies AND tell uv where to find them:

```toml
[project]
name = "agent-os"
version = "0.0.0"
requires-python = ">=3.11"
dependencies = [
    "nanobot-ai",
    "agent-os-observability",
    "agent-os-agent-adapter",
]

[tool.uv.sources]
nanobot-ai = { workspace = true }
agent-os-observability = { workspace = true }
agent-os-agent-adapter = { workspace = true }

[tool.uv.workspace]
members = [
    "packages/nanobot",
    "packages/observability",
    "packages/agent-adapter",
]
```

### uv.lock

Must be regenerated after adding the workspace config:
```bash
cd /home/sean/.hermes/agent-os
uv lock
```

If you skip the `[tool.uv.sources]` section, `uv lock` fails with:
```
× `nanobot-ai` is included as a workspace member, but is missing an entry
  in `tool.uv.sources`
```

### Dockerfile py-deps stage

```dockerfile
FROM python:3.13-slim AS py-deps
WORKDIR /app
RUN pip install --break-system-packages uv
COPY pyproject.toml uv.lock ./
COPY packages/nanobot/ packages/nanobot/
COPY packages/observability/ packages/observability/
COPY packages/agent-adapter/ packages/agent-adapter/
RUN uv sync          # NOT --frozen — workspace packages must be built
```

The `RUN uv sync` (without `--frozen`) builds and installs the local packages from the copied source directories. Output:
```
Built agent-os-agent-adapter @ file:///app/packages/agent-adapter
Built agent-os-observability @ file:///app/packages/observability
Built nanobot-ai @ file:///app/packages/nanobot
Installed 87 packages in 220ms
```

## Common Failure Modes

| Error | Cause | Fix |
|-------|-------|-----|
| `No solution found when resolving dependencies: agent-os-agent-adapter was not found` | Package names not declared in root `pyproject.toml` deps | Add them to `dependencies = [...]` |
| `` `nanobot-ai` is included as a workspace member, but is missing an entry in `tool.uv.sources` `` | uv can't resolve workspace packages without explicit sources mapping | Add `[tool.uv.sources]` entries |
| `uv sync --frozen` installs only 12 packages (dev-only) | `--frozen` locks to exact lockfile contents; workspace packages aren't in lockfile until `uv sync` (no flags) runs first | Use `uv sync` without `--frozen` in the Dockerfile |
| `exec /app/.venv/bin/nanobot: no such file or directory` | Shebang `#!/app/.venv/bin/python` can't find interpreter (mismatch between venv Python version and runtime Python) | Ensure runtime stage has same Python minor version as venv build stage |
| `ModuleNotFoundError: No module named 'X'` at runtime | Package has an undeclared import (runtime dependency not in `pyproject.toml` deps) | File bug against the package — Dockerfile stage correctly installs all declared deps |
