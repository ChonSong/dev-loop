# Vision Troubleshooting Sessions

## Session 1: 2026-06-11 — MiniMax migration (mimo-v2-omni 404)

### Problem

`vision_analyze` returned `404 - No endpoints found for mimo-v2-omni`

### Root Cause Chain

1. `$HERMES_HOME/config.yaml` had:
   ```yaml
   auxiliary:
     vision:
       model: mimo-v2-omni
   ```

2. At gateway startup, `gateway/run.py` bridged this to:
   ```python
   os.environ["AUXILIARY_VISION_MODEL"] = "mimo-v2-omni"
   ```

3. `tools/vision_tools.py:_handle_vision_analyze()` (line 1217):
   ```python
   model = os.getenv("AUXILIARY_VISION_MODEL", "").strip() or None
   return vision_analyze_tool(image_url, full_prompt, model)
   ```

4. This bypasses `load_config()` entirely — the env var is passed as explicit `model` arg to `async_call_llm`, which takes highest priority.

5. `mimo-v2-omni` is a Xiaomi MiMo V2 model, NOT served by OpenRouter. The 404 came from OpenRouter.

### Config File Locations

Hermes has TWO config files:
- **Root:** `$HERMES_HOME/config.yaml` (what `hermes config set` writes to)
- **Home:** `$HOME/.hermes/config.yaml` where `$HOME` may differ from `$HERMES_HOME`

`load_config()` reads `$HERMES_HOME/config.yaml` ONLY. The home config is NOT a fallback.

### The Env Var Trap

The gateway's `config → env` bridge is a one-time operation at startup:

```python
# gateway/run.py lines 1081-1098
for _task_key in _aux_bridged_keys:
    _task_cfg = _auxiliary_cfg.get(_task_key, {})
    _prov = str(_task_cfg.get("provider", "")).strip()
    _model = str(_task_cfg.get("model", "")).strip()
    ...
    if _prov and _prov != "auto":
        os.environ[f"AUXILIARY_{_upper}_PROVIDER"] = _prov
    if _model:
        os.environ[f"AUXILIARY_{_upper}_MODEL"] = _model
```

These env vars persist for the process lifetime. Config file changes after startup are invisible to tools that read directly from `os.environ`.

### Vision Resolution Flow

```
_handle_vision_analyze()
  └─ model = os.getenv("AUXILIARY_VISION_MODEL")      ← env var (highest)
  └─ vision_analyze_tool(image_url, prompt, model)
       └─ async_call_llm(task="vision", model=model)
            └─ _resolve_task_provider_model("vision", model=model)
                 reads config.yaml auxiliary.vision.*        ← config (medium)
                 resolved_model = model or cfg_model
            └─ resolve_vision_provider_client(provider, model)
                 └─ _resolve_task_provider_model("vision", provider, model)  ← called AGAIN
                 └─ _resolve_strict_vision_backend(provider, model)
                      └─ _try_openrouter(model=model)       ← NO api_key passed!
```

Key bug: `_resolve_strict_vision_backend()` for OpenRouter does NOT accept or forward `api_key`. It always falls back to `os.getenv("OPENROUTER_API_KEY")`.

### Test Results

| State | Error | Meaning |
|-------|-------|---------|
| Root config had `mimo-v2-omni` | 404 - No endpoints found | Model not on OpenRouter |
| Root config changed to `google/gemini-2.0-flash-001` via OpenRouter | 401 - Missing Authentication header | OpenRouter key not in gateway env |
| Restored root config with full vision block | Still 404 - mimo-v2-omni | Gateway cached old env var |
| Test with curl using `gpt-4o-mini` + key from `.env` | 402 - Payment Required | OpenRouter has billing issues |

### Fix Applied

1. Updated `$HERMES_HOME/config.yaml`:
   ```yaml
   auxiliary:
     vision:
       provider: minimax
       model: minimax-m3
   ```

2. Root cause: `AUXILIARY_VISION_MODEL` env var in gateway process

3. Remaining blocker: WebUI server process needs restart to pick up new config and re-bridge env vars.

---

## Session 2: 2026-06-12 — OpenRouter free-tier vision (nemotron-nano)

### Goal

Switch vision backend to OpenRouter free tier: `nvidia/nemotron-nano-12b-v2-vl:free`

### Setup

**`config.yaml`:**
```yaml
auxiliary:
  vision:
    provider: openrouter
    model: nvidia/nemotron-nano-12b-v2-vl:free
    api_key: ${OPENROUTER_API_KEY}
```

**`.env`:**
```
OPENROUTER_API_KEY=sk-or-...
AUXILIARY_VISION_MODEL=nvidia/nemotron-nano-12b-v2-vl:free
AUXILIARY_VISION_PROVIDER=openrouter
```

### Symptom Pattern: "Empty ChatCompletion"

When `vision_analyze` failed, it returned:

```
Auxiliary vision: LLM returned invalid response (type=ChatCompletion):
'ChatCompletion(id=None, choices=None, created=None, model=None, object=None,
service_tier=None, system_fingerprint=None,'
```

This is NOT a 401/402 auth error — it's an empty/None ChatCompletion object created
by the OpenAI SDK when the response can't be parsed. The root cause was the
`OPENROUTER_API_KEY` env var not being loaded into the Hermes process environment.

### Diagnosis Chain

```
1. vision_analyze() → "invalid response" (empty ChatCompletion)
   ↓
2. curl test with OpenRouter API directly → SUCCESS (model returns "Purple.")
   ↓
3. OpenAI Python library test → SUCCESS (with sourced .env)
   ↓
4. Check env: $OPENROUTER_API_KEY in shell → empty
   ↓
5. Check .env file has the key → YES (sk-or-v1-...)
   ↓
6. `source ~/.hermes/.env` then OpenAI test → SUCCESS
   ↓
7. Root cause: Hermes process started without .env being fully loaded into
   os.environ — restart needed
```

### Key Facts

- **`nvidia/nemotron-nano-12b-v2-vl:free` is a working free vision model**
  via OpenRouter. It answers visual queries with factual descriptions.
- **`.env` must contain `OPENROUTER_API_KEY=`** — the AUXILIARY_VISION_* vars
  are not sufficient because `_try_openrouter()` reads `os.getenv("OPENROUTER_API_KEY")`.
- **Restart is required** after adding/changing `.env` vars. Hermes reads `.env`
  at process start; `os.getenv()` reflects whatever was loaded then.
- **The `config.yaml` `api_key: ${OPENROUTER_API_KEY}` is a variable reference**
  that Hermes resolves from the process environment. If the var isn't set, the
  reference resolves to empty string and no key is sent.

### Working Config After Restart

```yaml
auxiliary:
  vision:
    provider: openrouter      # triggers _resolve_strict_vision_backend("openrouter")
    model: nvidia/nemotron-nano-12b-v2-vl:free
    api_key: ${OPENROUTER_API_KEY}
```

After WebUI restart: `vision_analyze` returned detailed image descriptions
(successfully described a night bridge scene).

### Pitfall: Env Var Must Be in .env, Not Just Config

The `config.yaml` `api_key: ${OPENROUTER_API_KEY}` is just a config value — it
depends on `os.getenv("OPENROUTER_API_KEY")` resolving. The `.env` file is what
populates `os.environ` at Hermes startup. Without `.env` having the key,
`_try_openrouter()` returns `None, None` and vision falls through.

The `.env` AUXILIARY_VISION_* vars are redundant when the config.yaml has the
same values (they come from the same source), but they're harmless and provide
a fallback for tools that check env vars directly.
