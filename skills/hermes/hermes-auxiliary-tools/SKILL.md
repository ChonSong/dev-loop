---
name: hermes-auxiliary-tools
description: Configure, diagnose, and fix Hermes auxiliary tools (vision, web_extract, compression, approval). Covers the config-to-env bridge, env var overrides, and gateway restart requirements.
trigger: Use when the user asks about Hermes vision, auxiliary tool configuration, why vision_analyze isn't working, or any tool reading from AUXILIARY_* env vars. Also triggers on the "ChatCompletion(id=None" error pattern — see references/vision-troubleshooting.md "Session 2" for the OpenRouter free-tier diagnosis chain.
---

# Hermes Auxiliary Tools Configuration

Hermes uses lightweight "auxiliary" models for side tasks: vision analysis, web extraction, context compression, session search, title generation, and approval. Each has its own config under `auxiliary.<task>` in `config.yaml`.

## Architecture

### Config → Env Bridge (Gateway Startup)

At gateway startup, `gateway/run.py` reads `auxiliary.*` config and bridges non-empty values to `AUXILIARY_<TASK>_*` env vars:

```python
# From gateway/run.py (lines ~1081-1098)
for _task_key in _aux_bridged_keys:   # {"vision", "web_extract", "approval"}
    _task_cfg = _auxiliary_cfg.get(_task_key, {})
    _model = str(_task_cfg.get("model", "")).strip()
    if _model:
        os.environ[f"AUXILIARY_{_upper}_MODEL"] = _model
    # Same for provider, base_url, api_key
```

**These env vars are set ONCE at gateway startup and persist for the process lifetime.** Config file changes do NOT update them.

### Tool-Level Env Var Resolution

The vision tool reads directly from `os.environ`, **bypassing** `load_config()`:

```python
# From tools/vision_tools.py, _handle_vision_analyze():
model = os.getenv("AUXILIARY_VISION_MODEL", "").strip() or None
return vision_analyze_tool(image_url, full_prompt, model)
```

This `model` parameter is passed to `async_call_llm` which resolves model via:
- `model` arg (explicit, from env var) → highest priority
- `cfg_model` (from `load_config()`'s `auxiliary.vision.model`) → fallback
- Auto-detection chain → last resort

### Priority Chain

```
AUXILIARY_VISION_MODEL env var  (highest - set at gateway startup)
               ↓
config.yaml auxiliary.vision.model  (medium - re-reads on each call)
               ↓
Auto-detection: main provider → OpenRouter → Nous  (lowest)
```

## Diagnosing Vision Issues

### 1. Check the env vars in the gateway process

The terminal environment may differ from the gateway's `os.environ`. To determine what the gateway actually has:

- Check what error `vision_analyze` returns — it reveals the model being used
- `404 "No endpoints found for <model>"` means that model doesn't exist on the provider being used
- `401 "Missing Authentication header"` means no API key is being sent
- `402 "Payment Required"` means credits depleted

### 2. Check the config file

```bash
cat $HERMES_HOME/config.yaml
```

Look at `auxiliary.vision.*` — these values were bridged at the LAST gateway startup.

### 3. Check provider health

- OpenRouter: test with `curl -H "Authorization: Bearer $OPENROUTER_API_KEY" https://openrouter.ai/api/v1/chat/completions`
- Check for billing issues (402 responses)
- Check for model availability (404 responses)

## Fixing Issues

### If the config file is correct but vision still fails

The gateway has stale env vars. The only fix is to **restart the WebUI server**:

```bash
# Kill the server.py process — container restart policy handles the restart
# Or use supervisor/s6 to restart
```

After restart, the gateway re-reads config.yaml and bridges the new values.

### Setting up a working vision config

```yaml
# $HERMES_HOME/config.yaml
auxiliary:
  vision:
    provider: <provider>       # openrouter, minimax, nous, etc.
    model: <model-name>        # e.g. google/gemini-2.0-flash-001, minimax-m3
    api_key: ${PROVIDER_API_KEY}  # env var reference
```

**Important:** The `provider` and `model` values should match a provider that:
1. Has a valid API key in `.env`
2. Has credits available
3. Serves the specified model

### Using MiniMax for vision

MiniMax is configured as a custom provider and can serve as the vision backend:

```yaml
auxiliary:
  vision:
    provider: minimax
    model: minimax-m3
```

Ensure `MINIMAX_API_KEY` is set in `~/.hermes/.env`.

### Avoiding the env var override problem

To prevent stale env var overrides:
- Remove `model` and `provider` from `auxiliary.vision` in config.yaml — let auto-detection work
- Or accept that restarting the WebUI is required after config changes

## The WebUI Server Embeds the Gateway

`server.py` starts the Hermes gateway **in-process**. There is no separate gateway process:

```
server.py (Python process)
  └── Hermes gateway (in-process, loaded at startup)
       └── Agent sessions (created per user interaction)
```

This means `hermes gateway restart` from the terminal does NOT affect vision config — it creates a separate gateway process that immediately conflicts.

## Reference Files

- `references/vision-troubleshooting.md` — Debugging transcripts covering MiniMax migration, OpenRouter free-tier (nemotron-nano) setup, "empty ChatCompletion" symptom, and the env-var-not-loaded diagnosis chain
