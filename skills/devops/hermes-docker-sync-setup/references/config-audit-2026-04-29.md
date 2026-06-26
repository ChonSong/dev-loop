# hermes-sync Config Audit — 2026-04-29

Three root-cause findings from a full migration audit. These patterns recur because
hermes-sync config is derived from the live config on the machine where it was first
committed — which may contain machine-specific paths, disabled features (for safety),
and OpenClaw-era service references.

---

## Finding 1 — `terminal.cwd` is Machine-Specific

**Config:**
```yaml
terminal:
  cwd: /home/sean/workspace   # machine-specific path
```

**Problem:** `/home/sean/workspace` does not exist on a fresh Ubuntu VM. Every
terminal/bash/shell tool call fails silently or with `FileNotFoundError`.

**Fix applied:** `cwd: /opt/data/workspace` — a path inside the container's bind mount,
guaranteed to exist because `setup.sh` creates it.

**Rule:** `terminal.cwd` must always be a path inside `/opt/data` (the bind mount root),
never a host-specific absolute path.

---

## Finding 2 — `approvals.cron_mode: deny` Silently Kills All Cron Jobs

**Config:**
```yaml
approvals:
  cron_mode: deny   # default in safety-oriented configs; wrong for automation
```

**Problem:** With `cron_mode: deny`, every cron job is rejected at execution time — not
paused for approval, not logged, just silently blocked. The cron job table shows
`last_run: never` for all jobs with no explanation.

**Fix applied:** `cron_mode: lazy` — prompts once per job, then auto-approves subsequent
runs. This is the right default for a personal agent where you want cron automation
but occasional visibility.

**Why it was set to `deny`:** The config was derived from a production-safety-oriented
Hermes config where `deny` is appropriate. In a personal migration context it kills
all automation silently.

---

## Finding 3 — `custom_providers` Referenced a Dead Service

**Config (before):**
```yaml
custom_providers:
  minimax:
    url: http://localhost:4001/v1   # rate_smoother from OpenClaw era
  zai:
    url: http://localhost:4001/v1   # same
```

**Problem:** `localhost:4001` was the rate smoother service from the OpenClaw stack.
It was never migrated. Provider calls to `minimax`/`zai` via these entries all fail.

**Fix applied:** Removed both entries. `minimax` uses its standard provider config
with `base_url: https://api.minimax.io/v1` and `${MINIMAX_API_KEY}` env var.
`zai` resolves natively without a custom provider entry.

**Rule:** Never carry forward `localhost` URLs in `custom_providers`. Rate limiting
and provider aggregation are handled differently in Hermes.

---

## Also Fixed

| Item | Fix |
|------|-----|
| `setup.sh` | Added `git init` for `~/.hermes` (required by backup cron job) |
| `hermes-sync/workspace/` | Restored HEARTBEAT.md, TOOLS.md, heartbeat-state.json, memory/search.sh |

---

## Verified Clean

After fixes, `git status` in hermes-sync shows only intentional tracked changes.
Push to origin: `git push origin master` (repo uses `master` branch, not `main`).
