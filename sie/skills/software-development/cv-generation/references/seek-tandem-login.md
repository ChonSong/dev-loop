# SEEK Sign-In via Tandem Browser (GSI Iframe)

SEEK uses Google Sign-In (GSI) via a cross-origin iframe from `accounts.google.com/gsi/button`. The "Continue as Sean" button lives inside this iframe and cannot be clicked via `Runtime.evaluate` JavaScript injection.

## Login Flow

1. Navigate to `https://www.seek.com.au` in the Tandem Browser
2. A login modal appears with a GSI iframe containing the "Continue as Sean" button
3. **Do NOT try to JS-click the iframe content** — it's cross-origin and cannot be scripted
4. **Use coordinate-based click** (`Input.dispatchMouseEvent`) via CDP at the center of the GSI iframe

### Finding Click Coordinates

The GSI iframe position can be found by querying the parent page DOM:

```javascript
const r = await send('Runtime.evaluate', {
  expression: `(() => {
    const f = document.querySelector('iframe[src*="accounts.google.com/gsi"]');
    if (f) { const r = f.getBoundingClientRect(); return JSON.stringify({x: r.x, y: r.y, w: r.width, h: r.height}); }
    return null;
  })()`,
  returnByValue: true
});
const pos = JSON.parse(r.result.result.value);
// Click at center
await send('Input.dispatchMouseEvent', { type: 'mousePressed', x: pos.x + pos.w/2, y: pos.y + pos.h/2, ... });
await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: pos.x + pos.w/2, y: pos.y + pos.h/2, ... });
```

Alternative: use vision analysis of the screenshot to estimate coordinates. The GSI button is typically centered vertically in the login modal (~y=490 on a 1920x1080 viewport).

### If GSI Click Doesn't Work

- The user can click the button in their Tandem Browser window directly
- After they click, you instantly share the authenticated session
- Verify login by checking for the profile avatar in the top-right of SEEK

## Search URL Formats

- General search: `https://www.seek.com.au/jobs?keywords=KEYWORDS&location=Sydney`
- Company-specific: `https://au.seek.com/COMPANY-jobs?location=Sydney` (works for companies with dedicated pages, e.g., Qvest)
- Job detail: `https://www.seek.com.au/job/{numeric-id}`
- API search (via browser session): SEEK uses a React SPA; the API is not directly accessible from curl

## Robot/Anti-Bot Coverage

SEEK uses Cloudflare challenge pages. The Tandem Browser's Electron app (with stealth patches) typically passes these automatically. If not:
1. The user may need to solve a CAPTCHA in their Tandem window
2. The session cookie persists after that
3. Subsequent navigations from the shared browser will use the same authenticated session

## After Login

Once logged in, the SEEK session shows:
- Profile avatar (letter "S") in top-right
- "Saved searches" and "Saved jobs" tabs
- "Recommended" section with job listings
- Search bar for keyword searches
- Filter pills (Pay, Type, Remote, Classification, Listing time)
