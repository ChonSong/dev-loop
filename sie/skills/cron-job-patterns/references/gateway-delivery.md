# Gateway Delivery Troubleshooting

Cron jobs with `deliver: discord`, `deliver: telegram`, etc. require the Hermes gateway to be running. The gateway is the bridge between the cron scheduler and external chat platforms.

## Symptoms

- `last_delivery_error: "no delivery target resolved for deliver=discord"`
- `last_delivery_error: "no delivery target resolved for deliver=origin"`
- Job `last_status: ok` but no message received — the agent ran fine, output was generated, but delivery failed silently

## Diagnosis

```bash
hermes gateway status
# ✗ Gateway is not running  ← this is the problem
# ✓ Gateway is running (PID: XXXX)  ← healthy
```

## Fix

### In Docker (current setup)

```bash
# Start gateway in background
hermes gateway run   # runs in foreground, use background terminal session
```

`hermes gateway install` prints a message that systemd install doesn't work in Docker — the container runtime IS the service manager.

### Making it persistent

The gateway won't survive container restarts unless it's in the entrypoint:

```dockerfile
# Option 1: entrypoint script
ENTRYPOINT ["/bin/bash", "-c", "hermes gateway run & && exec original_entrypoint"]

# Option 2: supervisord / s6-overlay (preferred for multi-process containers)
```

### On bare metal / VM

```bash
hermes gateway install   # systemd user service
# or
sudo hermes gateway install --system  # system service
```

## Delivery Target Reference

| `deliver` value | Requires gateway? | Notes |
|-----------------|-------------------|-------|
| `local` | No | Writes to cron log only |
| `origin` | Yes (if origin is a platform) | Fails when origin=null (jobs created in container) |
| `discord` | Yes | Needs gateway + Discord bot configured |
| `telegram` | Yes | Needs gateway + Telegram bot configured |
| `all` | Yes | Fans out to every connected home channel |
| `platform:chat_id:thread_id` | Yes | Direct platform targeting |

## Config Check

Discord config in `config.yaml`:
```yaml
discord:
  require_mention: true
  auto_thread: true
  # ... bot token set via environment or config
```

If Discord section is present but gateway isn't running, messages generate but never leave the container.
