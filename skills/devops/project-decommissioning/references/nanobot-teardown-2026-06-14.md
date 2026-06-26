# Nanobot Teardown — June 14, 2026

**Source:** Session `7df11d91aa93` + `20260614_195617_7462a6`

## Context

Nanobot was a fork of HKUDS/nanobot (41K★, ultra-lightweight AI agent framework) deployed as two containers (api + gateway) that had been crash-looping with no clear recovery path. Hermes had already replaced nanobot as the primary agent framework.

## What Was Preserved

| Asset | Size | Reason |
|---|---|---|
| WhatsApp bridge (`bridge/src/`) | ~25KB | Custom Node.js/Baileys bridge with WebSocket, QR auth, media handling |
| Workspace skills (gmail, summarize-content, reddit, coolify) | ~50KB | Reusable skill definitions, portable to Hermes |
| `soul-reference.md` | ~5KB | Nanobot's philosophy document |

**Backup location:** `/home/sc/workspace/archived-nanobot/` (212KB total)

## What Was Removed

- 2 Docker containers: `nanobot-api`, `nanobot-gateway`
- 2 Docker images: ~851MB each
- Local clone: 76MB
- Config: `~/.nanobot/`
- Hermes skills: `nanobot-to-hermes-migration`, `nanobot-integration-plan`, debugging ref
- seans-reporepo entries: `owned/ChonSong_nanobot.md`, `owned/ChonSong_nanobot-workspace.md`, `starred/HKUDS_nanobot.md`, `starred/lucmuss_nanobot-webgui.md`
- GitHub repo: Already deleted previously (remote returned 404)

## What Was Left Alone (part of other projects)

- `agent-os/packages/nanobot/` — facade/integration layer within agent-os
- `agent-os/apps/dashboard/agent-core/src/nanobot_proxy.py` — proxy within agent-os
- `claw-aie-harness/scripts/sync_nanobot_channels.sh` — harness script
- `everything-dashboard/agent/test_nanobot.py` — test reference
- `openclaw-backup/workspace/codi/code-library/nanobot_*.py` — archived code library

## Disk Reclaimed

~1.7GB total (containers + images + repo + config)
