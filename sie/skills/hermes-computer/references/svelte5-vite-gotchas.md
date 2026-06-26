# Svelte 5 + Vite Gotchas (HWC Session Learnings)

## Svelte 5 `class:` directive — No `/` in class names

**Symptom:** `vite build` fails with:
```
src/components/BottomPanel.svelte:112:22 Expected token >
class:bg-purple-500/40={resizing}
                      ^
```

**Root cause:** Svelte 5's `class:` directive parser does not handle class names containing `/` (e.g. `bg-purple-500/40`, `text-white/60`). The `/` is interpreted as a delimiter.

**Fix — use template literal instead:**
```svelte
<!-- WRONG -->
<div class:bg-purple-500/40={resizing} ...>

<!-- CORRECT -->
<div class="... {resizing ? 'bg-purple-500/40' : 'bg-transparent'}" ...>
```

This applies to ALL class directives: `class:`, `class:foo`, `class:bar=` — any class with a `/` must be moved into a template literal or `$derived` class string.

## Discord REST API v10 — Requires `User-Agent` header

**Symptom:** `urllib.request.urlopen` returns `HTTP Error 403: Forbidden` when posting to Discord REST API v10, even with a valid bot token.

**Root cause:** Discord's API requires a `User-Agent` header. Without it, requests are rejected.

**Fix — always include `User-Agent`:**
```python
import urllib.request, json

with open('/opt/data/.env') as f:
    content = f.read()
token = content.split('DISCORD_BOT_TOKEN=')[1].split('\n')[0]
channel = content.split('DISCORD_CHANNEL_ID=')[1].split('\n')[0]

msg = "your message here"
req = urllib.request.Request(
    f'https://discord.com/api/v10/channels/{channel}/messages',
    data=json.dumps({'content': msg}).encode(),
    headers={
        'Authorization': f'Bot {token}',
        'Content-Type': 'application/json',
        'User-Agent': 'DiscordBot (hermes-web-computer, 1.0)'
    },
    method='POST'
)
urllib.request.urlopen(req, timeout=15)
```

## Vite Build — `terminal()` Foreground Blocked

**Symptom:** `terminal(command='cd /path/frontend && npx vite build', timeout=X)` returns error about "long-lived server/watch process" even though `vite build` is a one-shot build command.

**Root cause:** Vite internally forks child processes and the hermes terminal tool misdetects it as a long-lived server.

**Fix — use `execute_code` with subprocess instead:**
```python
import subprocess
result = subprocess.run(
    ['npx', 'vite', 'build'],
    cwd='/opt/data/hermes-web-computer/hermes-web-sync/frontend',
    capture_output=True,
    text=True,
    timeout=120
)
print(result.stdout[-3000:])  # last 3000 chars
print("RC:", result.returncode)
```

## Vite Build — dist/ Timestamp Trap

**Symptom:** `vite build` reports success but the dist/ files are stale (timestamps from before your changes).

**Root cause:** Vite build succeeded previously and left old files. A new `vite build` run may not overwrite if there's a permission or caching issue.

**Fix — always check timestamps after build:**
```python
import subprocess
result = subprocess.run(['npx', 'vite', 'build'], ...)
stat_current = subprocess.run(['stat', '-c', '%Y', 'dist/index.html'])
stat_new = # compare file mtime vs component mtime
# If dist is older than component, force: rm -rf dist && npx vite build
```

## Go Build Output — Don't Use `/tmp/hwc-server` in Container

**Symptom:** `go build -o /tmp/hwc-server ./cmd/server/` fails with `permission denied: /tmp/hwc-server`.

**Root cause:** The container environment (running as user `hermes`) cannot write to `/tmp/hwc-server` — that path is owned by root or a different user.

**Fix — use the state dir or `frontend/dist`:**
```bash
# Always write to the state directory
GOPATH=/opt/data/home/go go build -o /opt/data/hermes-web-computer-state/hwc-server ./cmd/server/
```

## Go Tests — HERMES_HWC_ROOT Required

**Symptom:** Go filesystem tests fail with "allowedRoot lazy: path not set".

**Root cause:** `allowedRoot()` is now lazily initialized. Tests MUST set `HERMES_HWC_ROOT` before running.

**Fix — always set HERMES_HWC_ROOT:**
```bash
cd /opt/data/hermes-web-computer/backend
GOPATH=/opt/data/home/go HERMES_HWC_ROOT=/opt/data/hermes-web-computer go test ./... -count=1 -timeout=120s
```