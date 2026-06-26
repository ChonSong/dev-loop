# g3 Coach/Player Loop — Reference

From the Block AI Research paper "Adversarial Cooperation in Code Synthesis" (Dec 2025) and g3's Rust implementation at github.com/dhanji/g3.

## Architecture

The loop lives in g3's `crates/g3-cli/src/autonomous.rs`. Not in the execution engine — it's a CLI-mode orchestrator.

```
loop (1..max_turns):
  1. execute_player_turn()    — implements against requirements
  2. execute_coach_turn()     — reviews, outputs IMPLEMENTATION_APPROVED or feedback
  3. if approved → break; else feed feedback to player, loop
```

## Key Patterns

### Fresh Context Per Turn
The coach spawns as a **brand-new agent** with no context from the player's session. No shared history, no accumulated mental model that would rationalize shortcuts. This is the single most important design decision.

Implementation: `let mut coach_agent = Agent::new_autonomous_with_project_context_and_quiet(coach_config, ...);`

### Separate Model Configs
Coach and player can use different models/providers:
```toml
[providers]
coach = "anthropic.coach"      # Lower max_tokens (32k), lower temp
player = "anthropic.player"    # Higher max_tokens (64k)
```

### Approval Sentinel
The coach must output a specific string: `IMPLEMENTATION_APPROVED`. Not prose, not "looks good" — an unambiguous signal parsed by the orchestrator. Absence of the sentinel = rejection.

### Rejection = Retry, Not Escalate
On rejection, coach feedback is fed back to the SAME player agent for another iteration. The player gets: "Address the following specific feedback from the coach" + original requirements. Max turns typically 10. No human escalation path.

### Error Surface
The coach sees the full output of every player tool call — stdout, stderr, exit codes, compilation errors. Not a condensed summary. The player cannot hide failures.

## Player Prompt Structure
- **First turn**: Full requirements text + SHA hash (staleness detection). "Implement step-by-step."
- **Subsequent turns**: Coach feedback wrapped with "Address the following specific feedback from the coach" + requirements for re-anchoring.

## Coach Prompt Structure
- Role: "You are G3 in coach mode. Your role is to critique and review implementations against requirements."
- Review criteria baked in: correct implementation, compilation success, missing requirements, specific improvements
- Explicit threshold: ">95% complete" before approving
- Tools: told to use UI tools (webdriver) to test functionality
