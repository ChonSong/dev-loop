# Cron Job Provider Diagnosis — "No models provided" Pipeline

## When to use

Multiple cron jobs (3+) failing simultaneously with the same error:
```
RuntimeError: Error code: 400 - {'error': {'message': 'No models provided', 'code': 400}}
```

This error is a **strong signal of shared provider misconfiguration**, not individual job bugs.

## Diagnostic Pipeline

### Step 1: List all jobs and identify failure pattern

```bash
hermes cron list
```

Look for jobs with identical error messages. If 5+ unrelated jobs (System Monitor, Autonomy Digest, APH Hansard, etc.) all show the same error, the root cause is in the **model/provider config**, not the jobs themselves.

### Step 2: Check the model config

Read `~/.hermes/config.yaml` and find the `model:` section:

```yaml
model:
  base_url: <endpoint>
  default: <provider>/<model>
  provider: <provider>
```

Three values matter:
- `provider` — which provider driver Hermes uses (e.g., `opencode-go`, `openai`, `minimax`)
- `default` — the model name passed in API calls
- `base_url` — may override the provider's default endpoint

### Step 3: Check provider auth

Verify the API key for the configured provider exists in the environment:

```bash
env | grep -i "<PROVIDER_NAME>_API_KEY"
```

**Common failure modes:**
| Provider key missing → | Error from API |
|---|---|
| `OPENCODE_API_KEY` | `400 "No models provided"` |
| `MINIMAX_API_KEY` | `401 invalid_api_key` |
| `OPENROUTER_API_KEY` | `401` or `429` |

### Step 4: Verify with curl

```bash
curl -s -w "\nHTTP %{http_code}" <endpoint>/v1/models \
  -H "Authorization: Bearer <key>" | tail -5
```

Or use Python if curl is unavailable:

```python
import urllib.request
req = urllib.request.Request(
    "https://<provider-api>/v1/models",
    headers={"Authorization": "Bearer <key>"}
)
try:
    with urllib.request.urlopen(req, timeout=5) as r:
        print(f"Connected: HTTP {r.status}")
except Exception as e:
    print(f"Failed: {e}")
```

### Step 5: Check for hybrid config

If `model.provider` and `model.base_url` point to different providers (e.g., provider=opencode-go but base_url=https://api.minimax.io/anthropic), the config is in a hybrid state. The `base_url` may be an override for the model's chat completions endpoint while the provider driver handles embedding/other operations differently.

### Step 6: Fix

- **Missing key**: Add the key to the container environment or `.env`
- **Expired key**: Rotate or switch to a working provider
- **Wrong provider**: Change `model.provider` in config.yaml to a configured provider (minimax, openrouter, openai)
- **Model name**: Verify the model name is valid with the provider (e.g., `opencode-go/deepseek-v4-flash` may need the provider prefix or not)

## Key Insight

The `"No models provided"` error is **misleading** — it doesn't mean the cron prompt provided no model. It means the API call to the configured provider endpoint was rejected, and the provider returned this confusing error instead of a proper 401/403. The fix is in credential or provider configuration, not in the job prompt.
