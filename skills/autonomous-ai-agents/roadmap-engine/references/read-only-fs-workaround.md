# Read-Only Filesystem Workaround

**Date:** 2026-05-24
**Root cause:** `/opt/data/hermes-sync` mounted read-only in cron container
**Symptoms:** All writable operations fail with `OSError: [Errno 30] Read-only file system`

## The Problem

When the Roadmap Engine runs as a cron job, `/opt/data/hermes-sync` is read-only. Any code that tries to:
- Write snapshots to `roadmap-history/`
- Write reports to `nightly-reports/`
- Commit/push via git
- Clone new repos into `workspace/projects/`
- Create files in any `hermes-sync/` subdirectory

...fails immediately with `OSError: [Errno 30] Read-only file system`.

## The Workaround

Patch all three files to redirect **writable** paths to `/tmp/hermes-sync`, while keeping **read-only** source paths pointing to `/opt/data/hermes-sync`.

### Files to patch

**`roadmap.py`** (data model):
```python
# BEFORE
HERMES_SYNC = Path("/opt/data/hermes-sync")
WORKSPACE   = HERMES_SYNC / "workspace"
ROADMAP_FILE = WORKSPACE / "plans" / "roadmap.json"
HISTORY_DIR  = WORKSPACE / "plans" / "roadmap-history"
MEMORY_DIR   = WORKSPACE / "memory"

# AFTER
HERMES_SYNC = Path("/opt/data/hermes-sync")
WORKSPACE_TMP = Path("/tmp/hermes-sync")
WORKSPACE   = WORKSPACE_TMP / "workspace"
ROADMAP_FILE = WORKSPACE / "plans" / "roadmap.json"
HISTORY_DIR  = WORKSPACE / "plans" / "roadmap-history"
MEMORY_DIR   = WORKSPACE / "memory"
```

**`reporters.py`** (Phase 3 report generator):
```python
# BEFORE
HERMES_SYNC    = Path("/opt/data/hermes-sync")
WORKSPACE      = HERMES_SYNC / "workspace"
MEMORY_DIR     = WORKSPACE / "memory"
PLANS_DIR      = WORKSPACE / "plans"
REPORTS_DIR    = PLANS_DIR / "nightly-reports"

# AFTER
HERMES_SYNC    = Path("/opt/data/hermes-sync")
WORKSPACE_TMP = Path("/tmp/hermes-sync")
WORKSPACE      = WORKSPACE_TMP / "workspace"
MEMORY_DIR     = WORKSPACE_TMP / "workspace" / "memory"
PLANS_DIR      = WORKSPACE_TMP / "workspace" / "plans"
REPORTS_DIR    = PLANS_DIR / "nightly-reports"
```

**`roadmap_engine.py`** (main entry point):
```python
# Add at top of constants block
HERMES_SYNC  = Path("/opt/data/hermes-sync")
WORKSPACE_TMP = Path("/tmp/hermes-sync")   # NEW

# Change WORKSPACE line
WORKSPACE    = WORKSPACE_TMP / "workspace"

# In _execute_task(), change the local path construction
# BEFORE
local = HERMES_SYNC / proj.get("local_path", f"projects/{proj['title']}") if proj else None
# AFTER
local_proj = proj.get("local_path", f"projects/{proj['title']}") if proj else None
local = WORKSPACE_TMP / local_proj if local_proj else None
```

### Pre-run setup (once per session)

```bash
mkdir -p /tmp/hermes-sync/workspace/plans/nightly-reports
mkdir -p /tmp/hermes-sync/workspace/plans/roadmap-history
mkdir -p /tmp/hermes-sync/workspace/memory
mkdir -p /tmp/hermes-sync/workspace/projects
cp /opt/data/hermes-sync/workspace/plans/roadmap.json /tmp/hermes-sync/workspace/plans/roadmap.json
cp -r /opt/data/hermes-sync/projects/repo-transmute /tmp/hermes-sync/workspace/projects/ 2>/dev/null
cp -r /opt/data/hermes-sync/projects/everything-dashboard /tmp/hermes-sync/workspace/projects/ 2>/dev/null
```

### Restoring files post-run

Since `/opt/data/hermes-sync` is read-only, pushed changes cannot be written back during the run. Two options:

**Option A (preferred):** Configure the cron job to run from a writable checkout:
```bash
# Clone hermes-sync to /tmp for the engine run
git clone https://github.com/ChonSong/hermes-sync.git /tmp/hermes-sync-run
# Run from the writable clone
cd /tmp/hermes-sync-run && python scripts/roadmap_engine.py --phase all
# Then push from that clone
```

**Option B:** Accept that outputs go to `/tmp/hermes-sync/` only. The report is still generated and delivered. A separate morning job can copy outputs back when the filesystem is read-write.

## Key Insight

The roadmap.json and existing repos ARE readable from `/opt/data/hermes-sync` — only writes are blocked. So:
- **HERMES_SYNC** = `/opt/data/hermes-sync` (read roadmap.json, read existing repos)
- **WORKSPACE_TMP** = `/tmp/hermes-sync` (write snapshots, reports, diffs)

The two-path pattern is intentional: source paths stay on the read-only mount, output paths go to `/tmp`.