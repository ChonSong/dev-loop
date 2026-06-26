# Persistent Phase Engine — Reference Implementation

## Architecture

The Persistent Phase Engine solves the fundamental problem of large project completion: how to maintain state across context compaction, session timeouts, and cron job restarts.

## State Directory Structure

```
/opt/data/project-state/<project>/
├── PHASE_TRACKER.json      # Machine-readable state
├── CHECKPOINTS/            # Human-readable completion records
│   ├── phase-A-complete.md
│   ├── phase-B-complete.md
│   └── ...
├── PROGRESS.md             # Running log
└── NEXT_ACTION.md          # What next session should do
```

## PHASE_TRACKER.json Schema

```json
{
  "project": "<project-name>",
  "total_phases": <int>,
  "current_phase": <int>,
  "status": "not_started|in_progress|complete|failed",
  "phases": [
    {
      "id": "<phase-id>",
      "name": "<human-readable name>",
      "status": "pending|complete|failed",
      "commit": "<git commit hash>",  // Only for complete phases
      "checkpoint": "<filename.md>",  // Only for complete phases
      "error": "<error message>"      // Only for failed phases
    }
  ],
  "next_action": "<brief description>",
  "next_action_details": "<detailed instructions>",
  "workdir": "/opt/data/<project>/",
  "last_updated": "<ISO timestamp>"
}
```

## Cron Job Template

```yaml
name: "phase-engine: <project> completion"
schedule: "every 30m"
repeat: "1/20"  # Format: "N/limit"
deliver: "discord"
enabled_toolsets: ["terminal", "file"]
prompt: |
  Execute next phase of <project> using the persistent phase engine.

  STATE_DIR: /opt/data/project-state/<project>/
  WORKDIR: /opt/data/<project>/

  INSTRUCTIONS:
  1. Read PHASE_TRACKER.json to find the next pending phase.
  2. **VERIFY GIT BEFORE EXECUTING**: Run `cd <workdir> && git log --oneline -10 && git status --short`.
     If the pending phase's expected commit is already in git, the phase is already done —
     update the tracker to match git reality and stop. Tracker drift is the #1 cause of
     wasted token budget: prior session completes the phase, dies before updating tracker.
  3. If all phases complete → report success and stop.
  4. If next phase is genuinely pending → execute it completely.
  5. After execution:
     a. Verify build/tests pass
     b. git add + commit + push
     c. Write checkpoint to CHECKPOINTS/phase-{id}-complete.md
     d. Update PHASE_TRACKER.json with completion status AND the commit hash
  6. Report results.

  CRITICAL RULES:
  - Execute ONE phase per run (the first pending one)
  - NEVER skip phases - execute in order
  - ALWAYS verify git state first — tracker may say "pending" when work is already done
  - ALWAYS verify before committing
  - If phase fails, write error to tracker and stop
  - Each phase should be under 50K tokens of work
```

## Checkpoint Template

```markdown
# Phase <id> Complete

**Completed:** <timestamp>

## What Was Done
- <task 1>
- <task 2>

## Files Changed
- <file 1>
- <file 2>

## Build Status
- Build: ✅ passed
- Tests: ✅ 10/10 passed

## Git Commit
- Hash: <commit hash>
- Message: <commit message>

## Decisions Made
- <decision 1 with rationale>

## Pitfalls Encountered
- <pitfall 1 and how it was resolved>
```

## Token Budget

- Per phase: ~50K tokens (work + verification + commit)
- State management: ~5K tokens (read/write tracker)
- 1M token project: ~20 phases × 50K = 1M tokens
- Overhead: ~20 cron runs × 5K = 100K
- **Total: ~1.1M tokens across 20+ sessions**

## Why This Works

1. **Survives context compaction** — State is on disk, not in memory
2. **Survives session timeouts** — Next session reads tracker and continues
3. **Survives interruptions** — Checkpoints mark safe resume points
4. **Self-healing** — Failed phases can be retried from checkpoint
5. **Auditable** — Complete history of what was done and when

## Real Example: hermes-web-computer

Session date: 2026-05-11 to 2026-05-12

Phases completed:
- A-B: Illogical Impulse CSS + Tailwind + WorkspacePill + Dock (commit: 21819ae)
- C: Floating panels glassmorphism (commit: 08eb7ef)
- D-F: Command palette + Monaco theme + scrollbars (commit: dd1caa1)
- G: Drag-and-drop + agent context awareness (commit: 22ecbab)
- H: Workspace system + keyboard shortcuts (commit: 05a27b3)
- I: E2E tests (commit: 4c7098e)
- J: Floating window drag + chrome + workspace persistence (commit: 2aeabf3)

Remaining:
- K: Tile enter/exit animations
- L: Shift+Alt+Number move tile to workspace
- M: Agent output → filesystem drag
- N: Lighthouse audit
- O: Final polish + documentation
