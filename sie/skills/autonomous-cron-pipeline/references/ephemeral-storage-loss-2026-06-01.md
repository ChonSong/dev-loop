# Ephemeral Storage and Autonomous Engine Loss — 2026-06-01

## The Incident

The Roadmap Autonomy Engine (`roadmap_engine.py`) was a ~1,126-line Python script that ran a 3-phase autonomous loop (research → execute → report). It was iteratively improved across 5 cron sessions (May 24–28) to v1.1, fixing executor bugs, test framework detection, and dedup logic.

**It was only stored in `/tmp/hermes-sync/scripts/`** — tmpfs that gets wiped on container restart. It was never committed to GitHub. When the container restarted, the script was permanently lost. The cron job (`6576b5f87515`) now errors with `RuntimeError: Connection error` on every run.

## Root Cause

1. The roadmap engine script lived in `/tmp/` — ephemeral storage
2. It was never committed to any git repo
3. The cron job prompt hardcodes a path to the script — so it breaks silently when the file is gone
4. `deliver: local` means errors go nowhere visible

## Similar At-Risk Projects

| Project | Location | Risk | Tests |
|---------|----------|------|-------|
| GTO Wizard Clone | `/tmp/gto-wizard-clone/` | HIGH — will be wiped on restart | 139+ passing |
| Roadmap Engine | `/tmp/hermes-sync/scripts/` | LOST — already gone | N/A |

## The Rule

**Never store working code or autonomous engine scripts in `/tmp/`.** Always use persistent paths:
- `/workspace/<project>` — survives container restarts, backed up by cron
- `/opt/data/<project>` — persists if mounted from host
- Git repos on GitHub — immune to local failures

**Before creating a cron job that references a script:**
1. Verify the script exists at the hardcoded path
2. Verify the path is persistent (not `/tmp/` or other tmpfs)
3. If the script is valuable, commit it to a git repo
4. Test the full command manually before scheduling

## Recovery Checklist

When you discover a cron job referencing a missing file at a `/tmp/` path:
1. Check if it's in GitHub: `cd /tmp && git clone <repo> && find . -name '<script>'`
2. If found, copy to persistent path and update the cron job prompt
3. If not found, ask the user whether to rebuild or abandon
4. If rebuilding, check git history for the spec/architecture
