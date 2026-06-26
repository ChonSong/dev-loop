# Output File Inspection Workflow

When terminal is blocked (e.g., by Tirith security scanner) or you need to verify actual job health beyond `last_status: "ok"`, use file-tool-based inspection.

## Rationale

The cron engine's `last_status` field tracks whether the agent completed without crashing — it does NOT track whether the actual task logic succeeded. A job can return `last_status: "ok"` for every run while silently failing (e.g., terminal blocked, service down, tool denied). Output files tell the real story.

## Workflow

### 1. Locate the cron state

The canonical path is container-specific. Check these in order:

| Container / Context | Path |
|---------------------|------|
| Hermes WebUI container (hermeswebui user) | `/home/hermeswebui/.hermes/cron/jobs.json` |
| Hermes sync container (sc user) | `/home/sc/.hermes/cron/jobs.json` |
| Generic fallback | `~/.hermes/cron/jobs.json` |

Output lives at the same base path under `cron/output/<job-id>/`.

### 2. Read jobs.json

```python
from hermes_tools import read_file

data = read_file("/home/sc/.hermes/cron/jobs.json")
# JSON with a "jobs" array containing all job definitions + state
```

Each job entry contains:
- `id`, `name` — identity
- `last_status` — `"ok"` (agent ran) or `"error"` (agent crashed)
- `last_error` — engine-level error message or `null`
- `last_delivery_error` — delivery failure or `null`
- `last_run_at` — ISO timestamp of most recent run
- `state` — `"scheduled"`, `"paused"`, etc.
- `enabled` — boolean
- `repeat.completed` / `repeat.times` — lifetime run counter & budget

### 3. Find and read output files

Output files are written as `<timestamp>.md` under `cron/output/<job-id>/`.

```python
# List output files for a specific job
output_dir = "/home/sc/.hermes/cron/output/<job-id>"
files = search_files(pattern="*.md", path=output_dir, target="files", output_mode="files_only")

# Sort and read the most recent
files_sorted = sorted(files.split("\n"))
most_recent = files_sorted[-1]
read_file(most_recent)
```

### 4. What to look for in output files

| Signal | Meaning |
|--------|---------|
| `FAILED` in title or first lines | Job logic failed |
| `HTTP 530`, `error 1033` | Cloudflare tunnel issue |
| `HTTP 5xx`, `HTTP 4xx` | Service error or authorization issue |
| `[SILENT]` as sole output | Job produced nothing (may be normal for quiet jobs, or may mean it couldn't execute) |
| `RuntimeError`, `Broken pipe` | Tool or path failure |
| `blocked by security scanner` | Tirith or similar blocking terminal |
| Empty output (0 lines) | Job may have crashed before writing output |

### 5. Cross-reference with jobs.json

- If `last_status: "ok"` AND output shows `FAILED` → **functional failure masked by engine**. Flag as a real issue.
- If `last_status: "ok"` AND output is blank/empty → job may have crashed silently or produced no output (check other recent runs).
- If `last_run_at` is days old while schedule says "every 15m" → gateway was down or scheduler stalled.
- If `last_error` is null but `last_delivery_error` has a message → job ran but couldn't deliver.

### 6. Use Other Cron Outputs to Confirm Block Scope

When terminal is blocked by a security scanner, you can still check whether OTHER cron jobs are also failing with the same pattern — without running any commands:

1. List output directories: check `/home/sc/.hermes/cron/output/` for all job ID directories
2. Pick one or two other jobs (especially ones that historically produced rich output)
3. Read their most recent output file — if they also report "terminal blocked by security scanner" or similar, the scope is confirmed as systemic
4. Check `jobs.json` to see if the scheduler is still ticking (are `next_run_at` timestamps advancing?)

This cross-referencing is faster than diagnosing each job individually, and it confirms you're looking at a systemic issue rather than a job-specific one.

## Reference: output inspection applied (June 13, 2026)

When this workflow was first used, it revealed:
- **16/16 jobs** showed `last_status: "ok"` — engine view looked perfect
- **3/16 jobs** were actually failing — functional failures found only via output file inspection
- **1 CRITICAL** — GTO Watchdog returning HTTP 530 for 20+ consecutive hours (Cloudflare tunnel)
- **1 CRITICAL** — auto-continue-work terminal-blocked for 9+ hours
- **1 systemic** — Tirith security scanner blocking all terminal-based jobs

Without output file inspection, all failures would have been invisible.
