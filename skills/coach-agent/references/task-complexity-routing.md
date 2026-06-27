# Task Complexity → Model Routing

## How it works

The Coach reads the AGENTS.md task BEFORE review and classifies it by complexity.
The complexity score determines which model tier is used for the review.

## Model Tiers (all confirmed ACTIVE on OR key)

| Tier | Model | SWE-bench | Cost | When to use |
|------|-------|-----------|------|-------------|
| **S-Tier** | minimax-m2.5 | 81.2%† | $0.000013 | Complex reviews, multi-file bugs, architecture |
| **A-Tier** | minimax-m3 | 80.5% | $0.000028 | Strong coding + QA reviews |
| **A-Tier** | deepseek-v4-pro | 80.6% | $0.000014 | Strong coding, cheaper than minimax |
| **B-Tier** | deepseek-v4-flash | 79% | $0 | Simple reviews, CSS/visual, documentation |
| **B-Tier** | deepseek-v3.2 | ~78% | $0.000002 | Newest deepseek, good value |
| **C-Tier** | qwen3.7-plus | high | $0.00036 | Good balance, moderate cost |
| **D-Tier** | kimi-k2.7-code | ~75% | $0.000037 | Coding specialist |
| **Context**  | glm-5.2 | ~80% | 1M ctx | Large repo understanding, sparse fixes |
| **Free fallback** | big-pickle | ~75% | $0 | When OR quota exhausted |

† Lingxi v2.0 optimal backbone — first agent to exceed 80% on SWE-bench Verified

## Task Complexity Classification

The Coach classifies the task BEFORE selecting a model.

### Complexity = Sum of:

**Files category:**
- 1 file changed: +0
- 2-3 files: +1
- 4-7 files: +2
- 8+ files: +3

**Task domain:**
- Visual/CSS/styling: +0
- Documentation/configuration: +0
- Frontend logic (state, components): +1
- API/backend logic: +2
- Canvas/game logic (Polytopia): +3
- Architecture/refactoring: +2

**Task type:**
- `chore` (cleanup, lint): +0
- `fix` (bug): +1
- `feat` (new): +1
- `refactor` (restructure): +2
- `perf` (optimization): +2

**Novelty (check DevKnowledge):**
- Similar past fix found (pattern exists): +0
- No similar past fix (novel): +1
- No DevKnowledge available: +1

**Risk:**
- Low risk (isolated change): +0
- Medium risk (touches main component): +1
- High risk (touches core, shared state): +2

### Routing Threshold

| Score | Tier | Model |
|-------|------|-------|
| 0-2 | Simple | deepseek-v4-flash (B) or big-pickle (free) |
| 3-5 | Medium | deepseek-v4-pro (A) or qwen3.7-plus (C) |
| 6-8 | Complex | minimax-m3 or minimax-m2.5 (S/A) |
| 9+ | Critical | minimax-m2.5 (S) |

## Routing Heuristic (Prompt Injection for Coach)

The Coach processes this logic at Step 0 (before verification):

```
Before reviewing, classify the current task using the complexity rubric
in references/task-complexity-routing.md.

1. Read the task from AGENTS.md
2. Check DevKnowledge: any similar past fixes?
3. Assess: how many files changed? What domain? What risk?

4. Pick model:
   Score 0-2 → deepseek-v4-flash (79%, free, handles >90% of visual/CSS tasks)
   Score 3-5 → deepseek-v4-pro (80.6%, strong for logic bugs and features)
   Score 6+  → minimax-m2.5 (81.2%, Lingxi v2.0 backbone for complex reviews)

5. Route the review through the selected model.
```

## Why This Works

| Task Type | % of Tasks | Best Model | Why |
|-----------|-----------|-----------|-----|
| CSS/visual polish | ~40% | v4-flash | These are simple — font sizes, colors, layout. 79% SWE-bench is overkill. |
| Frontend component fix | ~30% | v4-pro | Need to understand React state + interactions. 80.6% is right. |
| API/backend logic | ~15% | minimax-m3 | Solver route changes, preflop ranges, game logic. 80.5%. |
| Architecture/refactor | ~10% | minimax-m2.5 | Multi-file restructures. 81.2% Lingxi-verified. |
| Game logic (Polytopia) | ~5% | minimax-m2.5 | Complex canvas state + AI logic. Highest tier. |

The cheap models handle ~70% of tasks. Only ~30% need S/A tier.
Estimated monthly cost: essentially free (all OR free tier).

## Model Selection Reference

From the Coach's perspective, the model selection command is:

```bash
# Route based on task complexity score
python3 /home/sc/repos/autonomous-dev-system/skills/coach-agent/scripts/task-complexity-router.py \
  --task "$(cat AGENTS.md | grep current_task)" \
  --project "gto-wizard-clone"
```

This script:
1. Parses the task from AGENTS.md
2. Queries DevKnowledge for similar past fixes
3. Computes complexity score
4. Returns the recommended model name
5. The Coach uses this model for the review
