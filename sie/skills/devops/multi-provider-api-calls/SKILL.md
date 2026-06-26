---
name: multi-provider-api-calls
description: Call multiple LLM provider APIs (MiniMax, OpenRouter, OpenAI, Gemini) with correct auth headers, endpoints, and response parsing. Includes error handling for Token Plan limits.
version: 1.0
tags: [api, llm, providers, minimax, openrouter, gemini]
---

# Multi-Provider LLM API Calls

When making direct API calls to multiple LLM providers, each has different auth headers, endpoints, and response formats.

## Provider Details

### MiniMax (Anthropic-compatible)

- **Endpoint**: `https://api.minimax.io/anthropic/v1/messages`
- **Auth**: `x-api-key` header (NOT `Authorization: Bearer`)
- **Required header**: `anthropic-version: 2023-06-01`
- **Request body**: `{ model, messages, max_tokens, temperature }`
- **Response format**: `{ content: [{ text: "..." }], usage: { input_tokens, output_tokens } }`
- **Pitfalls**:
  - The `/anthropic/v1/chat/completions` endpoint returns 404 — must use `/anthropic/v1/messages`
  - Token Plan keys (prefix `sk-cp-`) return error 2061 "your current token plan not support model" when plan doesn't include the model
  - Error 2061 is NOT a transient error — backoff won't help, need to switch providers
  - Both `/v1/chat/completions` (native) and `/anthropic/v1/messages` (compatible) exist but only the latter works with Hermes config

### OpenRouter

- **Endpoint**: `https://openrouter.ai/api/v1/chat/completions`
- **Auth**: `Authorization: Bearer <key>`
- **Optional headers**: `HTTP-Referer`, `X-Title`
- **Request body**: `{ model: "openai/gpt-4o-mini", messages, max_tokens }`
- **Response format**: OpenAI-compatible `{ choices: [{ message: { content } }], usage: { total_tokens } }`
- **Pitfalls**: Model names include provider prefix (e.g. `openai/gpt-4o-mini`, `anthropic/claude-sonnet-4`)
- Free models (suffix `:free`) are frequently rate-limited upstream with 429 — they are unreliable, always have paid fallback
- When a free model fails with 429, set model-level backoff only, NOT provider-level (paid models on same provider remain available)
- Account balance check: `GET https://openrouter.ai/api/v1/auth/key` with `Authorization: Bearer <key>` — returns `usage`, `usage_daily`, `is_free_tier`

### OpenAI

- **Endpoint**: `https://api.openai.com/v1/chat/completions`
- **Auth**: `Authorization: Bearer <key>`
- **Request body**: `{ model: "gpt-4o-mini", messages, max_tokens }`
- **Response format**: `{ choices: [{ message: { content } }], usage: { total_tokens } }`

### Google Gemini

- **Endpoint**: `https://generativelanguage.googleapis.com/v1beta/models/<model>:generateContent`
- **Auth**: `x-goog-api-key` header (NOT `?key=` query param when sending POST JSON body)
- **Request body**: `{ contents: [{ role, parts: [{ text }] }], generationConfig: { maxOutputTokens, temperature } }`
  - Role mapping: `assistant` → `model`, `user` → `user`
- **Response format**: `{ candidates: [{ content: { parts: [{ text }] } }], usageMetadata: { totalTokenCount } }`
- **Pitfalls**:
  - Using `?key=` in URL with POST JSON body causes the body to be interpreted as a query param — use header instead
  - Free tier has strict daily quotas that exhaust quickly
  - Role must be `model` not `assistant` for assistant messages

## Error Handling Strategy

| Error | Action |
|-------|--------|
| HTTP 429 (rate limit) | Backoff 60s |
| HTTP 500 + error 2061 (Token Plan) | Backoff 2h+ — won't self-resolve |
| HTTP 5xx (server error) | Backoff 120s, try next provider |
| HTTP 400 | Fix request format, don't retry |

## Tiered Model Selection

Map work to the cheapest sufficient tier:

| Tier | Models (OpenRouter) | Use for |
|------|---------------------|---------|
| **premium** | glm-5 ($0.60), deepseek-v4-flash ($0.14), qwen3-coder ($0.22) | Code generation, complex reasoning |
| **standard** | gpt-4o-mini ($0.15), qwen3-coder-30b ($0.07), glm-4.5-air ($0.13) | Planning, testing, documentation |
| **budget** | qwen3-coder:free, minimax-m2.5:free, nemotron-3-super:free | Ideation, ingestion, non-critical batch |

**Critical pitfall**: OpenRouter free models are frequently rate-limited upstream (HTTP 429). They are unreliable for any time-sensitive work. Always have paid fallback.

## Provider Rotation Pattern

### Model-level vs Provider-level Backoff

This is the most important lesson: **free model failures must NOT set provider-level backoff**. OpenRouter hosts both free and paid models. If a free model gets 429'd, setting provider-level backoff locks out ALL paid models on OpenRouter too.

```python
# WRONG: free model failure poisons the entire provider
health["backoff_until"] = backoff_dt  # blocks ALL openrouter models

# RIGHT: set model-level backoff for free models only
if is_free_model and consecutive_failures < threshold:
    set_model_backoff(reg, model_id, backoff_dt)  # only blocks that model
else:
    health["backoff_until"] = backoff_dt  # paid model failure = provider backoff
```

### Exclude Tried Models

When retrying, track which models have been attempted and exclude them from selection. Otherwise the system re-selects the same failed model.

```python
tried_models = set()
for attempt in range(max_retries):
    model = select_model(reg, tier, exclude_models=tried_models)
    tried_models.add(model["id"])
```

### Full Rotation Algorithm

1. Select model from requested tier, sorted by (consecutive_failures, cost) — healthiest cheapest first
2. Exclude previously-tried models
3. If tier exhausted, drop to lower tier (premium→standard→budget)
4. If all tiers exhausted, report failure
5. Track per-call: provider, model, tokens, latency, cost, success/failure
6. Daily budget reset at midnight local time

Recommended order: `openrouter` (primary, $2/day budget) → `openai` (fallback) → `minimax` (last, Token Plan issues)

## Implementation Reference

The full working implementation lives at:
- **Registry config**: `~/workspace/memory/provider_registry.json` — tiers, models, pricing, health state
- **Provider manager**: `~/workspace/scripts/provider_manager.py` — selection, health, backoff, logging
- **Event log**: `~/workspace/memory/provider_events.log` — JSONL structured log of all API calls

## Response Parsing (unified)

```python
if "content" in result and isinstance(result["content"], list):
    # Anthropic/MiniMax format
    text = result["content"][0].get("text", "")
elif "candidates" in result:
    # Gemini format
    text = result["candidates"][0]["content"]["parts"][0]["text"]
elif "choices" in result:
    # OpenAI/OpenRouter format
    text = result["choices"][0]["message"]["content"]
```
