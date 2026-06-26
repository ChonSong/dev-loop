---
name: cdp-browser-automation
description: Automate web browsers via Chrome DevTools Protocol (CDP) through a Node.js viewer server. Fill forms, upload files, handle Angular/React SPAs, bypass IP blocks via host-network Chrome.
category: automation
---

# CDP Browser Automation

## When to use
A site requires login cookies, bypasses Cloudflare, or has complex Angular/React forms that resist simple DOM manipulation. Uses a headless Chrome instance running on the host network (bypasses container IP blocks).

## Architecture
```
Headless Chrome (port 9222) ← electron-viewer.js (port 3099) ← Your HTTP commands
```
- Chrome exposes CDP on `127.0.0.1:9222`
- `electron-viewer.js` at `~/.hermes/scripts/electron-viewer.js` connects to CDP
- Serves HTTP API on `http://127.0.0.1:3099`

## Quick Start
```bash
# 1. Start headless Chrome with CDP
/path/to/chrome --headless --remote-debugging-port=9222 --no-sandbox --disable-gpu &

# 2. Start the viewer
node ~/.hermes/scripts/electron-viewer.js &

# 3. Use it
curl -X POST http://127.0.0.1:3099/navigate -d '{"url":"https://site.com"}'
curl -X POST http://127.0.0.1:3099/click-text -d '{"text":"Quick apply"}'
```

## HTTP API Endpoints

| Method | Path | Body | Description |
|--------|------|------|-------------|
| GET | `/info` | — | Current page URL + title |
| GET | `/screenshot.png` | — | Page screenshot |
| POST | `/navigate` | `{"url":"..."}` | Navigate to URL |
| POST | `/click` | `{"x":N,"y":N}` | Click at pixel coordinates |
| POST | `/click-text` | `{"text":"..."}` | Click element by text content (fuzzy match) |
| POST | `/fill` | `{"selector":"[name=X]","value":"..."}` | Fill form field by CSS selector |

## Common Workflow: SEEK Quick Apply

1. Navigate to job page → `/navigate`
2. Click "Quick apply" → `/click-text`
3. Upload CV (see File Uploads below)
4. Click "Don't include a cover letter" → `/click-text`
5. Click "Continue" → `/click-text`
6. **Handle role-requirements** — fill all form elements:
   - Selects: set `.value` + dispatch `change` event
   - Radios: `.click()` + dispatch `change`
   - Checkboxes: `.click()` + dispatch `change`
   - Text fields: set `.value` + dispatch `input` + dispatch `change`
   - Hidden text inputs named `questionnaire.indirect_*` — these are also required
7. Continue through profile step → `/click-text`
8. Click "Submit application" → `/click-text`

## File Uploads via CDP

Use `DOM.setFileInputFiles` via the WebSocket connection:

```javascript
const doc = await send('DOM.getDocument');
const q = await send('DOM.querySelector', {
  nodeId: doc.result.root.nodeId,
  selector: '#fileInputId'
});
await send('DOM.setFileInputFiles', {
  nodeId: q.result.nodeId,
  files: ['/path/to/file.pdf']
});
```

First click "Upload a resumé" label to make the file input visible, then upload.

## AngularJS Form Handling

When setting DOM values doesn't register (form keeps showing validation errors):

```javascript
// Access Angular scope from any input in the form
const scope = angular.element(input).scope();
scope.$apply(function() {
  scope.data.fieldName = value;  // field names vary by form
});
```

Radio buttons and checkboxes in Angular forms — setting `scope.data` alone isn't enough. Also click the actual DOM element:
```javascript
input.click();
input.dispatchEvent(new Event('change', {bubbles: true}));
try { angular.element(input).scope().$digest(); } catch(e) {}
```

## CDP Result Parsing

`Runtime.evaluate` with `returnByValue: true` returns messages in this nested structure:
```json
{"id": N, "result": {"result": {"type": "string", "value": "ACTUAL_VALUE"}}}
```
So access via `m.result.result.value`, NOT `m.result.value`.

## Pitfalls

- **CDP WebSocket target may disappear** if the page navigates — reconnect needed
- **Angular forms need `$scope.$apply()`** to acknowledge DOM changes — without this, validation clears but the form won't submit
- **React forms** may need different events — try native `input` + `change` events with `{bubbles: true}`
- **SEEK role-requirements** often have hidden text inputs with `questionnaire.indirect_*` names — find and fill them
- **Shared browser is single-threaded** — parallel agents navigating it will conflict (each overwrites the other's page)
- **Cloudflare** blocks most company career portals from automated access — SEEK Quick Apply via host-network Chrome is more reliable
- **CV verification**: after uploading via `setFileInputFiles`, SEEK may show "Loading..." and then revert to an older stored resume. Verify the page text shows the correct filename before clicking Continue

## References

- `references/seek-apply-workflow.md` — detailed SEEK Quick Apply flow with screenshots
