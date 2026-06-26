# Empty `model:` Field in `config.yaml`

## Symptom

Cron jobs fail with:
```
RuntimeError: Error code: 400 - {'error': {'message': 'No models provided', 'code': 400}, 'user_id': 'user_...'}
```

`hermes config show` displays:
```
◆ Model
  Model:        (empty)
```

## Diagnostic

1. Read the config file: `cat /opt/data/config.yaml`
2. Check if top-level `model:` and/or `provider:` keys are missing or empty
3. Compare with `hermes config show` output — if `Model:` is blank, the primary model is not configured

## Root Cause

The config file has no primary model set. Example:
```yaml
auxiliary:
  vision:
    model: mimo-v2-omni
    provider: opencode-go
```
...but no top-level `model:` key. The `auxiliary.vision` model only applies to vision tasks, not to the main agent loop.

When cron jobs fire, they inherit the empty `model:` from config, or if the job was created without an explicit `model`/`provider`, the scheduler passes null — and the provider API (opencode-go, minimax, etc.) returns 400: "No models provided".

## Fix

```bash
hermes config set model <model-name>
hermes config set provider <provider-name>
```

Example for OpenCode-Go:
```bash
hermes config set model deepseek-v4-flash
hermes config set provider opencode-go
```

After setting, verify:
```bash
hermes config show | grep "Model:"
# Should show: Model: deepseek-v4-flash
```

Then `/reset` in interactive sessions. Cron jobs pick up the change on their next scheduled run.

## Related

- This is different from the cron scheduler's "400 - Model not exist" error (scheduler rejects the job before execution). This "No models provided" error comes from the provider API after the job starts running.
- `hermes-agent` skill → Troubleshooting → Model/provider issues
- `autonomous-cron-pipeline` skill → Pitfall 18 (set model/provider explicitly on cron jobs)
