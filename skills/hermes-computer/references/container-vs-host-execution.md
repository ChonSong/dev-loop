# Container vs Host Execution: Browser and Build Tools

> Discovered 2026-05-23 during visual QA audit of hermes-web-computer. The container sandbox lacks Chromium system libraries — all browser automation must run on the EndeavourOS host.

## The Core Problem

The `hermes` Docker container (Ubuntu-based, sandboxed) cannot run:
- **Chromium headless** — missing `libglib-2.0.so.0`, `libnss3`, `libX11`, `libatk-1.0`, `libatk-bridge-2.0`
- **Playwright browser automation** — Chromium binary exists but crashes on launch due to missing libs
- **`yay` package manager** — not installed in container
- **`sudo` with password** — not available; can't install system packages

The **EndeavourOS host** (Arch-based) can run everything, but:
- Needs Chromium installed via `yay -S chromium` (requires user password)
- Playwright must be run via SSH from container with agent forwarding

## What Runs Where

| Task | Container | Host | Notes |
|------|-----------|------|-------|
| Go build (`go build`) | ✅ | ✅ | Available in container |
| Go tests (`go test`) | ✅ | ✅ | Available in container |
| Node/npm | ✅ | ✅ | Via `n` or direct install |
| Vite build (`npm run build`) | ✅ | ✅ | Svelte 5 build works |
| Playwright tests (headless) | ❌ | ✅ | Needs Chromium + deps |
| Screenshot capture | ❌ | ✅ | Needs browser |
| Vision analysis (`browser_vision`) | ❌ | ✅ | Needs Chromium + network |
| `yay` package install | ❌ | ✅ | Arch-specific |

## The SSH Agent Forwarding Pattern

The container has SSH agent forwarding set up. Use it to run commands on the host:

```bash
# Run Playwright tests on host, copy results back
ssh -i /home/hermeswebui/.hermes/container_key \
    -o ForwardAgent=yes \
    sean@172.19.0.1 \
    "cd ~/hermes-web-computer && npx playwright test e2e/tests/visual/"

# Run a script on host and retrieve artifacts
scp -i /home/hermeswebui/.hermes/container_key \
    scripts/visual-qa.sh \
    sean@172.19.0.1:/tmp/visual-qa.sh

ssh -i /home/hermeswebui/.hermes/container_key \
    -o ForwardAgent=yes \
    sean@172.19.0.1 \
    "bash /tmp/visual-qa.sh && ls /tmp/hwc-qa/"
```

## Key Host Paths

| Resource | Path |
|----------|------|
| hermes-web-computer repo | `/home/sean/.hermes/hermes-web-computer` |
| Backend binary | `/tmp/hwc-server` (built from local source) |
| Screenshot output | `/tmp/hwc-qa/` |
| Chromium binary | `/usr/bin/chromium` (when installed) |
| SSH key (container→host) | `/home/hermeswebui/.hermes/container_key` |

## Layered Verification (No Browser = No Problem)

When Chromium isn't available on the host yet, use layered verification:

### Layer 1: DOM Inspection (free, unlimited)
```javascript
// In browser console
document.querySelectorAll('[class*="glass"], [class*="backdrop-blur"]').length
getComputedStyle(document.querySelector('.bg-\\[\\#12121a\\]')).backgroundColor
document.querySelectorAll('button').length
```

### Layer 2: HTTP Response Audit (free, unlimited)
```bash
# Verify correct dist is served
curl -s http://localhost:3113/ | grep -o 'src="/assets/index-[^"]*\.js"'
curl -s http://localhost:3113/assets/*.css | grep -c 'backdrop-blur-xl\|bg-\[\#12121a\]'
```

### Layer 3: Source Audit (fast, no runtime needed)
```bash
# Check glassmorphism classes in source files
grep -rn 'backdrop-blur-xl\|bg-\[\#12121a\]\|border-white/10' \
  /home/hermeswebui/.hermes/hermes-web-computer/frontend/src/components/
```

### Layer 4: Playwright Screenshots (after Chromium installed)
```bash
# On EndeavourOS host
cd ~/hermes-web-computer
npx playwright test e2e/tests/visual/ --update-snapshots
```

## Installing Chromium on EndeavourOS

```bash
# On EndeavourOS host (requires user password)
yay -S chromium

# Verify
chromium --version
```

If user isn't in sudoers and `yay` needs password, the container can't install it. Plan around this — the `scripts/visual-qa.sh` checks for Chromium and exits gracefully if not found.

## Visual QA for hermes-web-computer

See `hermes-computer` skill §"Container Browser Execution Model" and `references/visual-qa-pipeline.md` for the full workflow.

## General Rule

**Build in container, browser on host.** The container is great for Go builds, source changes, and testing. The host is great for anything that needs a real browser or system libraries. Always know which environment you're operating in.