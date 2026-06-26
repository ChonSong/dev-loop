---
name: multi-provider-llm-backoff
description: Build and debug multi-provider LLM systems with patient backoff retry. Covers NVIDIA NIM discovery, backoff retry bug patterns, and free model cost tracking.
tags:
  - llm
  - provider-management
  - backoff-retry
  - nvidia-nim
  - autonomous-agents
---

# Multi-Provider LLM Backoff Retry System

Skill for building and debugging provider rotation systems that use multiple LLM providers with patient backoff retry.

## Provider API Discovery Checklist

When adding a new provider:
1. Test API key auth with a trivial call (e.g. "hi" with max_tokens=5)
2. Survey available models: GET /v1/models with Authorization header
3. Test latency of candidate models — larger models often have 30-90s cold starts on NVIDIA NIM
4. Check if pricing/context_window fields are returned (NVIDIA returns null for both)
5. If context window unknown, use conservative defaults (e.g. 4K-32K)
6. Add provider to registry with FREE pricing (cost_in=0, cost_out=0) to avoid KeyError in calculate_cost()

## Critical Bug Pattern: Backoff Retry Gave Up Too Fast

**Symptom:** When all models in a tier are in backoff state, the retry loop exits immediately instead of waiting.

**Root cause:** Old pattern used `select_model(exclude_models=tried)` which returns `None` when all models are excluded or in backoff. Code did `if m is None: break` — this exits the loop, then the sweep loop only ran 3 times before giving up.

**Fix:** The correct pattern:
1. When `get_available_models()` returns empty, compute the **earliest backoff expiry** across all models in the tier
2. Sleep until that time (capped at 900s) instead of giving up
3. Use 99 sweeps (not 3) for overnight workloads
4. Use `max_sweeps` config (not hardcoded `3`)

```python
def make_api_call(reg, tier_name, ...):
    while sweep_count < max_sweeps:
        available = get_available_models(reg, tier_name)
        if not available:
            wait_sec = _compute_min_backoff(reg, tier_name, ...)
            time.sleep(wait_sec)  # Wait for earliest backoff to clear
            continue
        # ... try models
```

## Cost Tracking KeyError Bug

**Symptom:** `KeyError: 'cost_in'` in `calculate_cost()` when using free models.

**Cause:** Free models in registry don't have `cost_in`/`cost_out` keys. Direct dict access `m["cost_in"]` fails.

**Fix:** Always use `.get()` with defaults:
```python
cost_in = m.get("cost_in", 0)
cost_out = m.get("cost_out", 0)
```

## Critical Bug Pattern: MiniMax Response Content Is a Typed Block List

**Symptom:** Calling MiniMax API returns HTTP 200 but `result.get("content", [{}])[0].get("text")` always returns empty string — no error, just silent empty responses. All attempts return "LLM returned empty/short response" after the `len(text.strip()) > 50` check fails.

**Root cause:** MiniMax's response `content` field is an **array of typed blocks**, not a dict:

```python
# WRONG — assumes content is a dict (breaks silently)
text = result.get("content", [{}])[0].get("text", "")

# CORRECT — iterate blocks and find the text type
content = result.get("content", [])
text = ""
for block in content:
    if isinstance(block, dict) and block.get("type") == "text":
        text = block.get("text", "")
        break
```

Full MiniMax message structure:
```python
{
  "content": [
    {"type": "thinking", "thinking": "...", "signature": "..."},  # may be present
    {"type": "text", "text": "The actual response text here"}
  ],
  "model": "MiniMax-M2.7",
  "stop_reason": "end_turn"
}
```

**Discovery path:** Tested with simple prompt "Summarize in 3 sentences..." → `thinking` block present, `text` block present. With complex multi-topic prompts (like Hansard summaries), the `thinking` block was 2500+ chars and `text` was empty — the model was using extended thinking on hard prompts and outputting the summary *only* in the thinking block (which was being discarded). Reducing prompt complexity or using `max_tokens: 500` with `temperature: 0.3` produced text output.

**Fix:** Always parse as typed block list, not dict. If `text` block is missing/empty on a thinking model, try simplifying the prompt or reducing complexity to shift work from thinking to generation.

**Affected models:** MiniMax-M2.7 (confirmed). Other thinking-capable models likely similar pattern — always inspect the actual response structure before assuming dict format.

## NVIDIA NIM Specifics (as of 2026-04)

- API base: `https://integrate.api.nvidia.com/v1/chat/completions`
- Auth: `Authorization: Bearer nvapi-...` (env: `CUSTOM_INTEGRATE_API_NVIDIA_COM_API_KEY`)
- OpenAI-compatible format (chat completions)
- Free tier models: `google/gemma-3-12b-it` (fast, ~60s cold start), `nvidia/nemotron-mini-4b-instruct` (tiny, very fast)
- Larger models (70B+): 30-90s cold starts, can time out at 30s
- Context window: NVIDIA returns null — use defaults (4K-196K depending on model)
- RPM limit: effectively unlimited on free tier (set rpm_limit=999)
- Models requiring very fast responses: prefer gemma-3-12b-it over larger models

## Free Model Failure Strategy

Free model failures should NOT trigger provider-level backoff (which would block all models from that provider). Use model-level backoff only:
- Free model fails → model-specific `backoff_until` set → other free models on same provider still usable
- Paid model fails → provider-level backoff (blocks all models from that provider)

## Verified Working Stack (2026-04-27)

- **OpenRouter** (free tier): qwen3-coder, gpt-oss-120b, nemotron-3-super-120b, minimax-m2.5
- **NVIDIA NIM** (free tier): google/gemma-3-12b-it, nvidia/nemotron-mini-4b-instruct, minimaxai/minimax-m2.7, z-ai/glm5
- **Exhausted**: minimax_portal (error 2061), zai (balance=0), openai (quota=0), gemini (quota=0)

- See `references/aph-hansard-monitor.md` for APH-specific scraping notes (Azure WAF workarounds, Hansard XML structure, parsing approach)

## Key Files

- `/home/sean/workspace/scripts/provider_manager.py` — provider management with backoff
- `/home/sean/workspace/memory/provider_registry.json` — registry v4 (as of 2026-04-27)
- `/home/sean/workspace/scripts/overnight_engine.py` — uses provider_manager
