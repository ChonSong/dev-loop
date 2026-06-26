# OpenClaw Migration Audit

Findings from reviewing the migrated zoul workspace (2026-04-29).

## What was migrated ✅

- `zoul/` workspace → `zoul.archived/` then `hermes-sync/` (config, skills, memory, docker, setup.sh)
- `SOUL/USER/TOOLS/MEMORY/HEARTBEAT` → root `memory/`
- Delegation patterns → `skills/agents/zoul-delegation/`
- `zoul`, `zoul-soul`, `zoul-delegation` agents in `skills/agents/`

## Remaining OpenClaw artifacts ⚠️

### 1. `skills/openclaw-imports/` — mostly inert

Contains skills ported from ClawHub that still work but reference OpenClaw tooling:

| Skill | Status |
|-------|--------|
| `self-improving-agent/` | Active hook migrated. ClawHub `.clawhub/` origin.json is stale (registry offline). Hook system (`hooks/openclaw/`) is dead — OpenClaw is gone. |
| `gmail/` | Works. Standard Gmail API/SMTP via himalaya CLI. |
| `sonoscli/` | Works. Standard Sonos CLI tool. |
| `notion-api/` | Works. Standard Notion API. |
| `morning-briefing/` | Works. Generic briefing prompts. |
| `affine-logger/` | Works. AFFiNE API is platform-agnostic. |
| `gcalcli-calendar/` | Works. Standard gcalcli tool wrapper. |
| `hybrid-orchestrator/` | Review content — may have OpenClaw-specific delegation patterns. |
| `api-gateway/` | Large (5 files, `references/` dir). Needs content review for OpenClaw refs. |
| `automation-workflows/` | Generic workflow design — likely Hermes-compatible as-is. |

**Recommendation:** Strip `.clawhub/` origin metadata from all. Move compatible skills to proper categories. Keep `openclaw-imports/` as a staging area.

### 2. `skills/agents/zoul` SKILL.md

Has 3 OpenClaw mentions. Should be reviewed for delegation patterns that still apply to Hermes.

### 3. `config.yaml` — stale `zoulhassouldbot`

```
zoulhassouldbot:
  botToken: ${TELEGRAM_BOT_TOKEN_ZOULSOUL}
```

This Telegram bot is decommissioned. Remove if confirmed dead.

### 4. `.clawhub/` origin.json files

Five skills have `{"registry": "https://clawhub.ai", "slug": "..."}` pointing to an offline/deprecated registry. These are inert — registry is gone but files remain. Strip the `.clawhub/` directories.

## Cleanup commands (run on new machine after setup)

```bash
# Remove dead OpenClaw hook system
rm -rf ~/.hermes/skills/openclaw-imports/self-improving-agent/hooks/openclaw/

# Strip ClawHub origin metadata
find ~/.hermes/skills/openclaw-imports -name '.clawhub' -type d -exec rm -rf {} +

# Remove stale zoulhassouldbot from config (backup first)
cp ~/.hermes/config.yaml ~/.hermes/config.yaml.bak
# Then edit: remove the zoulhassouldbot: block

# Restart gateway
docker compose -f ~/hermes-sync/docker/docker-compose.yml restart
```

## What's NOT migrated (intentional)

- `zoul/` agent code — superseded by Hermes native agents
- ClawHub registry sync — registry is offline
- OpenClaw's TypeScript hook handlers — incompatible (Hermes uses Python hooks)

## What's new that didn't exist in OpenClaw

- `hooks/self-improvement/` — Hermes-native Gateway hook (session:start/end learnings reminder)
- 6-hour cron sync job to GitHub
- GHCR pre-built image (`ghcr.io/chonsong/hermes-sync:latest`)
