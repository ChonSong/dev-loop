# Memory File Location & Permission Matrix

Canonical locations discovered 2026-05-10.

## Read-Write (accessible from cron + TUI)
| Path | Owner | Notes |
|------|-------|-------|
| `/opt/data/memories/USER.md` | hermes:hermes | User profile |
| `/opt/data/workspace/memory/heartbeat-state.json` | hermes:hermes | Heartbeat state |

## Read-Only (cron reads OK, writes fail)
| Path | Mount | Notes |
|------|-------|-------|
| `/opt/data/hermes-sync/memory/MEMORY.md` | `ro,noatime` | Canonical synced memory — writes must go through TUI or host SSH |
| `/opt/data/hermes-sync/memory/USER.md` | `ro,noatime` | Synced user profile |

## Root-Owned (cron cannot read)
| Path | Owner | Notes |
|------|-------|-------|
| `/opt/data/memories/MEMORY.md` | root:root | Permission denied from hermes user |

## Stale Lock Files (safe to remove)
- `/opt/data/memories/MEMORY.md.lock` (Apr 26)
- `/opt/data/hermes-sync/memory/MEMORY.md.lock` (Apr 29, read-only fs — can't remove from container)

## Write Strategy from Cron
1. Try `memory` tool first (may be disabled in cron)
2. Fall back to `terminal` → `cat` for reads
3. For writes to hermes-sync path: use `ssh sean@localhost "echo '...' >> /opt/data/hermes-sync/memory/MEMORY.md"` if SSH key is available
4. If SSH unavailable, include pending entries in cron response for TUI session to apply
