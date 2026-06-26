# Credential Pool Architecture in nesquena/hermes-webui

## Two Different WebUI Projects

There are **two separate WebUI projects** for Hermes Agent:

| Project | Repo | Stack | Credential Pool Support |
|---------|------|-------|------------------------|
| **Hermes WebUI** | `nesquena/hermes-webui` (14.6k ⭐) | Python + vanilla JS, no build step | Partial — exists but limited |
| **Hermes Studio** | `EKKOLearnAI/hermes-studio` (8k ⭐) | Vue 3 + TypeScript + Koa | Different codebase |

**This document covers `nesquena/hermes-webui`** (the Python one). The user may refer to either — clarify which one they mean.

## How Credential Pools Work

### Backend (`api/providers.py`)

- `_ACCOUNT_USAGE_PROVIDERS` (line ~80): frozenset of providers that get full pool probing — currently `{"openai-codex", "anthropic"}`
- `_codex_pool_snapshot()` (line ~513): builds pool status from probed credential data — status, windows, plans, exhaustion
- `_fetch_codex_account_usage_from_pool()` (line ~607): probes each credential against the provider's usage API
- `get_provider_quota()` (line ~1623): main quota endpoint — routes to either account-usage probing (for Codex/Anthropic) or OpenRouter key check, returns "unsupported" for all others

### Data Flow

```
auth.json → credential_pool.<provider> → entries[] → probe each → _codex_pool_snapshot → /api/provider/quota
```

### Frontend (`static/panels.js`)

- `_buildProviderQuotaPoolBreakdown()` (line ~7073): renders per-credential pool UI with status badges, windows, reset timers
- `_providerQuotaPoolShouldDefaultOpen()` (line ~7063): auto-opens pool section if ≤3 credentials
- The pool UI is already fully built — it renders inside the Providers panel quota card

## The Gap

Pool data is only fetched for `_ACCOUNT_USAGE_PROVIDERS`. For other providers (opencode-zen, opencode-go, etc.), `get_provider_quota()` returns `{"status": "unsupported"}` and the pool UI never renders, even though `auth.json` has the credential data.

## auth.json Credential Pool Structure

```json
{
  "credential_pool": {
    "opencode-zen": [
      {
        "id": "...",
        "label": "OPENCODE_ZEN_API_KEY",
        "auth_type": "api_key",
        "priority": 0,
        "source": "env:OPENCODE_ZEN_API_KEY",
        "last_status": "exhausted",
        "last_status_at": 1781692522.77,
        "last_error_code": 429,
        "last_error_reason": "rate_limited",
        "last_error_reset_at": 1782613748.77,
        "request_count": 0,
        "secret_fingerprint": "sha256:..."
      }
    ]
  }
}
```

## Key Code Locations

| File | Line | Purpose |
|------|------|---------|
| `api/providers.py` | ~80 | `_ACCOUNT_USAGE_PROVIDERS` — controls which providers get pool probing |
| `api/providers.py` | ~513 | `_codex_pool_snapshot()` — builds pool status from probed data |
| `api/providers.py` | ~607 | `_fetch_codex_account_usage_from_pool()` — probes each credential |
| `api/providers.py` | ~1623 | `get_provider_quota()` — main quota endpoint |
| `api/config.py` | ~2851 | `_get_auth_store_path()` — reads auth.json |
| `api/config.py` | ~2931 | `_AUTH_FINGERPRINT_VOLATILE_KEYS` — fields that churn on rotation |
| `static/panels.js` | ~7063 | `_providerQuotaPoolShouldDefaultOpen()` — auto-open logic |
| `static/panels.js` | ~7073 | `_buildProviderQuotaPoolBreakdown()` — renders pool UI |

## Working with Credential Pool Code

- Don't confuse `credential_pool` (in auth.json, holds API key credentials) with `probe_worker_pool` (async workers for probing provider usage)
- When adding pool support for new providers, the simplest path is a generic local-only snapshot (read from auth.json) rather than probing each credential against a usage API
- `config.yaml` stores `credential_pool_strategies` — rotation strategy per provider (`fill_first`, `round_robin`, `least_used`, `random`)
- The Hermes agent writes pool status fields (`last_status`, `last_error_code`, `last_error_reset_at`) to auth.json on each request — the WebUI can read these without probing

## GitHub Auth for PR Creation

- `gh` binary on this system is NOT the GitHub CLI — it's a custom browser-opener tool
- `GITHUB_PAT` or `GITHUB_TOKEN` in `~/.hermes/.env` may not have issue/PR creation scopes
- Fine-grained PATs need `Pull requests: Write` on the target repo; classic tokens with `repo` scope work for everything
- If API returns 403 (not 401), the token is valid but scoped too narrowly
- Fallback: give the user the direct PR creation URL: `https://github.com/nesquena/hermes-webui/compare/master...ChonSong:branch-name`
