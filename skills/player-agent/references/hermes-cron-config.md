# Hermes Cron Job Configuration

From Hermes Agent docs at hermes-agent.nousresearch.com and hands-on setup.

## Per-Job Model Override

Each cron job can specify a different model/provider:

```yaml
# In the cron job record (via cronjob tool):
model: "openrouter/owl-alpha"
provider: "openrouter"
```

When set, the cron execution uses that specific model. When `null`, uses the global default (set via `hermes model`).

## Skill Loading in Cron Jobs

Skills are loaded at job start, not dynamically mid-session. The cron scheduler:

1. Loads skills in the specified order (`skills: ["player-agent"]`)
2. Each skill's SKILL.md is injected as **user messages** (context), NOT into the system prompt
3. The job's prompt is appended as the task instruction
4. The agent processes the combined skill context + prompt

Key constraint: skills CANNOT override the base system prompt. They're context, not system overrides.

## approvals.cron_mode

```yaml
approvals:
  cron_mode: approve  # Auto-approve dangerous commands in cron
```

- `deny` (default): dangerous commands are automatically denied (no human to prompt)
- `approve`: dangerous commands auto-approved for headless automation
- Hardline blocklist always applies: `rm -rf /`, fork bombs, `mkfs.*` on mounted devices, piping untrusted URLs to `sh`

## Scheduling Formats

Cron supports multiple schedule formats:
- `every 60m` — every N minutes from creation
- `0 * * * *` — standard cron expression (at minute 0 of every hour)
- `5 * * * *` — offset pattern (at minute 5 of every hour)
- `0 */2 * * *` — every 2 hours
- `0 16 * * *` — daily at 16:00
- `2026-06-15T09:00:00` — one-shot ISO timestamp

## Coach/Player Offset Pattern

Coach runs offset from player to allow time for commits:

```
Player: 0 * * * *  (:00)
Coach:  5 * * * *  (:05)  — 5 min offset
```

This gives the player 5 minutes to commit before the coach starts reviewing.

## Provider Discovery

Model availability is cached in `/home/sc/.hermes/models_dev_cache.json`. Contains models from all configured providers (Requesty, OpenRouter, HuggingFace, etc.) with pricing, context limits, and capabilities.

## Fresh Agent Per Tick

Each cron job tick creates a completely new agent session with:
- No conversation history from previous ticks
- No shared context with other agents (player and coach are fully isolated)
- Fresh system prompt assembly (stable → context → volatile)
