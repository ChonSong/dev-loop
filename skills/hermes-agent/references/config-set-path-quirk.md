# `hermes config set` Path Quirk

## Symptom

`hermes config set` reports success ("✓ Set ...") but the actual config file Hermes reads is untouched.

## Root Cause

`hermes config set` resolves its target relative to the **real** `~` (`Path.home()`), while Hermes reads config relative to `$HOME`. When `$HOME` is overridden (e.g. `$HOME=/home/hermeswebui/.hermes/home`), these point to different files.

| Owner | Path |
|-------|------|
| Written by `hermes config set` | `/home/hermeswebui/.hermes/config.yaml` (the real home) |
| Read by running Hermes | `/home/hermeswebui/.hermes/home/.hermes/config.yaml` (via `$HOME/.hermes/`) |

## Diagnosis

```bash
echo "HOME=$HOME"
hermes config path
ls -la "$HOME/.hermes/config.yaml"
grep -A 3 '^model:' "$HOME/.hermes/config.yaml"
```

## Fix

Edit `$HOME/.hermes/config.yaml` directly with `patch`, then `/reset`.

## Prevention

After `hermes config set`, verify the value in `$HOME/.hermes/config.yaml`. If it didn't stick, `$HOME` is overridden — patch directly instead.
