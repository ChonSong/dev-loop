# g3 Coach/Player Architecture — Comparison with Our Implementation

## g3's Native Approach

g3 runs coach and player in a **single session** with shared context:

```
Session: player implements → coach reviews → player iterates → coach approves
```

Key properties:
- **Shared context**: Coach sees everything the player did — the diff, the reasoning, the false starts
- **Synchronous iteration**: Player doesn't start the next task until coach approves the current one
- **Configurable via config.coach-player.example.toml**: Separate `[providers.anthropic.player]` and `[providers.anthropic.coach]` with different model, max_tokens, temperature
- **Loop bound**: Max turns (default 10), not separation of duties
- **Plan-based**: Player writes a plan with `plan_write` before touching code; coach validates evidence at the end

## Our Approach (Separate Cron Jobs)

Two independent cron jobs, offset by 5m:

```
Player cron (:00): implements → commits → updates checkpoint
Coach cron (:05): reads checkpoint → reads diff → decides APPROVE/FIX/REVERT
```

Key properties:
- **Fresh context**: Coach has NO shared history — evaluates the commit as a stranger would. This is our single biggest advantage over g3's shared-context approach
- **Asynchronous iteration**: Player can start the NEXT task while coach reviews the previous one. Higher throughput, but risk of compounding bad patterns across ticks
- **Model isolation**: Each cron pins its own model. We chose reliability over separation (same flash model for both, since stronger models 429'd)
- **No natural loop bound**: Coach can keep rejecting and the player keeps retrying — mitigated by max consecutive ticks and daily audit

## Trade-offs

| Dimension | g3 (Shared Session) | Our (Separate Cron) |
|-----------|-------------------|---------------------|
| **Context for review** | Full — sees all intermediate steps | Reconstructed from git diff + AGENTS.md |
| **Throughput** | Wait for review before next task | Player advances while coach reviews |
| **Model isolation** | Configurable per-role | Fully independent per-cron |
| **Rubber-stamp risk** | Higher (shared rationalization) | Lower (fresh context, no shared history) |
| **Recovery from bad commit** | Immediate (next iteration) | Coach can revert before next player tick |
| **Complexity** | One process, one config | Two cron jobs, two prompts, two skills |

## Key Design Decisions That Differ

1. **Plan system**: g3 uses `plan_write` with structured items (touches, checks, evidence). We use a mental discipline in the player-agent prompt. If plan quality degrades, consider a formal `plan_write`-like tool or checkpoint field.

2. **Coach feedback loop**: g3 gives the coach's feedback directly to the player in-session. Ours can't — the player already moved on. The coach either fixes or reverts. This makes our FIX path more important.

3. **Bound on iterations**: g3 has max_turns (default 10). Our max_consecutive (2) is a round-robin limit, not a quality cap. A chronically rejected task could bounce between player and coach indefinitely. The daily audit should detect this.

## When Our Approach Works Better

- Projects with stable test suites (coach can verify independently)
- When model quality/cost is asymmetric (coach wants a more expensive model)
- When the user wants continuous progress even during review cycles
- When the coach needs genuine independence from the player's rationalization

## When g3's Approach Works Better

- Tight iteration cycles (fix → review → fix → review in minutes)
- Tasks where intermediate context matters (API design decisions, architecture choices)
- When tests are incomplete and the coach needs to understand intent
