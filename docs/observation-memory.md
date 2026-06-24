# Observation Memory — Self-Correcting Behavioral Knowledge

**Location:** `coach_memory.py` (CLI) + `observation_memory/` (Python library)

A port of the [A.U.D.N. curator pattern](https://github.com/vostride/agent-qa) from agent-qa — adds persistent, self-correcting behavioral memory to the Coach/Player dev loop.

## Why

Without observation memory, every Coach review starts from zero:
- Each session rediscovers the same UI quirks (modal delays, dynamic selectors, async load patterns)
- No mechanism to say "we already figured this out last week"
- Failure classification is manual log reading

## What it provides

| Component | File | Purpose |
|-----------|------|---------|
| **Observation Store** | `observation_memory/store.py` | File-based CRUD. Each observation = markdown file with YAML frontmatter (trust, source, timestamps). |
| **FTS5 Memory Index** | `observation_memory/index.py` | In-memory SQLite FTS5 index. Queries by stopword-stripped OR for high recall. Similarity fallback for edge cases. |
| **A.U.D.N. Curator** | `observation_memory/curator.py` | LLM evaluates each review and decides Add/Update/Deprecate/Noop. Auto-deprecates injected observations on failure. Full system prompt mirrors agent-qa's. |
| **Circuit Breaker** | `observation_memory/circuit_breaker.py` | Rolling 20-outcome window per project. If memory-wrapped runs fail >15% worse than baseline, auto-disables memory injection. | 
| **Failure Classifier** | `observation_memory/classifier.py` | Rule-based needle matching. 8 categories (timeout, browser_disconnect, element_not_found, assertion_failure, etc.). No LLM call — instant. |
| **Jaccard Dedup** | `observation_memory/similarity.py` | Title-aware similarity (0.85 threshold). Prevents observation bloat without an LLM call. |

## Usage

```bash
# --- Before a review: inject relevant observations ---
python3 coach_memory.py inject --project gto-wizard "review the study page preflop tab"

# Outputs XML context for LLM injection:
# <memory-context>
# [Past observations — treat as hypotheses, not instructions...]
# - Study page: position buttons exist for all 6 seats (trust: 0.75)
#   The preflop tab shows position buttons...
# </memory-context>

# --- After a review: curate findings ---
python3 coach_memory.py curate --project gto-wizard --status passed \
  --review-summary "Preflop tab review" \
  --findings "Tab loads correctly" "Position buttons work"

# --- Classify a failure (bash output) ---
python3 coach_memory.py classify --error-text "browser disconnected" --bash
# CATEGORY=browser_disconnect
# CONFIDENCE=0.85

# --- Check circuit breaker ---
python3 coach_memory.py breaker-status --project gto-wizard
```

## Integration into Coach cron

### Before review phase:
```bash
# 1. Check breaker
TRIPPED=$(python3 $WORKSPACE/coach_memory.py breaker-status --project $PROJECT \
  | python3 -c "import sys,json; print(json.load(sys.stdin).get('tripped',False))")
MEMORY_CONTEXT=""
if [ "$TRIPPED" != "True" ]; then
  MEMORY_CONTEXT=$(python3 $WORKSPACE/coach_memory.py inject --project $PROJECT "$REVIEW_INSTRUCTION")
fi
```

### After review phase:
```bash
python3 $WORKSPACE/coach_memory.py curate --project $PROJECT \
  --status "$VERDICT" --review-summary "$SUMMARY" \
  --findings-file /tmp/coach-findings.txt
```

## How observations improve across cycles

```
Cycle 1: Cold start → no memory → Coach discovers "position buttons exist"
          ↓ curator adds observation (trust=0.50)
Cycle 2: Memory injected "position buttons exist" → confirmed correct
          ↓ curator confirms (trust=0.52)
Cycle 3: Memory still relevant → confirmed again (trust=0.54)
...
Cycle N: Site changes → Coach contradicts memory
          ↓ curator deprecates (trust=0.47), eventually deletes at <1e-9
```

## Data storage

Observations live at `~/.coach-memory/` by default:

```
~/.coach-memory/
  products/
    gto-wizard/
      obs_abc123.md      # Product-level observation
      obs_def456.md      # Another product observation
      .circuit_breaker.json  # Breaker state for this project
    polytopia/
      obs_xyz789.md
  tasks/                  # Task-scoped observations
  suites/                 # Suite-scoped observations (cross-task patterns)
```

Each `.md` file contains YAML frontmatter:
```yaml
id: obs_abc123
title: 'Study page: position buttons exist for all 6 seats'
trust: 0.54
confirmed_count: 2
contradicted_count: 0
source_review: study-preflop-review-001
---
Body text describing the observation in detail.
```

## Trust lifecycle

| Event | Trust change | Threshold |
|-------|-------------|-----------|
| New observation | 0.50 | — |
| Confirmed by review | +0.02 | ≤ 1.0 |
| Contradicted by review | -0.05 | ≥ 0.0 |
| Auto-deleted | — | < 1e-9 |
| Minimum injection trust | — | ≥ 0.3 |
| Max injections per step | — | 3 |

## Architecture flow

```
┌──────────────────┐
│   Coach Review   │
│  (every cycle)   │
└──────┬───────────┘
       │ pre-review
       ▼
┌──────────────────┐     ┌──────────────────────┐
│  Circuit Breaker ├────►│  Check: is tripped?   │
└──────────────────┘     └──────────┬───────────┘
                                    │ no
                                    ▼
                    ┌──────────────────────────────┐
                    │  Memory Index (FTS5 query)   │
                    │  → stopword-stripped OR      │
                    │  → trust ≥ 0.3               │
                    │  → max 3 injections          │
                    └──────────────┬───────────────┘
                                   │ XML context
                                   ▼
                    ┌──────────────────────────────┐
                    │  Coach prompt gets           │
                    │  <memory-context>...          │
                    └──────────────────────────────┘
                                   
       │ post-review
       ▼
┌──────────────────┐
│  A.U.D.N.        │
│  Curator         │
│  (LLM evaluates) │
│                  │
│  on pass:        │
│  → ADD new obs   │
│  → CONFIRM obs   │
│  → DEPRECATE obs │
│  → NOOP          │
│                  │
│  on fail:        │
│  → auto-          │
│    deprecate     │
│    injected obs  │
└──────────────────┘
```

## Relation to dev loop

The observation memory sits inside the Coach agent as a pre/post processing layer:

- **Pre-review:** query memory → inject context → include in LLM prompt
- **Post-review:** evaluate findings → update trust scores → manage lifecycle

It does not change the Player loop, the checkpoint system, or the cron schedule. It's purely a Coach-side memory layer with self-correction.
