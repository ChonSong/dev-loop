# `/goal` vs Persistent Phase Engine — When to Use Which

## `/goal` (Ralph Loop)

**What it is:** A built-in Hermes slash command (`/goal <text>`) that sets a standing goal auto-continuing across turns within a SINGLE session.

**How it works:**
1. After each turn, auxiliary `goal_judge` model evaluates: "Is the goal satisfied?"
2. If not done → continuation prompt fed back into same session
3. Continues until: goal achieved, turn budget exhausted (default 20), or user interrupts

**Source:** `/opt/hermes/hermes_cli/goals.py` (593 lines)

**Best for:**
- Single-session tasks (research, quick fixes, single-file changes)
- Tasks under 150K tokens (before context compaction hits)
- Tasks where the user stays present and can interrupt if needed

**Fails for:**
- Multi-phase projects (context compaction loses intermediate state)
- Tasks needing GitHub commits between phases
- Tasks that must survive session restarts
- Work requiring build/test verification between phases

## Persistent Phase Engine (autonomous-cron-pipeline skill)

**What it is:** Disk-based state machine with JSON tracker + checkpoint files + chained cron jobs.

**Best for:**
- Large projects (1M+ tokens)
- Multi-phase work needing independent commits
- "Let it cook" autonomous execution
- Work that must survive context compaction, session deaths, timeouts

**Why it works where `/goal` fails:**
- State on disk, not in memory
- Each phase commits independently to GitHub
- Cron jobs get fresh context windows
- Checkpoints mark safe resume points

## Decision Rule

| Scenario | Use |
|----------|-----|
| Single task, user present, < 150K tokens | `/goal <text>` |
| Multi-phase project, user wants to step away | Persistent Phase Engine |
| Need commits between phases | Persistent Phase Engine |
| Quick research or summary | `/goal` |
| 3+ phases, complex work | Persistent Phase Engine |
| User questions quality mid-session | STOP → switch to Persistent Phase Engine |

## Key Gotcha

The `hermes-agent` skill docs previously claimed `/goal` doesn't exist. **It does exist** — it's implemented in `/opt/hermes/hermes_cli/goals.py` and registered in `commands.py`. The skill docs were outdated. Always check the actual source code before declaring a feature doesn't exist.
