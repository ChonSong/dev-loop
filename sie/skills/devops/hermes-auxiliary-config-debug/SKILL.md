---
name: hermes-auxiliary-config-debug
description: Debug and fix Hermes auxiliary config (vision, compression, session_search) when changes don't take effect. Covers the multi-layer config resolution chain from config.yaml through load_config caching, gateway config bridge, .env reload, and env var override. Use when an auxiliary vision/model/provider change is ignored or the running session doesn't pick it up.
version: 1.0.0
author: Agent
---

# Hermes Auxiliary Config Debug

When you change `auxiliary.vision.*` or other auxiliary config in `config.yaml` but the session ignores it, the problem is almost always one of four caching layers.

## The Four-Layer Config Chain

```
config.yaml (on disk)
    |
    v
load_config() -- cached on (mtime_ns, file_size)
    |
    v
gateway config bridge (run.py:1065-1098) -- sets AUXILIARY_* env vars, ONE-TIME at startup
    |
    v
_handle_vision_analyze (vision_tools.py:1217) -- reads AUXILIARY_VISION_MODEL from env, bypasses config
```

## Layer 1: load_config() Caching

`_load_config_impl()` in `config.py` caches on `(st_mtime_ns, st_size)`. Changes to the file invalidate the cache. But:

- **Deleted file = cache cleared, fallback to DEFAULT_CONFIG only** -- no fallback to a secondary config file. Restore immediately.
- **New/changed file = fresh cache** -- after stat detects new mtime+size, the cache is rebuilt with `_deep_merge(DEFAULT_CONFIG, new_file)`.
- **The running Python process keeps the cache in `_LOAD_CONFIG_CACHE`** -- a global dict at module level. It persists for the process lifetime.
- **If load_config() reads the wrong file**, check `get_hermes_home()`:

```python
get_config_path() -> get_hermes_home() / "config.yaml"
```

`HERMES_HOME` env var controls which config file is read. In the WebUI container: `HERMES_HOME=/home/hermeswebui/.hermes` reads `/home/hermeswebui/.hermes/config.yaml`. This is the ROOT config.

**There is NO merge between root and home configs.** The config file at `$HERMES_HOME/config.yaml` is the single source. `/home/hermeswebui/.hermes/home/.hermes/config.yaml` is NOT read by `load_config()` -- it is a separate config for a different purpose.

## Layer 2: Gateway Config Bridge (THE MOST COMMON TRAP)

At startup, `gateway/run.py` (lines 1065-1098) reads `auxiliary.*` from config.yaml and sets `AUXILIARY_*` env vars:

```python
os.environ[f"AUXILIARY_{_upper}_PROVIDER"] = _prov
os.environ[f"AUXILIARY_{_upper}_MODEL"] = _model
```

**This is ONE-TIME.** These env vars persist for the gateway process lifetime. Changing config.yaml after startup does NOT update them. Even `hermes gateway restart` may not help if the gateway runs inside the WebUI server process.

**Diagnosis:** Check what the gateway actually has:
```bash
env | grep AUXILIARY
```
If `AUXILIARY_VISION_MODEL` shows a different value than your config.yaml, the gateway cached the old value at startup.

**Fix:** 
1. Set the correct values in `.env` file too (see Layer 3)
2. Restart the WebUI/gateway process to force rebridge

## Layer 3: .env Reload

The gateway calls `_reload_runtime_env_preserving_config_authority()` per-turn. This reloads `~/.hermes/.env` into `os.environ` with `override=True`.

If you put the correct `AUXILIARY_VISION_MODEL` and `AUXILIARY_VISION_PROVIDER` in `.env`, they will be picked up on the next turn WITHOUT a restart:

```
echo "AUXILIARY_VISION_MODEL=minimax-m3" >> ~/.hermes/.env
echo "AUXILIARY_VISION_PROVIDER=minimax" >> ~/.hermes/.env
```

But this only works if the gateway`s .env reload runs before the next vision call. The reload happens per-turn in the agent loop.

## Layer 4: vision_tools.py Env Override (Final Boss)

`_handle_vision_analyze` at `tools/vision_tools.py:1217` reads:

```python
model = os.getenv("AUXILIARY_VISION_MODEL", "").strip() or None
```

This env var overrides EVERYTHING -- including `load_config()` results. It is passed as the `model` argument to `vision_analyze_tool` then `async_call_llm(model=...)`. In `_resolve_task_provider_model`, `model or cfg_model` means the explicit model arg (from env var) takes precedence.

**Even if config.yaml has the correct model, the stale env var wins.**

## The Quick Fix

When a vision config change is not taking effect:

```bash
# 1. Verify what is actually being used
env | grep AUXILIARY_VISION

# 2. Update BOTH config.yaml AND .env with the correct values
hermes config set auxiliary.vision.model minimax-m3
echo "AUXILIARY_VISION_MODEL=minimax-m3" >> ~/.hermes/.env
echo "AUXILIARY_VISION_PROVIDER=minimax" >> ~/.hermes/.env

# 3. Restart the WebUI/gateway (most reliable)
# Within the WebUI container: /app/venv/bin/hermes gateway restart
# Or kill and restart the server.py process
```

OR, for a non-restart fix if the `.env` vars will be picked up:
- Add the correct AUXILIARY_VISION_* to `.env` (the per-turn reload picks them up)
- BUT this won't work if the gateway process started before the `.env` was updated and the env var was already set at startup via the config bridge (Layer 2 takes precedence over Layer 3)

**Correction:** The per-turn `.env` reload with `override=True` DOES override stale AUXILIARY_* env vars set at startup. So adding the correct values to `.env` should fix it within 1-2 turns. If it doesn't, the gateway needs a full restart.

## Auxiliary Provider Resolution

The `resolve_provider_client()` function in `agent/auxiliary_client.py` resolves providers for auxiliary tasks. It supports:

| Provider type | How it resolves | Example |
|---|---|---|
| Built-in | Provider-specific branch | openrouter, nous, openai-codex, xai-oauth |
| Custom endpoint | explicit_base_url + explicit_api_key | provider: custom |
| Named custom_providers | From config.yaml custom_providers list | minimax, openrouter |
| PROVIDER_REGISTRY | From hermes_cli.auth.PROVIDER_REGISTRY | API-key providers |

**ProviderProfile providers (opencode-go, opencode-zen):** These use `register_provider()` from plugins. Historically thought to be unsupported for auxiliary tasks, but `opencode-go` + `mimo-v2-omni` has been verified WORKING for vision (tested 2026-06-12, session e9c8fd7de8ef, `vision_analyze` returned success). The key is:
- `api_key` must be empty (`''`) — opencode-go handles auth internally
- `base_url` must be empty (`''`) — uses opencode-go's default URL
- The model must have vision capabilities (e.g. `mimo-v2-omni`)
- The env var override via `.env` must match (see Layer 3 below)

## Vision-Specific Path

For `task="vision"`, `async_call_llm` calls `resolve_vision_provider_client()`:

1. `_resolve_task_provider_model("vision")` reads `auxiliary.vision.*` from config
2. `resolve_vision_provider_client()` creates the OpenAI/Anthropic client
3. If the provider returns `None`, falls back to auto-detection (main provider then OpenRouter then Nous)
4. OpenRouter 402 = no credits. MiniMax 403 = opencode.ai proxy dead (but MiniMax Anthropic endpoint works directly if key is valid)

**Working configuration for OpenRouter free vision models:**

OpenRouter has free-tier vision-capable models that work without credits. Tested working:

```yaml
auxiliary:
  vision:
    provider: openrouter
    model: nvidia/nemotron-nano-12b-v2-vl:free
    api_key: ${OPENROUTER_API_KEY}
```

Or use the meta-model that auto-routes to available free models:
```yaml
auxiliary:
  vision:
    provider: openrouter
    model: openrouter/free
    api_key: ${OPENROUTER_API_KEY}
```

**Confirmed working free vision models on OpenRouter (tested 2026-06-12):**

| Model | Vision | Notes |
|-------|--------|-------|
| `nvidia/nemotron-nano-12b-v2-vl:free` | ✅ | Best balance of accuracy + speed. Described resume accurately. |
| `openrouter/free` | ✅ | Meta-model, auto-routes to free models. Works. |
| `nex-agi/nex-n2-pro:free` | ✅ | Works but shorter/simpler responses. |
| `google/gemma-4-31b-it:free` | ✅ | Vision-capable but hits 429 rate limits easily. |
| `google/gemma-4-26b-a4b-it:free` | ✅ | Vision-capable but hits 429 rate limits easily. |

**Does NOT work (despite being "free" label):**
- `google/gemini-2.0-flash-001` — 404, not on OpenRouter
- Any model returning HTTP 402 = insufficient OpenRouter credits (even with free tier, some models need prepaid credits)

**Note on `api_key` and the named custom provider trap:**

The `api_key` override in `auxiliary.vision` is forwarded to `resolve_provider_client` as `explicit_api_key` but the named custom provider branch (`_get_named_custom_provider`) does NOT use `explicit_api_key` — it reads the key from the `custom_providers` config entry. The override ONLY works for the `custom` (direct endpoint) provider path (lines 3554-3570 in auxiliary_client.py).

For OpenRouter, the `_try_openrouter` function also ignores `explicit_api_key` when called from `_resolve_strict_vision_backend` — it falls back to `os.getenv("OPENROUTER_API_KEY")`. So the key must be in the environment, not just the config.

## Debugging Technique: Direct API Test

When a provider/model combination fails, test it directly from terminal:

```python
import json, urllib.request

with open('/home/hermeswebui/.hermes/.env') as f:
    env = {}
    for line in f:
        line = line.strip()
        if '=' in line:
            k, v = line.split('=', 1)
            env[k.strip()] = v.strip()

key = env.get('OPENROUTER_API_KEY', '')  # or OPENCODE_GO_API_KEY
url = "https://openrouter.ai/api/v1/chat/completions"
payload = {
    "model": "minimax-m3",
    "messages": [{"role": "user", "content": "Say hello"}],
    "max_tokens": 10
}
req = urllib.request.Request(
    url,
    data=json.dumps(payload).encode(),
    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
)
try:
    resp = urllib.request.urlopen(req, timeout=15)
    print(json.loads(resp.read()))
except urllib.error.HTTPError as e:
    print(f"HTTP {e.code}: {e.read().decode()[:300]}")
```

**Error code meanings:**
- 401 = auth failure (wrong key or format)
- 402 = payment required (no credits)
- 403 = forbidden (key rejected, account issue)
- 404 = model not found (wrong name or endpoint)
- 1010 (opencode.ai specific) = account/credits issue on proxy
