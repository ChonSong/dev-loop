# Skill Selector Calibration Notes

## Current State (2026-05-25)

| Metric | Value |
|--------|-------|
| Total skills | 1,441 |
| Summarized | 453 (32%) |
| Coverage | 32% |
| Batch success | ~6/73 (most JSON parse errors) |

## Parsing Journey (what was tried)

1. **VoltAgent**: `## [name](url)\ndescription` regex — matched 0. Fixed by using line-by-line bullet parsing (`- **[name](url)** - desc`).
2. **0xNyk**: Same regex — matched 0. Problem: README has mixed formats including `**[beta]** [name](url) by [author]**` which breaks simple patterns.
3. **Unified fix**: Split on last ` - ` to separate name_block from description, extract first markdown link from name_block. Works for all three formats (VoltAgent bold, 0xNyk/bold with maturity, 0xNyk/plain).

## LLM Summary Model Evolution

| Model | Result |
|-------|--------|
| `openrouter/auto` → `google/gemini-2.5-flash-lite` | 402 insufficient credits |
| `openrouter/free` → `openai/gpt-oss-20b:free` | Returns `None` content |
| `poolside/laguna-xs.2:free` | Works but truncates JSON mid-response |
| `baidu/cobuddy:free` | Returns `None` content, only reasoning |

Current recommendation: use `poolside/laguna-xs.2:free` but with JSON retry logic.

## Score Calibration

- `svelte-development` scores 7.3 on "debug svelte component" (correct top match)
- `docker-patterns` scores high on "build docker and deploy to kubernetes" (correct)
- `hermes-docker-workflow` also fires on docker-related queries (expected — both relevant)
- Remote skills (voltagent) with `anthropics/` prefix score on AI tool keywords
- Many voltagent skills have `**kwargs` descriptions that are actually table-of-contents listings, not descriptions — scoring on these is unreliable

## Known Gaps

- **453/1,441 summaries** — remaining 983 skills score on raw description only
- **JSON parse errors on poolside** — model cuts off mid-JSON, causing parse failures. Retry loop would help but not yet implemented.
- **voltagent skills lack rich metadata** — only description text, no category/tags. Many descriptions are TOC-style ("kwargs: name, description, ...").
- **Duplicate skill names across sources** — first-found wins in dedup. Local skills always win over remote.