# Hermes System Prompt Architecture for Cron Jobs

## Three Tiers of Prompt Assembly

The system prompt is assembled in **three ordered tiers** (from agent/system_prompt.py):

| Tier | Components | Notes for Cron |
|------|-----------|----------------|
| **1. Stable** | Identity (SOUL.md or fallback), tool/model guidance, skills prompt, environment hints, platform hints | Always included |
| **2. Context** | Caller-supplied system_message, project context files (AGENTS.md, CLAUDE.md, .cursorrules) | Included when workdir is set on a cron job |
| **3. Volatile** | Built-in memory snapshot (MEMORY.md), user profile (USER.md), external memory-provider block, timestamp/session/model/provider line | Included — but cron has no interactive session history |

**Final assembly order:** `Stable → Context → Volatile` (joined with `\n\n`)

## 10-Layer Concrete Structure

1. **Agent Identity** — `~/.hermes/SOUL.md` or `DEFAULT_AGENT_IDENTITY` fallback
2. **Tool-aware behavior guidance** — memory instructions, tool enforcement, session search
3. **Honcho static block** (when active)
4. **Optional system message** (from config or API)
5. **Frozen MEMORY snapshot**
6. **Frozen USER profile snapshot**
7. **Skills index** — compact index of available skills (names + descriptions)
8. **Context files** — AGENTS.md, .cursorrules, etc.
9. **Timestamp + optional session ID**
10. **Platform hint**

## Cron Job Mechanics

Each cron tick:

```
tick()
  1. Acquire scheduler lock
  2. Load all jobs from jobs.json
  3. Filter to due jobs
  4. For each due job:
     a. Set state to "running"
     b. Create fresh AIAgent session (no conversation history)
     c. Load attached skills IN ORDER (injected as user messages)
     d. Run the job prompt through the agent
     e. Deliver response
     f. Update run_count, compute next_run
     g. Update state → scheduled/completed
  5. Write updated jobs back to jobs.json
  6. Release scheduler lock
```

Key point: Cron jobs run in a **completely fresh agent session** with no conversation history from previous runs. Skills are injected as user messages (context), not as system prompt. This means the SKILL.md content is available as conversation context, not as system-level instructions.

## Skill Loading

- Skills must be installed before they can be attached to cron jobs
- Skill names are case-sensitive
- Skills requiring interactive tools (clarify, messaging) won't work in cron
- **Multi-skill ordering matters:** Skills load in the order specified
- Skills are injected as user messages, not as part of the system prompt
- The skills index (names + descriptions) is in the stable tier for routing
- Full SKILL.md content is loaded on demand via skill_view() or injected as context

## Model Configuration for Cron Jobs

Per-job model and provider overrides are stored in the job record:
```json
{
  "model": "openrouter/owl-alpha",
  "provider": "openrouter"
}
```

When set, the cron execution uses that specific model/provider instead of the global default. When omitted/null, uses global config.

## Approvals for Cron

```yaml
approvals:
  cron_mode: deny      # deny (default) - dangerous cmds auto-denied
          : approve   # approve - auto-approve dangerous cmds
```

Even with `cron_mode: approve`, the **Hardline Blocklist** (rm -rf /, fork bombs, mkfs on mounted devices, piping untrusted URLs to sh) is always enforced.
