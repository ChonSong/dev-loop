# UV Workspace in Hybrid Python/Node Monorepos

When a monorepo contains both Python packages (with pyproject.toml) and Node packages (with package.json), uv workspace membership must be explicit — `packages/*` glob will fail if any subdirectory lacks a pyproject.toml.

## The Problem

```toml
# ❌ Fails: packages/types is a Node-only package without pyproject.toml
[tool.uv.workspace]
members = ["packages/*"]
```

Error: `Workspace member packages/types is missing a pyproject.toml`

## The Fix

List only Python packages explicitly:

```toml
# ✅ Works: only Python packages are uv workspace members
[tool.uv.workspace]
members = ["packages/poker-core"]
```

Or use multiple specific globs:

```toml
[tool.uv.workspace]
members = ["packages/poker-core", "apps/api", "apps/worker"]
```

## Real Case: gto-wizard-clone monorepo

The root `pyproject.toml` had no workspace config at all. The `packages/` directory contained:
- `packages/poker-core/` — Python package with pyproject.toml (depends on numpy)
- `packages/types/` — TypeScript/Node package (no pyproject.toml)
- `packages/ui-components/` — Node/React package (no pyproject.toml)

Adding `[tool.uv.workspace]` and regenerating `uv.lock` properly resolved gto-poker + numpy + numba + llvmlite into the lock file.

## Verify

```bash
uv lock --check         # Confirms lock file consistency
```

## .gitignore Patterns for Hybrid Monorepos

After adding uv workspace config, ensure `.gitignore` covers:

```gitignore
dist/
snapshots/
final-snapshots/
final-refs/
prd-snapshots/
prd-refs/
refs/
scripts/
tunnel-info.json
*creds.json
ui-qa*.json
ui-qa*.js
```

Without these, `git add -A` will sweep credentials (tunnel secrets), screenshots (200+ PNGs), and deployment scripts into commits.
