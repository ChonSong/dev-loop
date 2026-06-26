---
name: multi-provider-api-calls
description: Call LLM APIs from multiple providers.
category: devops
tags: [api, llm, providers, minimax, openrouter, gemini, opencode]
source: local
is_imported: true
---

# multi-provider-api-calls

Call LLM APIs from multiple providers.

**Category:** devops
**Source:** local

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
- Account balance check: `GET https://openrouter.ai/api/v1/auth/key` with `Authorization: Bearer *** — returns `usage`, `usage_daily`, `is_free_tier`
- **HTTP 402 (Insufficient credits)**: Account-level credit exhaustion. NOT the same as HTTP 429 (rate limit). 402 means "no money in account" — retrying won't help. Fix: add credits at https://openrouter.ai/settings/credits. Check balance via the auth/key endpoint above.

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
| HTTP 400 (generic) | Fix request format, don't retry |
| HTTP 400: `"No models provided"` | NOT a request-format bug — the configured provider is rejecting the model parameter. Most commonly caused by missing or expired API key for the configured provider, or a provider that doesn't recognize the model name. Trace: `config.yaml → model.provider → model.default → provider base_url and api_key → curl test`. This is a config/credential fix, NOT a retry pattern. Multiple unrelated cron jobs hitting this simultaneously is a strong signal for a shared misconfiguration. |

## Tiered Model Selection

Map work to the cheapest sufficient tier:

| Tier | Models | Use for |
|------|--------|---------|
| **premium** | deepseek-v4-flash, claude-sonnet-4 | Code generation, complex reasoning |
| **standard** | gpt-4o-mini, qwen3-coder-30b, glm-4.5-air | Planning, testing, documentation |
| **budget** | minimax-m2.5:free, nemotron-3-super:free | Ideation, ingestion, non-critical batch |

**Critical pitfall**: Free models are frequently rate-limited upstream (HTTP 429). They are unreliable for any time-sensitive work. Always have paid fallback.

## Provider Rotation Pattern

### Model-level vs Provider-level Backoff

**Free model failures must NOT set provider-level backoff.** OpenRouter hosts both free and paid models. If a free model gets 429'd, setting provider-level backoff locks out ALL paid models on OpenRouter too.

### Exclude Tried Models

When retrying, track which models have been attempted and exclude them from selection. Otherwise the system re-selects the same failed model.

## Hermes Credential System (Docker)

When running hermes in a Docker container, API keys are intentionally sealed:

- `~/.hermes/.env` is protected — `read_file()`, `cat`, `patch()` all blocked.
- `config.yaml` custom_providers use `${ENV_VAR}` references resolved at runtime.
- The gateway process (under tini) injects keys; they're not readable from `/proc/<pid>/environ`.
- `auth.json` only has `credential_pool` for explicitly added providers, not main model keys.

**To use LLM from an external script**: either import from hermes agent code (`sys.path.insert(0, '/usr/local/lib/hermes-agent/')`) or route through the gateway via a messaging platform. There is no supported way to extract keys from outside the hermes process.

**MiniMax specifics** (via Hermes Docker): provider=`opencode-go`, base_url=`https://api.minimax.io/anthropic`, auth header=`x-api-key` (NOT `Authorization: Bearer`), response format is Anthropic `{"content": [{"text": "..."}]}` not OpenAI.

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