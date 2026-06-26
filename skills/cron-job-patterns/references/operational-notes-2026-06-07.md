# Operational Observations — Cron Context Limitations

## Background Tool Restrictions (confirmed 2026-06-07)

Background cron jobs in the Hermes container have a restricted tool whitelist.

Allowed: memory, skill_manage, skill_view, skills_list
Blocked: write_file, read_file, patch, terminal, execute_code, session_search, browser_*, delegate_task

Error on blocked tool: "Background review denied non-whitelisted tool: <name>. Only memory/skill tools are allowed."

Workarounds:
1. Run as foreground WebUI session instead of background cron
2. Design cron prompts to only use memory + skill tools
3. Pre-load findings into memory from a WebUI session for cron to reference

## Memory Tool Capacity

Hard 2,200 char limit. Current usage near capacity as of 2026-06-07.
Overflow error: "Replacement would put memory at 2,398/2,200 chars."
Action: prune old entries or request limit increase.

## WebUI /api/sessions Slowness

Consistently 5-13s per request. Bottlenecks: get_cli_sessions (3-6s), redact_sessions (0.7-6.6s), lineage_metadata (0.1-1.8s).

## error.log Signals (2026-06-07)

- Slow WebUI warnings (all /api/sessions requests 5-13s)
- Memory tool overflow errors recurring
- Background review denials (pattern above)
- skill_manage loop failures: "file_content is required for 'write_file'" when file_content param omitted
- Missing skill: "Skill 'creative/hyperframes' not found" — old path after skill reorganization
