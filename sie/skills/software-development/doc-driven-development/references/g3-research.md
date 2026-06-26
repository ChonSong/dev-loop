# g3 — Dialectical Autocoding Reference

**Source**: [github.com/dhanji/g3](https://github.com/dhanji/g3)
**Research Paper**: [Block AI — Adversarial Cooperation in Code Synthesis](https://block.xyz/documents/adversarial-cooperation-in-code-synthesis.pdf)

## Overview

g3 is an open-source Rust AI coding agent by Dhanji R. Prasanna (dhanji). Its key innovation is **dialectical autocoding** — a coach/player adversarial feedback loop where two agents with different system prompts cooperate: the player implements, the coach reviews, and they iterate until the coach signs off.

## Coach/Player Loop Mechanics (Code Level)

The loop lives in `crates/g3-cli/src/autonomous.rs` (a private module, NOT in the execution engine):

```
g3-cli/src/lib.rs::run()
  → mode dispatch: --autonomous flag
  → run_autonomous(agent, project, ...)
    → loop (1..max_turns):
        1. execute_player_turn()   — implements requirements
        2. execute_coach_turn()    — reviews, outputs IMPLEMENTATION_APPROVED or feedback
        3. if approved → break; else feed feedback back to player
    → print_final_report()
    → save_session_continuation()
```

### Player Turn
- Prompt: `build_player_prompt(requirements, requirements_sha, coach_feedback)`
  - First turn: Full requirements + SHA hash. "Implement step-by-step."
  - Subsequent turns: Coach feedback wrapped with "Address the following specific feedback from the coach"
- Max retries: 3 (`MAX_PLAYER_RETRIES`)
- Error handling: ContextLengthExceeded → logs, returns Failed. Panic → terminates. General errors → retry.

### Coach Turn
- **Spawns a brand-new agent** with fresh context — NO context bleed from player
- Feedback extracted via `coach_feedback::extract_from_logs()` — reads coach's session log
- Approval signal: `IMPLEMENTATION_APPROVED` — unambiguous sentinel string
- Max retries: 3 (`MAX_COACH_RETRIES`)
- Empty feedback → `CoachTurnResult::Failed`

### Rejection = Retry, Not Escalate
Same player agent gets coach feedback and iterates. Max turns typically 10. No human escalation path.

## 8 Evidence Gates

| # | Gate | What It Prevents |
|---|------|-----------------|
| 1 | Requirements checklist (✅/❌ per item) | Missing requirements |
| 2 | Compilation/run gate | Code doesn't compile |
| 3 | Functional test gate | Happy-path-only testing |
| 4 | Edge case gate | Missing boundary conditions |
| 5 | Security gap checklist | Auth/validation holes |
| 6 | Approval sentinel string | Vague prose approval |
| 7 | Turn limit circuit breaker | Infinite loops |
| 8 | Fresh context per turn | Rationalization of shortcuts |

## Key Differences

| Aspect | g3 | Our System |
|--------|-----|------------|
| Runtime | Single Rust binary | Hermes cron jobs |
| Agent defs | `agents/*.md` files | Hermes skills (`SKILL.md`) |
| Coach/Player | Same session, same loop | Two cron jobs offset by 5m |
| Project tracking | `requirements.md` + todo | AGENTS.md + checkpoint.json |
| Discovery | User specifies repo | Auto-discovery via AGENTS.md glob |
| Coach model | Config override | `openrouter/owl-alpha` (free) |
| Player model | Same or different | `deepseek-v4-flash` (cheap) |
