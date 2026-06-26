# Playwright Screenshot Techniques

## Host-side Screenshot (Primary Method)

On EndeavourOS host with Chromium installed, use `npx playwright screenshot` from the project directory:

```bash
cd /home/sean/.hermes/hermes-web-computer
npx playwright screenshot --browser chromium http://127.0.0.1:3005 /tmp/hwc5.png
```

This avoids module path issues that plague `node -e "require('playwright')"` invocations.

**Requirements:**
- Playwright installed in project's `node_modules/`
- Chromium downloaded: `npx playwright install chromium`
- Target URL must be reachable from host

## Node Inline (Fails Without Correct Module Path)

```bash
node -e "const{chromium}=require('./frontend/node_modules/playwright');..."
```

This fails when:
- `playwright` not in project root `node_modules/`
- Wrong version of playwright is found first in NODE_PATH

Use `npx playwright screenshot` instead — it handles the module resolution.

## Playwright Browser Cache Version Mismatch

**Symptom:**
```
browserType.launch: Executable doesn't exist at /home/sean/.cache/ms-playwright/chromium_headless_shell-1223/chrome-headless-shell-linux64/chrome-headless-shell
```

**Cause:** `npx playwright install` (newer version) expects `chromium_headless_shell-1223`, but cache has `chromium-1217` and `chromium_headless_shell-1217`.

**Fix:** Use the existing cached version with `npx playwright screenshot` (it auto-detects the correct browser). Or run `npx playwright install` from the project directory with the matching playwright version.

Check what's cached:
```bash
ls ~/.cache/ms-playwright/
# Output: chromium-1217  chromium_headless_shell-1217  ffmpeg-1011
```

The `npx playwright screenshot` command uses whatever browser is present and works — it doesn't need the headless shell variant.

## Port Discovery: HWC vs agent-os

Before taking screenshots, verify which backend is on which port:

```bash
# HWC Go backend (correct target for screenshots)
curl -s http://localhost:3005/ | grep title
# → <title>Hermes Web Computer</title>

# agent-os (old, wrong for HWC screenshots)
curl -s http://localhost:3113/ | grep title
# → empty or different content
```

**Always curl the title first** — blind screenshot of `:3113` captures the wrong app.

## Copying Screenshots to Container

```bash
# From container:
scp -i /home/hermeswebui/.hermes/container_key \
    sean@172.19.0.1:/tmp/hwc5.png \
    /workspace/hwc5.png
```

## Screenshot for Vision Analysis

Use absolute paths. The platform renders `MEDIA:/workspace/hwc5.png` inline for vision analysis:

```bash
scp sean@172.19.0.1:/tmp/hwc5.png /workspace/hwc5.png
# Then in chat: MEDIA:/workspace/hwc5.png
```

## Common Screenshot Scenarios

| Scenario | Command |
|----------|---------|
| Single screenshot | `npx playwright screenshot --browser chromium http://127.0.0.1:3005 /tmp/s.png` |
| Full page | `npx playwright screenshot --browser chromium --full-page http://127.0.0.1:3005 /tmp/s.png` |
| Specific element | Use `page.locator('.selector').screenshot({path: '/tmp/s.png'})` in a script |
| Wait for JS | `npx playwright screenshot ...` — playwright waits for `load` event by default; add `--wait-for-timeout=3000` for SPAs |