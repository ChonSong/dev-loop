# Tandem Shared Browser + SEEK Job Research

## Architecture

Two separate components:

1. **Tandem Browser (Electron app)** — GUI window on user's desktop. Runs the actual browser session with user logins (cookies, Google auth). Chrome CDP debug port at `localhost:9222`.
2. **electron-viewer.js** (at `~/.hermes/scripts/electron-viewer.js`) — Node.js server that connects to the Electron CDP and serves a screenshot viewer. Runs on port `3099`. Shares the same session/cookies as the Tandem Browser.

## The viewer does NOT connect to the Playwright Chrome

There are TWO Chrome instances:
- `chrome` (PID from Tandem Electron, port 9222) — the actual browser the user sees
- Playwright Chrome (separate, if launched) — a headless instance with different cookies

The electron-viewer.js explicitly polls `/json` and uses `webview` type targets to connect to the user's actual content.

## API Endpoints (port 3099)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/screenshot.png` | GET | Current page screenshot |
| `/info` | GET | JSON list of page targets (id, title, url) |
| `/navigate` | POST | Navigate to a URL (body: `{"url": "..."}`) |
| `/click` | POST | Click at pixel coordinates (body: `{"x": N, "y": N}`) |

The `/click` endpoint was added to `electron-viewer.js` during this session (it didn't exist originally). The HTML viewer has `img.onclick` that POSTs to `/click`.

## Setting Up the Viewer

```bash
# Install ws dependency
cd /home/sc/.hermes/scripts && npm init -y && npm install ws

# Start the viewer
node /home/sc/.hermes/scripts/electron-viewer.js

# Verify it connected to the Electron page
cat /tmp/electron-viewer.log
```

## SEEK Specifics

### Google Sign-In (GSI)

SEEK uses Google's GSI (Google Sign-In) which renders inside an **iframe** from `accounts.google.com/gsi/button?theme=...`. This means:

- Cannot find the button via `document.querySelector` on the parent page — it's in a cross-origin iframe
- Must click via CDP mouse events at the iframe's coordinates on the parent page
- The iframe position varies by viewport size — use vision_analyze on a screenshot to estimate coordinates

### Login Flow

1. Navigate to `https://www.seek.com.au`
2. Click the "Continue as Sean [email]" button in the GSI iframe
3. Browser auto-redirects through Google OAuth to SEEK dashboard
4. User lands on job search page with avatar visible (profile initial in top-right)

### Job Search URLs

- Search by company: `https://au.seek.com/{Company}-Jobs?location=Sydney`
- Search with keywords: `https://www.seek.com.au/jobs?keywords={keywords}&location=Sydney`
- Job detail: `https://www.seek.com.au/job/{numeric-id}`

### Notes

- SEEK has aggressive bot detection (Cloudflare). The **only** reliable way to browse is through the Tandem Browser's Electron session.
- `curl` to any SEEK URL returns a Cloudflare challenge page.
- Once logged in through the shared browser, `visit` the page, take a screenshot via `/screenshot.png`, then `analyze` via `vision_analyze`.
