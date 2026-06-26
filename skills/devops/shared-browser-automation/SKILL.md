---
name: shared-browser-automation
category: devops
description: Automate web forms and interactions through the Tandem/Electron shared browser using CDP and the electron-viewer API. Covers form filling, button clicking, file uploads, Angular/React form handling, and screenshot verification.
triggers:
  - "shared browser"
  - "electron viewer"
  - "form automation"
  - "cdp automation"
  - "tandem browser"
  - "seek apply"
  - "job application"
active: false  # Load only when the user's task involves browser automation through the shared viewer
---

# Shared Browser Automation

The Hermes environment runs an **electron-viewer** (`/home/sc/.hermes/scripts/electron-viewer.js`) on `http://127.0.0.1:3099` that connects to the Tandem Browser's Electron app CDP at port `9222`. This gives you a shared browser session with the user — same cookies, same login state.

## Endpoints

All via HTTP POST to `http://127.0.0.1:3099`:

| Endpoint | Body | Purpose |
|----------|------|---------|
| `/navigate` | `{"url": "..."}` | Navigate to URL |
| `/screenshot.png` | (GET) | Current page screenshot |
| `/info` | (GET) | JSON list of page targets |
| `/click` | `{"x": 481, "y": 490}` | Click at pixel coordinates |
| `/click-text` | `{"text": "Continue"}` | Find + click button/link by text (fuzzy match) |
| `/fill` | `{"selector": "[name=\"mobile\"]", "value": "..."}` | Fill form field + notify Angular |

## Use Method

### 1. Check browser state
```
curl -s http://127.0.0.1:3099/info
curl -s -o /tmp/screenshot.png http://127.0.0.1:3099/screenshot.png
```

### 2. Navigate
```
curl -s -X POST http://127.0.0.1:3099/navigate -H "Content-Type: application/json" -d '{"url":"https://..."}'
sleep 4
```

### 3. Click buttons
```
curl -s -X POST http://127.0.0.1:3099/click-text -H "Content-Type: application/json" -d '{"text":"Quick apply"}'
```

### 4. Fill fields
```
curl -s -X POST http://127.0.0.1:3099/fill -H "Content-Type: application/json" -d '{"selector":"[name=\"mobile\"]","value":"0434968983"}'
```

### 5. Upload files (CDP direct)
Use `DOM.setFileInputFiles` via a Node.js CDP script:
- Click "Upload a resumé" label first
- Wait 1s for file input to render
- Use `DOM.querySelector` to find `#resume-fileFile`
- Call `DOM.setFileInputFiles` with the file path

### 6. Verify before submission
Always take a screenshot of the review/submit page and show the user before clicking final submit.

## CDP Direct Access

For complex forms, connect to the underlying Chrome DevTools Protocol at `ws://127.0.0.1:9222`. Install `ws` package:
```
cd /tmp && npm init -y 2>/dev/null && npm install ws
```

Key CDP methods:
- `Page.navigate` — navigate to URL
- `Runtime.evaluate` — execute JavaScript in page context
- `DOM.querySelector` + `DOM.setFileInputFiles` — file uploads
- `Input.dispatchMouseEvent` — click at coordinates
- `Input.insertText` — type text into focused element
- `Page.captureScreenshot` — take screenshot

## Angular Form Handling

AngularJS forms need their model updated directly, not just the DOM:
```javascript
const scope = angular.element(inputElement).scope();
scope.$apply(function() {
  scope.data.contact.mobile = '0434968983';
});
```

Then click radio/checkbox elements directly to trigger Angular change detection:
```javascript
document.querySelector('input[name="question_107"][value="289"]').click();
```

## Pitfalls

1. **SEEK swaps uploaded CVs**: SEEK's profile stores old resumes. After uploading via file input, verify the displayed filename matches what you uploaded. If it shows an old resume, the upload may not have registered. **Always verify** on the review page before submitting.
2. **AngularJS form validation**: Setting `el.value` alone doesn't update Angular's model. Use `scope.$apply()` or `angular.element(el).triggerHandler('input')`. For stubborn Angular forms, find the scope via `angular.element(document.querySelector('[name=\"mobile\"]')).scope()` and set `scope.data` directly.
3. **React forms (SEEK role-requirements)**: Text fields with `indirect_*` names are custom React components. DOM value changes may not trigger validation. Use the `/fill` endpoint which dispatches proper events. When stuck, check `document.querySelectorAll('input[type="text"], input:not([type]), textarea')` for empty values and fill them all.
4. **Tab switching**: The user may navigate away in the Tandem Browser GUI. Always re-navigate to your target URL before proceeding.
5. **Cloudflare tunnel**: The browse.codeovertcp.com URL requires Cloudflare Access auth. Use localhost:3099 from inside the container.
6. **Button text has zero-width characters**: SEEK buttons like "Continue⁠" have invisible Unicode chars. Use `click-text` endpoint (fuzzy match via `includes()`) or `b.textContent.trim().includes('Continue')` in CDP scripts.
7. **Radio/checkbox forms block Continue**: After filling selects and text fields, radio button groups and checkbox groups may still be empty. Use `document.querySelectorAll('input[type="radio"]')` — click first in each group by name. Same for checkboxes.
8. **SEEK upload race condition**: After clicking "Upload a resumé", the file input renders asynchronously. Wait 1-2s before calling `DOM.setFileInputFiles`. The Continue button may not work until the upload finishes.
