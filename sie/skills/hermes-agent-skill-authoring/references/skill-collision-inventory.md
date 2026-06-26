# Skill Collision Inventory

Skills that share the same name across category directories, causing `skill_view` ambiguity.
The tool REFUSES to guess — it throws an error listing both paths.

## Known Collisions (2026-06-07)

| Skill Name | Path 1 | Path 2 |
|---|---|---|
| `hermes-agent` | `hermes-agent/` | `autonomous-ai-agents/hermes-agent/` |
| `hermes-agent-skill-authoring` | `hermes-agent-skill-authoring/` | `software-development/hermes-agent-skill-authoring/` |
| `zoul` | `zoul/` | `agents/zoul/` |
| `zoul-soul` | `zoul-soul/` | `agents/zoul-soul/` |
| `zoul-delegation` | `zoul-delegation/` | `agents/zoul-delegation/` |
| `grill-me` | `grill-me/` | `-grill-me/` (leading hyphen) |
| `grill-with-docs` | `grill-with-docs/` | `-grill-with-docs/` |

## Workaround

When `skill_view(name='x')` fails with "Ambiguous skill name":
1. Use `skill_manage(action='edit', name='x', ...)` — hits the first match (usually root-level)
2. Or use the categorized path: `skill_manage(action='edit', name='category/x', ...)`

## Long-term Fix

Deduplication pass: merge duplicate content into one canonical skill, delete the duplicate,
and update any cron jobs or references that pointed to the old path.
