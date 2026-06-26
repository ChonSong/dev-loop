---
name: tandem-browser-shared-session
description: Fix Tandem Browser so the AI can see and share the same browsing session as the user
---

# Tandem Browser — Shared Session Setup

The Tandem Browser Electron app (user's GUI window) and the AI-accessible shared browser use **separate browser instances** with different user data dirs, so they don't share cookies/sessions.

Fix: add `--remote-debugging-port=9222` to the Electron app and connect a viewer to its **webview** CDP targets instead of a separate Playwright Chrome.

## Scripts

### `~/.hermes/scripts/start-tandem.sh`
Starts Tandem with remote debugging + viewer. Safe to re-run (kills old ports first).

### `~/.hermes/scripts/electron-viewer.js`
Node.js HTTP server that connects to the Electron CDP's **webview targets** (user's tabs, type `webview`) and serves a screenshot viewer at `localhost:3099`. Unlike `shared-browser.mjs`, it does NOT navigate on connect — only observes.

**Known limitations (CDP Runtime.evaluate):**
- The response structure for `Runtime.evaluate` with `returnByValue: true` is `{"id": N, "result": {"result": {"type": "...", "value": ACTUAL_VALUE}}}` — the actual data is at `m.result.result.value`, NOT `m.result.value`.
- Cross-origin iframes (like Google GSI sign-in buttons from `accounts.google.com/gsi/button`) cannot be clicked via `Runtime.evaluate` JS execution — their content is in a separate security context. Must use `Input.dispatchMouseEvent` with page coordinates (click at the iframe's bounding rect center).
- `Runtime.evaluate` on webview targets may time out if the page is mid-navigation or the webview has a pending load event. Navigate first, wait 3-5s, then evaluate.
## Known Limitations with Web Components (Shadow DOM)

- **Shadow DOM / Web Components**: Sites using Custom Elements with Shadow DOM like Google Colab (`<mwc-dialog>`, `<md-icon>`, `<colab-*>`), Google Drive, and newer Google apps hide their internal DOM from `Runtime.evaluate`. `querySelector` cannot penetrate shadow roots. Even open shadow roots (`el.shadowRoot`) are not accessible via CDP evaluate.
- **Signs you're hitting a Shadow DOM wall**: (a) `querySelector` returns null for elements clearly visible in screenshots, (b) coordinate-based clicks via `/click` land but nothing happens, (c) `getComputedStyle` doesn't find the element. When all three happen, stop trying to automate — Shadow DOM is the blocker.
- **Workaround**: Coordinate-based mouse clicks via `/click` are the only reliable interaction. Use `screenshot.png` + `vision_analyze` to read page state and get click coordinates.
- **When to pull the plug**: After 3 distinct attempts to automate a web component fail (different approaches, not just retrying the same thing), stop. Provide the user with a clear one-step instruction for what they need to do manually. Continuing to try different approaches wastes turns. Example: "Colab's Upload dialog is in Shadow DOM — I can't click it via CDP. Click File → Upload Notebook in your Tandem window and select the file."

**The `/click` endpoint must be added manually** — the base electron-viewer.js only ships `/screenshot.png`, `/info`, and `/navigate`. To enable coordinate-based clicking, add this block inside the HTTP handler before the HTML fallback:
```javascript
if (req.url === '/click' && req.method === 'POST') {
  let body = '';
  for await (const chunk of req) body += chunk;
  const { x, y } = JSON.parse(body);
  await cdp.send('Input.dispatchMouseEvent', { type: 'mousePressed', x, y, button: 'left', clickCount: 1 });
  await cdp.send('Input.dispatchMouseEvent', { type: 'mouseReleased', x, y, button: 'left', clickCount: 1 });
  res.writeHead(200, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify({ ok: true }));
  return;
}
```

**Dependency:** The script uses `require('ws')` — `ws` must be installed in the same directory: `cd /home/sc/.hermes/scripts && npm install ws`. Run this once; after install, the viewer can be started from any directory.

## New `/fill` and `/click-text` Endpoints

The `electron-viewer.js` has been extended with two HTTP endpoints for DOM-based form automation:

### `POST /fill` — Fill a form field by CSS selector

```bash
curl -s -X POST http://localhost:3099/fill \
  -H 'Content-Type: application/json' \
  -d '{"selector": "[name=\"mobile\"]", "value": "0434968983"}'
```

```bash
# For <select> elements:
curl -s -X POST http://localhost:3099/fill \
  -H 'Content-Type: application/json' \
  -d '{"selector": "select[name=\"country\"]", "value": "string:AU"}'
```

The endpoint sets `el.value`, dispatches `input` + `change` events, and calls `angular.element(el).triggerHandler()` for Angular awareness.

### `POST /evaluate` — Execute arbitrary JavaScript

Added in session 2026-06-16. Executes JS in the page context and returns the result:

```bash
curl -s -X POST http://localhost:3099/evaluate \
  -H 'Content-Type: application/json' \
  -d '{"expression": "document.title"}'
# → {"ok":true,"result":"SEEK - Jobs"}

curl -s -X POST http://localhost:3099/evaluate \
  -H 'Content-Type: application/json' \
  -d '{"expression": "window.scrollTo(0, 800)"}'
# → {"ok":true,"result":null}
```

**Implementation:** This endpoint was added to `electron-viewer.js` manually. If it's missing from your version, add this block inside the HTTP handler before the HTML fallback:

```javascript
if (req.url === '/evaluate' && req.method === 'POST') {
  let body = '';
  for await (const chunk of req) body += chunk;
  const { expression } = JSON.parse(body);
  const result = await cdp.send('Runtime.evaluate', {
    expression,
    returnByValue: true
  });
  res.writeHead(200, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify({ ok: true, result: result.result?.value }));
  return;
}
```

**Important:** `returnByValue: true` only works for JSON-serializable values. Complex objects (DOM nodes, functions) return `null`. Always return explicitly JSON-serializable data (strings, numbers, booleans, arrays of those, plain objects).

**When expressions get complex** (nested arrays, objects, long strings), write them to a temporary Python script file and use `execute_code()` from `hermes_tools` to call the viewer — this avoids shell escaping issues with the curl command.

```bash
# Exact match:
curl -s -X POST http://localhost:3099/click-text \
  -H 'Content-Type: application/json' \
  -d '{"text": "Continue"}'

# Fuzzy match (contains):
curl -s -X POST http://localhost:3099/click-text \
  -H 'Content-Type: application/json' \
  -d '{"text": "Australian cit"}'
```

The endpoint queries `button, a, input[type="submit"], [role="button"]` elements, tries exact text match first, then fuzzy contains match. Scrolls into view before clicking.

### Restart after adding endpoints

```bash
kill $(lsof -ti :3099) 2>/dev/null
sleep 1
node /home/sc/.hermes/scripts/electron-viewer.js > /tmp/electron-viewer.log 2>&1 &
sleep 2
cat /tmp/electron-viewer.log  # Verify "Connected"
```

## Application Form Automation

### AngularJS portals (Elmo, etc.)
Many employer career portals (NGS Super, others using Elmo talent systems) are AngularJS SPAs. DOM value changes via `el.value = '...'` do NOT propagate to the Angular model. Three approaches, in order of reliability:

1. **ngModel controller access** (most reliable for text inputs/selects):
   ```javascript
   const ngEl = angular.element(document.querySelector('[name="fieldName"]'));
   const ngModel = ngEl.controller('ngModel');
   ngModel.$setViewValue('desired-value');
   ngModel.$render();
   // For selects with prefixed values (e.g., "string:AU"), use the full option value
   ```

2. **Scope assignment** (for Angular model-backed forms):
   ```javascript
   // Try from a known input first — [ng-app] may not have a directly accessible scope
   const scope = angular.element(document.querySelector('[name="mobile"]')).scope()
     || angular.element(document.querySelector('[ng-app]')).scope();
   scope.$apply(function() {
     scope.data.contact.mobile = 'value';
   });
   ```

   If `$apply()` is too heavy (throws for unrelated digest errors), use `$digest()` after direct model assignment:
   ```javascript
   scope.data.contact.mobile = 'value';
   scope.$digest();  // lightweight — doesn't trigger $rootScope digest
   ```

3. **DOM event dispatch** (least reliable — may not trigger Angular digest):
   ```javascript
   el.value = 'value';
   el.dispatchEvent(new Event('input', {bubbles: true}));
   el.dispatchEvent(new Event('change', {bubbles: true}));
   ```

4. **CDP `DOM.setFileInputFiles`** for file uploads — the only reliable way to set file inputs in AngularJS forms:
   ```javascript
   // Get document root
   const doc = await send('DOM.getDocument');
   const query = await send('DOM.querySelector', {
     nodeId: doc.result.root.nodeId,
     selector: '#resumeFile'
   });
   await send('DOM.setFileInputFiles', {
     nodeId: query.result.nodeId,
     files: ['/absolute/path/to/file.pdf']
   });
   ```

**Pitfalls with AngularJS forms:**
- Country selects often use prefixed values like `"string:AU"` instead of plain `"AU"`. Always inspect `select.options` to find the correct value.
- Radio buttons need `element.click()` + `element.checked = true` to satisfy Angular's two-way binding. After setting scope values, call `scope.$digest()` to propagate changes to the DOM — this is lighter and more reliable than `scope.$apply()` when you're only updating models.
- The Angular scope may not be accessible from `[ng-app]` directly. If `angular.element(document.querySelector('[ng-app]')).scope()` returns undefined, try from any form input: `angular.element(document.querySelector('[name="fieldName"]')).scope()`.
- After filling, click "Save" before "Next" — the save validates via Angular and persists. If "Next" is clicked before save, Angular shows validation errors even if values appear set.
- The `$scope` may not be directly accessible from the document body if the app uses component-based architecture. Always try `ngModel.$setViewValue` first.
- Multi-step forms update `window.location.hash` (e.g., `#/step2`). Monitor the hash to detect progress transitions.

### React SPAs (SEEK Quick Apply)

SEEK's Quick Apply uses React with a mix of `<select>` dropdowns and radio/checkbox inputs. Unlike Angular, React doesn't auto-detect DOM value changes — you must dispatch proper native events.

#### Select dropdowns (first 3 screening questions)

```javascript
const sel = document.querySelector('select[name="questionnaire.AU_Q_6_V_10"]');
sel.value = 'AU_Q_6_V_10_A_14970';  // Australian citizen
sel.dispatchEvent(new Event('change', {bubbles: true}));
```

Use the `/fill` endpoint for this — it dispatches `change` automatically:
```bash
curl -s -X POST http://localhost:3099/fill \
  -H 'Content-Type: application/json' \
  -d '{"selector": "select[name=\"questionnaire.AU_Q_6_V_10\"]", "value": "AU_Q_6_V_10_A_14970"}'
```

#### Radio buttons (binary questions)

```javascript
const radio = document.querySelector('input[type="radio"][name="questionnaire.AU_Q_28763_V_3"][value="AU_Q_28763_V_3_A_28765"]');
radio.click();
radio.dispatchEvent(new Event('change', {bubbles: true}));
```

#### Checkboxes (multi-select questions)

```javascript
const cb = document.querySelector('input[type="checkbox"][name="questionnaire.AU_Q_28759_V_3"][value="..."]');
cb.click();
cb.dispatchEvent(new Event('change', {bubbles: true}));
```

#### File upload

React file inputs work the same as Angular — use `DOM.setFileInputFiles`:

```javascript
const doc = await send('DOM.getDocument');
const query = await send('DOM.querySelector', {
  nodeId: doc.result.root.nodeId,
  selector: '#resume-fileFile'
});
await send('DOM.setFileInputFiles', {
  nodeId: query.result.nodeId,
  files: ['/absolute/path/to/cv.pdf']
});
```

**Note:** The file input MUST be visible in the DOM. On SEEK, click the "Upload a resumé" radio first to reveal the file input.

#### SEEK application flow (multi-step)

```
1. /job/{id}/apply       → Choose documents (upload CV, set cover letter)
2. /job/{id}/apply/role-requirements  → Employer screening questions
3. /job/{id}/apply/profile           → Confirm SEEK profile
4. /job/{id}/apply/review            → Review & Submit
5. /job/{id}/apply/success           → Confirmation
```

**Check progress** via URL: the path segment after `/apply/` tells you which step.

### React form handling — advanced

SEEK's Quick Apply uses React with hidden `<select>` elements and custom radio/checkbox widgets. Simple `el.value = '...'` with `dispatchEvent` often fails to propagate to React's state.

#### Textareas (employer screening questions)

Use the **native value setter** trick to bypass React's synthetic event system:

```javascript
const ta = document.querySelector('textarea');
const nativeSetter = Object.getOwnPropertyDescriptor(
    window.HTMLTextAreaElement.prototype, 'value'
).set;
nativeSetter.call(ta, 'Yes');
ta.dispatchEvent(new Event('input', {bubbles: true}));
ta.dispatchEvent(new Event('change', {bubbles: true}));
```

This is required because React tracks value changes through its own event system — setting `ta.value = 'Yes'` directly won't trigger a React state update.

#### Radio buttons (binary/selection questions)

Radio buttons on SEEK's role-requirements page use auto-generated IDs (`:r1r:`, `:r1u:`, etc.) that change on re-render. Do NOT set the checked property directly — React won't see it.

**Correct approach — click the label:**

```javascript
const labels = document.querySelectorAll('label');
for (const l of labels) {
    const t = l.textContent.trim();
    // Match the specific option text (e.g. "No", "Yes, Baseline")
    if (t === 'No' && l.getAttribute('for')) {
        const input = document.getElementById(l.getAttribute('for'));
        if (input && input.type === 'radio') {
            l.click();
            break;
        }
    }
}
```

Label clicks propagate through React's event system and update component state. Direct `input.checked = true` does not.

**Fallback for unmatched radio groups:**

When you don't know which option text to match, find all radio groups with nothing selected and click the last option in each group (typically the most conservative):

```javascript
const groups = {};
document.querySelectorAll('input[type="radio"]').forEach(r => {
    if (r.name) {
        if (!groups[r.name]) groups[r.name] = [];
        groups[r.name].push(r);
    }
});
for (const radios of Object.values(groups)) {
    if (!radios.some(r => r.checked)) {
        const last = radios[radios.length - 1];
        const label = document.querySelector('label[for="' + last.id + '"]');
        if (label) label.click();
    }
}
```

#### Checkboxes (privacy policy, consent)

Same issue as radios — use native setter for the `checked` property:

```javascript
const cb = document.getElementById('privacyPolicy');
const nativeSetter = Object.getOwnPropertyDescriptor(
    window.HTMLInputElement.prototype, 'checked'
).set;
nativeSetter.call(cb, true);
cb.dispatchEvent(new Event('change', {bubbles: true}));
```

#### Select dropdowns

Standard `el.value = '...'` + `dispatchEvent(new Event('change', {bubbles: true}))` works for React selects — no special handling needed. Always inspect option values first:

```javascript
const selects = document.querySelectorAll('select');
for (const s of selects) {
    console.log(s.id, Array.from(s.options).map(o => o.text.trim()));
}
```

#### SEEK application flow (multi-step)

```
1. /job/{id}/apply       → Choose documents (upload CV, set cover letter)
2. /job/{id}/apply/role-requirements  → Employer screening questions
3. /job/{id}/apply/profile           → Confirm SEEK profile
4. /job/{id}/apply/review            → Review & Submit
5. /job/{id}/apply/success           → Confirmation
```

**Check progress** via URL: the path segment after `/apply/` tells you which step. Use `window.location.href` in a CDP evaluation.

#### Looping through multi-step forms

The `data-testid="continue-button"` attribute reliably identifies the Continue button across all SEEK steps:

```javascript
const btn = document.querySelector('button[data-testid="continue-button"]');
if (btn) {
    btn.scrollIntoView({block: 'center'});
    btn.click();
}
```

**Important:** The button text contains a zero-width joiner character (U+2060): `"Continue⁠"`. Exact text matching with `.textContent.trim() === 'Continue'` will FAIL. Use `.includes('Continue')` or the `data-testid` selector instead.

#### Batch application workflow

For high-volume sessions with many Quick Apply jobs:

1. Collect all unique job URLs from search results (deduplicate by URL, not title)
2. For each job: navigate → check QA badge → click QA → fill all fields → step through → submit
3. Use a script that calls `fill_all()` before each Continue click — this handles arbitrary form fields regardless of which question appears

**When stuck in an infinite Continue loop:** The Continue button is clickable but you're cycling between steps. This happens when a required field wasn't properly filled. Check for:
- Unanswered radio button groups (React doesn't register the selection)
- Textareas with empty values (React synthetic event didn't fire)
- Unchecked privacy/consent checkboxes
- The URL path to identify which step you're cycling through

#### Pitfalls with React forms (SEEK)

- Select dropdowns may have empty-string default values. Always inspect option values before setting.
- Radio and checkbox `value` attributes are opaque IDs, not human-readable text. Map labels to values in advance.
- The "Please make a selection" error overlay appears on validation failure. Check `document.querySelectorAll('[class*="error"], [class*="alert"]')` after attempting submit.
- SEEK profile step may have pre-filled data — just click Continue if no changes needed.
- The "Submit application" button text may include a non-breaking space: `"⁠Submit application"`.

## Architecture

```
User Desktop                     Hermes AI
┌──────────────────────┐         ┌─────────────────┐
│ Tandem Electron App  │         │ electron-viewer │
│  ┌────────────────┐  │ CDP     │  ┌─────────────┐│
│  │ Webview Tab 1  │◄─┼─────────┼──┤ Screenshot  ││
│  │ (persist:tandem│  │  :9222  │  │ & control   ││
│  │  cookies)      │  │         │  └─────────────┘│
│  ├────────────────┤  │         │ localhost:3099  │
│  │ Main Shell     │  │         └─────────────────┘
│  │ (index.html)   │  │
│  └────────────────┘  │
└──────────────────────┘
```

## Process Management

```bash
# Restart everything
~/.hermes/scripts/start-tandem.sh

# Manual steps if needed:
lsof -ti :9222 | xargs -r kill
lsof -ti :3099 | xargs -r kill
cd /home/sc/repos/tandem-browser
export DISPLAY=:0
nohup node_modules/electron/dist/electron . --no-sandbox --remote-debugging-port=9222 > /tmp/tandem-debug.log 2>&1 &
# Wait for CDP, then:
NODE_PATH=./node_modules nohup node /home/sc/.hermes/scripts/electron-viewer.js > /tmp/electron-viewer.log 2>&1 &
```

## Checking Status

```bash
# Is Electron CDP accessible?
curl -s http://127.0.0.1:9222/json/version

# List all page/webview targets
curl -s http://127.0.0.1:9222/json | python3 -c "
import sys,json
for t in json.load(sys.stdin):
    print(f'  [{t[\"type\"]:8s}] {t.get(\"title\",\"?\")[:60]:60s} {t.get(\"url\",\"?\")}')"

# Get viewer info (what the AI sees)
curl -s http://localhost:3099/info
```

## Reference Image Collection (for Coach-Agent Visual Comparison)

Tandem can navigate reference products and capture screenshots for the coach-agent's Spec Gap Detection (Phase 2.5). The coach compares these against the player's rendered output to find missing UI components and layout mismatches.

### Convention

Save reference images to the project's `docs/` directory:

```
docs/reference-<route>-<description>.png
```

Examples:
- `docs/reference-study-interface.png` → target for `/study`
- `docs/reference-home-layout.png` → target for `/`
- `docs/designs/quiz-card.png` → target for `/quiz`

### Capture Flow

```bash
# 1. Navigate to the reference page
curl -s -X POST http://localhost:3099/navigate \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://app.gtowizard.com/study"}'

# 2. Wait for page to fully render (5-10s for JS SPAs)
sleep 6

# 3. Take screenshot and verify it's real content
curl -s -o docs/reference-study-interface.png http://localhost:3099/screenshot.png
ls -la docs/reference-study-interface.png
# → Should be > 20KB for a real rendered page
# → < 15KB = loading state, login screen, or blank page
```

### Pitfalls

- **Login-walled targets**: The real GTO Wizard, GitHub, Facebook, and most SaaS products require authentication. Tandem captures the login page, not the interior. In this case, find an alternative: ask the user to log in, use a design mockup, or skip the reference image — the coach still runs structural checks.
- **Stale references**: If a reference image matches an old version of the target, the coach flags false-positive gaps. Regenerate reference images when the target design changes.
- **Timing**: SPAs render progressively. Wait 5-10s after navigation before capturing. Check file size as a heuristic — small files suggest a loading state. Take a second screenshot after scrolling if the page has lazy-loaded sections.
- **Viewport**: Tandem captures one viewport. Match the target's expected resolution (typically 1440px desktop).
- **SPA server-side redirects**: Single-page apps may redirect server-side unknown routes to a default page (e.g., `/courses` → `/`). When `/navigate` bounces to a different URL, the SPA router ignored the route server-side. Use client-side navigation instead: click a link in the UI or evaluate `window.location.href = '...'` via the `/evaluate` endpoint. The `/navigate` endpoint triggers a full server request — SPAs need client-side routing.
- **Canvas/WebGL rendered interfaces**: Some tools (game engines, WebGL renderers, canvas-based poker tables) render interactive elements programmatically. The DOM may show empty `<div>` containers or wrapper elements only. CDP evaluation finds no clickable buttons even though the screenshot clearly shows them. Detection: if `document.querySelectorAll('button')` returns empty but the screenshot shows buttons, the content is canvas-rendered. Workaround: click by pixel coordinates via the `/click` endpoint (requires the `/click` endpoint to be added to electron-viewer.js). Or accept that some reference targets can't be fully automated — capture what you can, let the coach compare visually.

## Viewing & Controlling

The viewer at `localhost:3099` shows a screenshot of the webview it's connected to:

```bash
# Take a screenshot
curl -s -o /tmp/snap.png http://localhost:3099/screenshot.png

# Navigate the webview (opens in the user's Tandem tab)
curl -s -X POST http://localhost:3099/navigate -H 'Content-Type: application/json' \
  -d '{"url":"https://example.com"}'

# Click at coordinates
curl -s -X POST http://localhost:3099/click -H 'Content-Type: application/json' \
  -d '{"x": 400, "y": 300}'

# Type text
curl -s -X POST http://localhost:3099/type -H 'Content-Type: application/json' \
  -d '{"text":"hello world"}'
```

## Connecting to a Different Webview Target

If the user opens a new tab, the viewer may still be connected to the old webview. To switch:

1. List targets: `curl -s http://127.0.0.1:9222/json`
2. Find the new webview target ID
3. Restart the viewer (it auto-connects to the first webview)

## Company Portals — What Works via Tandem

The Tandem Electron browser (with its Chromium-based User-Agent and full JS engine) bypasses Cloudflare/anti-bot protection on **many** company career portals that block the container's Playwright browser.

### ✅ Work reliably

| Portal | Notes |
|--------|-------|
| **Amazon.jobs** | Loads fully. Apply → Google sign-in works (no Amazon account needed). CAPTCHA at the final step requires human interaction. |
| **SEEK.com.au** | Full access — search, Quick Apply, employer questions, submission. |
| **Datadog Careers** | careers.datadoghq.com — loads all job listings. |
| **Canva Careers** | lifeatcanva.com — jobs filterable by country/team. JS-rendered SPA. |
| **Atlassian Careers** | atlassian.com/company/careers — full job search with filters. |

### ❌ Still blocked

| Portal | Issue |
|--------|-------|
| **Datacom Careers** | Cloudflare blocks Tandem too. |
| **LinkedIn** | Sign-in wall — requires user to log in manually. |

### Amazon.jobs — Google Sign-In Workflow

The AWS Cloud Support Associate Apprentice role (and other Amazon jobs) can be applied to **without creating a separate Amazon account** — use Google OAuth:

1. Navigate to the job page: `https://www.amazon.jobs/en/jobs/{JOB_ID}/...`
2. Click "Apply now" → redirects to `passport.amazon.jobs`
3. Click "Login with Google" → opens Google account chooser
4. Click the user's Google account → OAuth consent screen
5. Click "Allow" → Amazon.jobs email confirmation page
6. **CAPTCHA blocker**: Image selection challenge (click matching images). Cannot be automated — user must complete this in the Tandem window.
7. After CAPTCHA: email verification → application form → submit

**Important:** The step 5 "Allow" grants Amazon.jobs access to the Google account's name and email. This is a standard OAuth scope — safe to proceed.

Always verify the outcome after submitting a form:

### Check the success page

The URL tells you the result:
- `/apply/success` on SEEK = submitted ✅
- Still on `/apply/review` or same step = validation failed or click didn't register

### Verify which documents were attached

Before clicking the final Submit, check the review page text for document names:

```bash
curl -s http://localhost:3099/info
# Then CDP to extract text
```

On SEEK's review page, look for:
- `"Resume"` + filename — confirms what was attached
- `"Cover letter"` + "No cover letter" / filename

### Before Submit: Verify Attached Resume Filename

**Always check which resume SEEK actually attached before clicking Submit.** The single most common application error is SEEK silently swapping your freshly-uploaded CV for an older one from the user's profile.

Procedure at the review step:

```javascript
// Extract the review page text
const text = await send('Runtime.evaluate', {
  expression: `document.body.innerText`,
  returnByValue: true
});
const pageText = r?.result?.result?.value || '';
// Search for .pdf filenames in the resume section
const resumeStart = pageText.indexOf('Resumé') >= 0 ? pageText.indexOf('Resumé') : 0;
const resumeSection = pageText.substring(resumeStart, resumeStart + 500);
// Look for 'YOUR_CV_FILENAME.pdf' — if wrong, the old resume was used
```

**Critical SEEK pitfall:** SEEK's Quick Apply may use a **pre-existing resume from the user's SEEK profile** instead of the one you just uploaded. The evidence:
- The file upload shows `"CV - SRE.pdf"` in the upload field (progress indicator)
- But after the upload completes, the review page may show `"8/6/26 - Sean Cheong Software Engineer.pdf"` — an older resume that was already stored on the profile

**Mitigation:** After clicking "Upload a resumé" and using `DOM.setFileInputFiles`, navigate to the review step and verify which filename appears before clicking Submit. Use CDP to read the review page text and confirm the correct filename.

### Verify from the success page

```javascript
// After submit, check the page text
const text = await send('Runtime.evaluate', {
  expression: `document.body.innerText`,
  returnByValue: true
});
// Look for "Your application has been sent to" or "Thank you for applying"
const url = await send('Runtime.evaluate', {
  expression: `window.location.href`,
  returnByValue: true
});
// Confirmation URL patterns:
// SEEK  → /apply/success
// Elmo  → page with "Thank you for applying!" text
```

## User Preference: Show CV Screenshots Before Submitting

Before submitting a job application, always:
1. Generate the CV as a PDF
2. Take a screenshot via `Page.captureScreenshot` or Playwright
3. Present the screenshot to the user via `MEDIA:/path/to/screenshot.png`
4. Wait for explicit approval before clicking Submit

Do NOT skip this for any application — even if the same CV was used before. Each submission is a separate action that warrants verification.

## Pitfalls

- **`shared-browser.mjs` is destructive** — it navigates the first target it finds, hijacking the user's main window. Never use it.
- **Electron 40 requires glibc 2.35+** — won't run on Ubuntu 20.04. Error: `/lib/x86_64-linux-gnu/libc.so.6: version 'GLIBC_2.33' not found`. Root cause: native modules need C++20 compilation (GCC 11+), which ships with glibc 2.35+. Cannot work around — even source compilation fails because GCC 9/10 lack `<compare>`/`<source_location>` headers. Fix: upgrade to Ubuntu 22.04+ or run Tandem in Docker with X11 forwarding. Fallback: Chrome CDP viewer pattern.
- **Always check ports before asking the user.** Run `curl -s http://localhost:3099/info` and `curl -s http://127.0.0.1:9222/json/version` first. Tandem may already be running. The skill says to run `start-tandem.sh` but only if the user hasn't already started it. Check, don't ask.
- **Use `execute_code` for complex evaluate calls.** When evaluating multi-step JavaScript that returns structured data (arrays, objects, long strings), use `execute_code()` from `hermes_tools` with `urllib.request` to call the viewer API. This avoids shell escaping issues with curl -d. Pattern:

```python
from hermes_tools import terminal
import json, urllib.request

API = "http://127.0.0.1:3099"
def evaluate(expression):
    data = json.dumps({"expression": expression}).encode()
    req = urllib.request.Request(f"{API}/evaluate", data=data,
        headers={"Content-Type": "application/json"}, method="POST")
    resp = json.loads(urllib.request.urlopen(req, timeout=15).read())
    return resp.get("result")

result = evaluate("""(() => { /* complex JS here */ })()""")
```
- **User expects you to remember how to launch Tandem** — The script `~/.hermes/scripts/start-tandem.sh` is the canonical way. Do NOT ask the user "could you open Tandem?" — just run the script yourself. It kills old processes on 9222/3099, launches the Electron app with `--remote-debugging-port=9222`, waits for CDP, and starts the viewer. The user will see the Tandem window appear on their desktop.
- **`Target.createTarget` is not supported** in Electron's Chromium — you cannot create new hidden pages via CDP. Must connect to existing webview targets.
- **Port conflicts** — `EADDRINUSE :3099` means old viewer process is still running. Kill it first: `lsof -ti :3099 | xargs -r kill`
- **.mjs vs .js** — Electron-viewer uses `require('ws')` so must be `.js` (CommonJS), not `.mjs` (ESM), and needs `NODE_PATH` to find the `ws` module from tandem-browser's node_modules.
- **Module not found: ws** — Always run the viewer with `NODE_PATH=/home/sc/repos/tandem-browser/node_modules` or from the tandem-browser directory. Alternatively, install `ws` in the Hermes scripts dir: `cd /home/sc/.hermes/scripts && npm install ws`.
- **Viewer HTML has a click handler that POSTs to `/click` but the server may not have one** — The base `electron-viewer.js` only serves `/screenshot.png`, `/info`, and `/navigate`. If you try to click from the viewer UI, it'll silently return the HTML page instead. Add the `/click` endpoint as described above. Same applies to the `/type` endpoint for text input.
- **GSI iframes (Google Sign-In) require coordinate-based clicks** — SEEK, among other sites, uses Google's GSI flow where the sign-in button lives in a cross-origin iframe (`accounts.google.com/gsi/button`). JavaScript clicks via `Runtime.evaluate` cannot reach cross-origin iframe content. Use `Input.dispatchMouseEvent` with page coordinates instead. Find the iframe's position via the parent page's DOM: `document.querySelector('iframe[src*=\"accounts.google.com/gsi\"]').getBoundingClientRect()`, then click at the center.
