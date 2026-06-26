# Vision Config Resolution Code References

Exact code locations and paths discovered during June 2026 investigation.

## Key Files

| File | Purpose |
|---|---|
| `$HERMES_HOME/config.yaml` | Root config (single source for load_config()) |
| `gateway/run.py` (lines 1065-1098) | Gateway config bridge - sets AUXILIARY_* env vars at startup |
| `tools/vision_tools.py` (line 1217) | _handle_vision_analyze reads AUXILIARY_VISION_MODEL from env |
| `hermes_cli/config.py` (lines 5342-5430) | _load_config_impl caching logic |
| `agent/auxiliary_client.py` (lines 4127-4320) | resolve_vision_provider_client |
| `agent/auxiliary_client.py` (lines 4673-4765) | _resolve_task_provider_model |
| `agent/auxiliary_client.py` (lines 3336-3490) | resolve_provider_client |
| `agent/auxiliary_client.py` (lines 1544-1570) | _try_openrouter |
| `agent/auxiliary_client.py` (lines 4075-4095) | _resolve_strict_vision_backend |
| `agent/auxiliary_client.py` (lines 5570-5610) | async_call_llm |
| `./env` | API keys (loaded per-turn by _reload_runtime_env_preserving_config_authority) |
| `providers/__init__.py` (line 53) | register_provider for ProviderProfile entries |
| `plugins/model-providers/opencode-zen/__init__.py` | opencode-go ProviderProfile definition |

## Key Functions

### _resolve_task_provider_model (auxiliary_client.py:4673)

Priority order:
1. Explicit args (provider/model/base_url/api_key passed in) - always win
2. Config file (auxiliary.{task}.provider/model/base_url/api_key)
3. "auto" (full auto-detection chain)

When `base_url` is set without `provider`:
```python
if base_url:
    return "custom", resolved_model, base_url, api_key, resolved_api_mode
```

When `provider` is set without `base_url`:
```python
if provider:
    return provider, resolved_model, base_url, api_key, resolved_api_mode
```

When config has both `base_url` and `provider` set AND `provider != "auto"`:
```python
if cfg_base_url and cfg_provider and cfg_provider != "auto":
    # Returns provider NOT api_key - hardcoded None
    return cfg_provider, resolved_model, cfg_base_url, None, resolved_api_mode
```

### resolve_provider_client supported providers:

1. "openrouter" -> _try_openrouter(explicit_api_key)
2. "nous" -> _try_nous(vision=...)
3. "openai-codex" / "codex" -> _build_codex_client
4. "xai-oauth" -> _build_xai_oauth_aux_client
5. "custom" -> explicit base_url + api_key, or OPENAI_BASE_URL env vars
6. Named custom_providers (from config.yaml providers/custom_providers list)
7. PROVIDER_REGISTRY (from hermes_cli.auth)
8. ProviderProfile providers (opencode-go, opencode-zen) — historically thought unsupported, but `opencode-go` + `mimo-v2-omni` has been VERIFIED WORKING for vision (session e9c8fd7de8ef, 2026-06-12). Works with empty api_key and base_url — provider handles auth internally.

### load_config caching (config.py:5342)

```python
st = config_path.stat()
cache_key = (st.st_mtime_ns, st.st_size)
if cached and cached[:2] == cache_key:
    return deepcopy(cached[2])
```

Cache keyed on `str(config_path)`. File deletion = `cache_key = None` = rebuild from DEFAULT_CONFIG only (no fallback).

## Gateway vs Terminal Env Difference

The gateway process and terminal processes may have DIFFERENT environment variables even though both run in the same container:

- Gateway sets AUXILIARY_* env vars via `os.environ[f"AUXILIARY_{key}"] = value` at startup
- Terminal inherits the gateway's env, but if terminal uses `local` backend, it reads from shell init files NOT the gateway's Python os.environ
- The `env | grep AUXILIARY` command in terminal may show DIFFERENT values than what the gateway's os.environ has

## The .env file vs Gateway Bridge Priority

At startup (run.py lines 1061-1098):
1. `load_hermes_dotenv()` loads .env into os.environ
2. Config bridge reads config.yaml and writes AUXILIARY_* env vars, OVERRIDING .env values

Per-turn (_reload_runtime_env_preserving_config_authority):
1. `load_hermes_dotenv(override=True)` reloads .env, OVERRIDING stale env values

So .env wins per-turn, but config bridge wins at startup.
