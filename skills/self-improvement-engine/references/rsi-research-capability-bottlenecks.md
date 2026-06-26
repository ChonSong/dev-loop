# RSI Research: Capability Bottlenecks (Not Safety)

Research conducted 2026-06-22 during RSI study. Source: "Recursive Self-Improvement" by Emergent Garden (https://www.youtube.com/watch?v=t7_ZXgfJVG8).

## What Actually Limits Autonomous Self-Improvement

These are the REAL bottlenecks — verified against Hermes architecture:

### 1. Cron Job Reliability
Coach/Player cron jobs fail silently when their model is rate-limited. The single highest-impact fix: pin cron jobs to a provider with reliable rate limits. `opencode-go/deepseek-v4-flash` works. `openrouter/owl-alpha` hits HTTP 429 within 2-3 runs.

**Fix pattern:** When a cron shows `last_status: error` with HTTP 429, update the job's model:
```
cronjob(action='update', job_id='...', model={'provider': 'opencode-go', 'model': 'deepseek-v4-flash'})
```

### 2. Web Tool Fallback Chain
`web_search` and `web_extract` fail when Firecrawl billing is exhausted. These tools share a payment-dependent backend and fail together. `vision_analyze` goes through a separate auxiliary vision provider and is NOT affected by Firecrawl billing.

**Fallback order when web tools fail:**
1. Direct curl to known API endpoints (Wikipedia REST, arxiv API, DuckDuckGo HTML)
2. Google search via curl with browser user-agent (rate-limited but works)
3. YouTube via scraping initial data from page source

**Known working sources (Firecrawl-independent):**
- Wikipedia: `curl -sL "https://en.wikipedia.org/api/rest_v1/page/summary/<topic>"`
- Arxiv: `curl -sL "http://export.arxiv.org/api/query?search_query=..."`
- Anthropic blog: `curl -sL "https://www.anthropic.com/institute/<article>"` + HTML stripping

### 3. Vision vs Web Independence
`vision_analyze` uses the auxiliary vision provider (config.yaml `auxiliary.vision.provider`), typically `openrouter/google/gemini-2.5-flash`. This is on a completely separate billing/credential path from Firecrawl. When web tools fail, vision likely still works.

### 4. Self-Improvement Pipeline Fragility
The self-improvement engine (SIE) is a Python script pipeline that's fragile in three ways:
- **Deleted scripts:** If `self_improvement.py`, `learnings_scanner.py`, or `skill_author.py` get deleted, the SIE silently dies. Recovery: `git show <commit> -- scripts/<file>` from the archived hermes-sync repo.
- **Regex drift:** The parser expects specific markdown formatting in `.learnings/` files. If the bold-colon format changes (`**Field:**` vs `**Field**:`), the parser silently returns defaults (medium priority, backend area, recurrence=1).
- **Timezone bugs:** Naive datetime comparisons crash with `offset-naive and offset-aware` errors.

### 5. Feedback Loop Failure Mode
The Player-Coach loop stalls when any component fails:
- Coach 429 → no reviews → no new tasks → `current_task: "tbd"` → loop dead
- Player 429 → no commits → Coach has nothing to review → loop dead
- Fix: pin both to the same reliable model. Model separation is less important than the loop staying alive.

## What DOES Work
- **Vision comparison for visual fidelity:** Load reference via `vision_analyze`, load live via `browser_vision`, diff, write specific tasks with measurable criteria. This is the fastest path to visual parity.
- **Direct task injection:** When backlog is exhausted (`current_task: tbd`), adding tasks directly to AGENTS.md and updating the checkpoint unblocks the Player on the next tick.
- **Self-seeding learnings:** Writing real observed failures into `.learnings/LEARNINGS.md` feeds the SIE without waiting for automated detection.

## References
- Video: https://www.youtube.com/watch?v=t7_ZXgfJVG8
- SAHOO paper: https://arxiv.org/abs/2603.06333
- STOP paper: https://arxiv.org/abs/2310.02304
- Gödel Agent: https://arxiv.org/abs/2410.04444
- Darwin-Gödel Machine: https://arxiv.org/abs/2505.22954
- Anthropic RSI article: https://www.anthropic.com/institute/recursive-self-improvement
- Yampolskiy RSI survey: https://arxiv.org/abs/1502.06512
