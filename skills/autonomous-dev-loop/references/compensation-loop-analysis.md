# Compensation Loop Analysis — The Meta-Failure Mode

## The Pattern

When an LLM agent produces low-quality output in a dev loop, the instinctive fix is to **add more instructions telling it to be better**. Each added rule:
1. Consumes token budget in the system prompt (preamble)
2. Distracts from actual task context
3. Requires the same model that failed to now follow a longer instruction set
4. Creates a false sense of quality control

The net effect: **more preamble → less context for work → worse output → even more rules.**

```
LLM fails at a task
  → User adds rules to SKILL.md
    → SKILL.md grows (more preamble consumed per tick)
      → Less token budget remaining for actual work
        → LLM cuts corners even more
          → More rules added...
```

This is the **compensation loop** — and it explains why the dev loop hasn't succeeded after 12+ days of iteration.

## Evidence from the Dev Loop

### The Compliance Gate Meta-Cycle (Jun 24-25)

| Time | Action | What It Tried to Fix |
|------|--------|---------------------|
| 23:01 | Created `enforce_qa_gate.py` (keyword scanner) | Coach approving shallow output |
| 23:48 | Wired into cron with post-check | Make verification stick |
| 23:57 | Enhanced with multi-project checks | Coach only checking one project |
| 00:02 | Self-recognition: "this checks words, not truth" | The meta-problem |
| 00:17 | **Reverted all**: "scrap compliance layer" | 3 commits, 2 hours, all deleted |

**The irony**: The system built a **self-referential compliance gate** (checking whether verdicts mention keywords) to fix a **self-referential testing problem** (Player tests checking implementation against itself). The meta-problem exactly mirrors the ground-level problem.

### The Skill Bloat Spiral

The coach-agent SKILL.md went through:
- Original: ~63 lines of principles (after revert)
- Had been: 300 lines of procedures (before revert)
- The 300-line version was itself a trimmed-down version from 81KB
- Player SKILL.md similarly grew from 3.7KB to 350+ lines

Every rule in the current skills traces to a specific flash failure:
- "HTTP 200 is NOT browser QA" → because flash substituted curl for real browser interaction
- "SUBAGENT-FIRST directive" → because flash never delegated
- "Finding nothing is suspicious" → because flash repeatedly claimed zero issues
- "Known-bug regression check" → because advance-to-turn sat stagnant for 6 cycles

**These rules are monuments to the model's failures. But they're written for the same model that failed.** The rules don't change the model's capabilities — they only consume the context budget it needs to do its work.

### The Coach/Player Same-Model Regression

The original design (Phase 2, Jun 14-17) specified:
- Player on flash (fast, cheap, executes)
- Coach on stronger model (deep reasoning, catches flaws)

This was silently abandoned when the stronger model kept erroring (rate limits, 429s, fallbacks). Both now run on `deepseek-v4-flash`. The system's own docs acknowledge:
> "Pitfall: A Coach that never runs is worse than a Coach that shares the Player's model."

The reviewer is **no smarter than the implementer**. The Coach can't catch what the Player missed because they share the same blind spots. This single decision is the root cause of most downstream compensation loop iterations.

## How to Detect You're in a Compensation Loop

| Signal | How to Check | Severity |
|--------|-------------|----------|
| SKILL.md grows >15% per week | Compare line counts in `skill-hygiene-state.json` | 🟡 Warning |
| Rule-to-tool-call ratio increases | Count rules in SKILL.md vs avg tool calls per cron session | 🟡 Warning |
| Same failure pattern appears in Pitfalls AND in a gate | The gate exists because the pitfall was ignored | 🔴 Active loop |
| Preamble > 30% of tool output | Measure character ratio: skill prompt size ÷ avg verdict size | 🔴 Active loop |
| New rules cite specific prior failures | "HTTP 200 is NOT browser QA" = past failure written as a rule | 🔴 Active loop |

## How to Break the Loop

### Structural over documentation

Documentation-level fixes (SKILL.md rules) don't work because they're instructions to the same LLM that failed. **Structural fixes work**:

| Fix | Mechanism | Why It Breaks the Loop |
|-----|-----------|----------------------|
| Use different model for Coach | Model separation in cron job config | Coach can now see what Player couldn't |
| Pre-commit hook banning "Add E2E test for X" | Git hook (structural) | Blocks the self-referential task format at source, regardless of LLM compliance |
| Coach must produce browser artifact filenames | Post-hoc verification step | Makes shallow QA visible — can't claim "visited page" without a screenshot path |
| Auto-escalate after 2 cycles stagnant | Timeout counter in checkpoint reader | Prevents bugs from rotting regardless of Coach attention |
| Master checkpoint freshness validation | Pre-tick check against git log | Prevents staleness masking (the methodology fix was gated on stale data for 2+ hours) |
| Refresh skill from scratch periodically | Delete + rewrite, don't patch | Removes accumulated rule monuments; only the essential survives |

### The Pareto fix

If only one fix could be applied: **restore Coach to a stronger model**. It's the original architectural intent, it addresses the root cause (reviewer blind spots), and it unblocks all downstream compensation loops because the Coach no longer needs rules to do what a capable model does naturally (think before acting, delegate thoroughly, investigate deeply).

## See Also

- `autonomous-dev-loop/coach-model-bottleneck.md` — Specific evidence of v4 flash failure modes in the Coach role, with per-session tool-call analysis
- `agent-ops/enforcement-patterns.md` — The four enforcement patterns, including why pattern 4 (post-cycle verification) was eventually scrapped
- `self-improvement-engine/references/coach-player-loop-failure-detection.md` — Detection patterns for when the loop stalls
