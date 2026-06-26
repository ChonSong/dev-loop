# Browser Automation for LinkedIn

## Playwright vs CDP Decision Tree

1. **Try headless Playwright first** (faster, no display needed)
2. **If LinkedIn shows interstitial/login page after cookies are loaded** → switch to CDP
3. **CDP = Chrome remote debugging on port 9222** → controls real browser → no fingerprint mismatch

## Anti-Detection Patterns That DON'T Work

- Loading cookies from real Chrome into Playwright headless Chromium → DETECTED (redirect to login)
- Using `Object.defineProperty(navigator, 'webdriver', ...)` → NOT ENOUGH
- Changing user agent → NOT ENOUGH
- Using `--disable-blink-features=AutomationControlled` → NOT ENOUGH

LinkedIn checks canvas fingerprint, WebGL renderer, extension list, and other signals that differ between real Chrome and Chromium. The only reliable approach is controlling the real browser.

## CDP Setup (One-Time)

```bash
# On host — restart Chrome with debugging
pkill -f "google-chrome" 2>/dev/null; sleep 2
google-chrome --remote-debugging-port=9222 \
  --user-data-dir=/home/sean/.config/google-chrome/Default \
  --no-first-run --no-default-browser-check &
sleep 5
curl -s http://localhost:9222/json/version  # verify
```

Once running, any script can connect to `localhost:9222` and control all tabs.

## Session File Location

- `/home/sean/n8n-data/linkedin-session.json` — saved cookies (legacy, use CDP now)
- `/home/sean/.config/google-chrome/Default/` — real Chrome profile (source of truth for CDP)

## Key Technical Notes

- `websocket-client` Python package required on host (`pip3 install websocket-client`)
- Playwright on host also installed (`pip3 install playwright && python3 -m playwright install chromium`)
- Tablet/inline Python in SSH breaks with f-strings containing nested quotes — always write scripts to files first
- `scp` to `/workspace/` on host denied (different UID lands) — use `/tmp/` instead
