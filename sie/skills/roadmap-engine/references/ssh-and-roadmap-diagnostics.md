# Roadmap Engine — SSH & Roadmap Diagnostics

## SSH Key Location
- Key: `~/.ssh/id_ed25519` (owned by `hermes:hermes`)
- The key path `/home/hermes/.ssh/id_ed25519` does NOT exist — the correct path is `/home/hermes/.ssh/id_ed25519`
- `sean` user cannot auth with this key — `authorized_keys` on host likely missing the `id_ed25519.pub` entry

## Roadmap.json Structure (1053 lines total)
| Section | Lines | Contents |
|---------|-------|----------|
| Header/goals | 1–~100 | goals array, projects array |
| Tasks | ~100–680 | All task objects (todo/done) |
| Ideas | ~681–720 | idea objects |
| Learnings | ~722–1053 | learning objects |

**Truncation gotcha:** `read_file()` with default limit truncates at ~line 500. Always read `offset=501` to get the full task list, ideas, and learnings sections.

## Blockers Found
- **openclaw project**: `ChonSong/openclaw` GitHub repo does not exist. All 9 remaining tasks (task-openclaw-006 through task-openclaw-014) are blocked on the same chain — task-openclaw-005 scaffold must be pushed AND registered before any dependent task can proceed.
- **roadmap_engine.py location**: Live copy is at `/home/sean/.hermes/hermes-sync/scripts/roadmap_engine.py` — NOT in the container backup. Container backup at `/opt/data/hermes-sync/` is read-only and lacks all engine scripts.

## roadmap.json last_modified
- `2026-05-01T23:00:00+11:00` — 25 days stale at time of this session
- No overnight engine runs have updated it since May 1
