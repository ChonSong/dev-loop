# Free OpenRouter Vision Models (tested 2026-06-12)

## How to Discover Free Vision Models

Query the OpenRouter models API to find free models that support image input:

```python
import json, urllib.request

with open('/home/hermeswebui/.hermes/.env') as f:
    env = {}
    for line in f:
        line = line.strip()
        if '=' in line:
            k, v = line.split('=', 1)
            env[k.strip()] = v.strip()

key = env.get('OPENROUTER_API_KEY', '')
url = "https://openrouter.ai/api/v1/models"
req = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}"})
resp = urllib.request.urlopen(req, timeout=10)
data = json.loads(resp.read())

for m in data.get("data", []):
    mid = m.get("id", "")
    pricing = m.get("pricing", {})
    prompt_cost = float(pricing.get("prompt", 1))
    completion_cost = float(pricing.get("completion", 1))
    is_free = prompt_cost == 0 and completion_cost == 0
    
    arch = m.get("architecture", {}) or {}
    input_mod = arch.get("input_modalities", []) or []
    has_vision = "image" in input_mod if isinstance(input_mod, list) else False
    
    if is_free and has_vision:
        print(f"  {mid}")
```

## Confirmed Working Config

```yaml
auxiliary:
  vision:
    provider: openrouter
    model: nvidia/nemotron-nano-12b-v2-vl:free
    api_key: ${OPENROUTER_API_KEY}
```

## Alternative: opencode-go Provider (No API Key Needed)

If OpenRouter is unavailable or the API key doesn't resolve, use `opencode-go` instead:

```yaml
auxiliary:
  vision:
    provider: opencode-go
    model: mimo-v2-omni
    api_key: ''   # opencode-go handles auth internally
    base_url: ''  # uses provider default
```

**Also set in `.env`:**
```
AUXILIARY_VISION_MODEL=mimo-v2-omni
AUXILIARY_VISION_PROVIDER=opencode-go
```

This works because `opencode-go` is an aggregator provider with built-in authentication. Tested working 2026-06-12 with `vision_analyze` on a real resume screenshot — returned detailed, accurate description including person's name and role.

**Important:** The `AUXILIARY_VISION_MODEL` and `AUXILIARY_VISION_PROVIDER` env vars in `.env` take precedence over `config.yaml` settings. Both must be updated, then the gateway restarted for the change to take effect.

## Test Results (2026-06-12)

Tested with a real resume PNG image via OpenRouter chat completions API:

| Model | Result | Quality |
|-------|--------|---------|
| `nvidia/nemotron-nano-12b-v2-vl:free` | ✅ | Best — detailed description, named "Sean Cheong", "Junior Software Engineer" correctly |
| `openrouter/free` | ✅ | Good — auto-routes to available free models |
| `nex-agi/nex-n2-pro:free` | ✅ | Works but shorter responses, inconsistent (sometimes returns None) |
| `google/gemma-4-31b-it:free` | ✅ | Good quality but hits HTTP 429 rate limits |
| `google/gemma-4-26b-a4b-it:free` | ✅ | Same as 31B, rate limited |
| `google/gemini-2.0-flash-001` | ❌ 404 | Not a valid OpenRouter model ID |
| `openai/gpt-4o-mini` | ❌ 402 | Payment Required — needs credits |

## Architecture

Model naming convention on OpenRouter: `provider/model-name:free`

The `:free` suffix indicates the model is available on the free tier. The `openrouter/free` meta-model auto-routes to the best available free model.

## Pitfalls

- Just because a model is "free" on OpenRouter doesn't mean it returns 200 — some free models require prepaid credits for certain modalities.
- Rate limits (429) are common on free tier — Google Gemma models are especially aggressive.
- The `AUXILIARY_VISION_MODEL` env var OVERRIDES the model in config.yaml (set by gateway at startup, refreshed per-turn from .env).
