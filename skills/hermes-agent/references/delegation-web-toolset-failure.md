# Delegation Web Toolset Failure Pattern

## Symptom

`delegate_task(toolsets=["web"])` spawns a subagent that reports "completed" but produces zero results. The subagent's `web_search` and `web_extract` calls return null/empty.

## Root Cause

The `web` toolset in this environment does **not** expose `web_search` or `web_extract` as callable tools. The subagent inherits the parent's tool limitations. When the subagent attempts `web_search`, the tool simply doesn't exist in its context — it gets null back, not an error.

## Diagnosis

1. Check if `web_search` is available: `grep -r '"web_search"' /opt/hermes/toolsets.py`
2. If absent, the `web` toolset only provides browser-based tools
3. The subagent's summary will say "completed" with `api_calls: 1` but results array will be empty

## Workarounds

| Approach | When to use |
|----------|-------------|
| **Use `browser` toolset** instead of `web` | When browser automation is available |
| **Use `terminal` + `curl`** | When direct HTTP access works (test first) |
| **Fall back to local knowledge** | When external access times out |
| **Skip delegation, do it inline** | When parent has better tool access |

## Key Rule

**Never assume subagents have better network access than the parent.** In containerized environments, subagents inherit the same network constraints.

## Session Evidence

- 2026-06-07: Research task delegated with `["web"]` → subagent's `web_search` returned null → 0 results despite "completed" status
- ArXiv API (`export.arxiv.org`) timed out at 20s from container
- DuckDuckGo HTML scraping returned empty (anti-bot)
