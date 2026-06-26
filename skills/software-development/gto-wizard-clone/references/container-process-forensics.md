# Container Process Forensics — Killing Zombie Processes

The Hermes container lacks `kill`, `fuser`, `lsof`, `ps`, and `ss`. Process management requires Python `/proc` traversal.

## Finding and Killing Zombie Processes

```python
import os

for pid_str in os.listdir('/proc'):
    if not pid_str.isdigit():
        continue
    try:
        cmd = open(f'/proc/{pid_str}/cmdline', 'rb').read().decode('utf-8', 'ignore')
        # Check for target processes
        if 'uvicorn' in cmd and '8000' in cmd:
            os.kill(int(pid_str), 9)
            print(f'Killed uvicorn on 8000: PID={pid_str}')
        if 'next start' in cmd and '3000' in cmd:
            os.kill(int(pid_str), 9)
            print(f'Killed next on 3000: PID={pid_str}')
    except (FileNotFoundError, ProcessLookupError, PermissionError):
        pass
```

## Checking Port Binding

Without `lsof`/`ss`, use Python sockets or `/proc/net/tcp`:

```python
import socket
s = socket.socket()
s.settimeout(2)
result = s.connect_ex(('0.0.0.0', 8000))
s.close()
print('BUSY' if result == 0 else 'FREE')
```

Port numbers in `/proc/net/tcp` are hex:
- 8000 = 0x1F40
- 8555 = 0x216B
- 3000 = 0x0BB8

## Common Zombie Sources

| Process | Command | Ports |
|---------|---------|-------|
| uvicorn | `Python apps.api.main:app` | 8000, 8001, 8002 |
| next-server | `node .../next/dist/bin/next start` | 3000, 3001, 8555 |
| next dev | `node .../next dev` | 3000 |

## Port Fallback Strategy

Default ports that commonly get stuck in TIME_WAIT:
- 8000 → fallback to 8002
- 3000 → fallback to 3001 or 8555
- 3001 → fallback to 3002

## Background Process Check

List tracked background processes:
```python
# process list (Hermes tool) — shows sessions created by terminal(background=true)
# But zombie processes created outside this mechanism won't appear
```

## PATH Issues for Background Processes

Background processes (`terminal(background=true)`) do NOT inherit the agent's PATH.
Always use absolute binary paths:

- Node: `/home/hermeswebui/.hermes/home/.local/bin/node`
- Python venv: `/app/venv/bin/python3`
- uvicorn: `/app/venv/bin/uvicorn`
- Next.js: `/workspace/gto-wizard-clone/node_modules/next/dist/bin/next`
- npm: `/home/hermeswebui/.hermes/home/.local/bin/npm`
- Playwright: `/workspace/gto-wizard-clone/node_modules/.bin/playwright`

When a background process exits immediately with no output, PATH is almost always the cause.
