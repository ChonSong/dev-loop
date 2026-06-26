---
name: cdp-form-automation
description: Automate complex web forms (Angular, React) via CDP through the shared electron-viewer
---

# CDP Form Automation

Use when standard browser tools can't handle complex SPA forms — AngularJS validation, React selects, multi-page application flows.

## Setup

The Tandem Browser (Electron app) with CDP on port 9222 is served through the electron-viewer on port 3099. Both are launched together:

```bash
# Start/restart — kills old processes, launches Electron + viewer
bash /home/sc/.hermes/scripts/start-tandem.sh
```

The script does three things:
1. Kills anything on ports 9222 and 3099
2. Launches Electron from `/home/sc/repos/tandem-browser` with `--remote-debugging-port=9222`
3. Waits for CDP to be ready, then starts `electron-viewer.js` on port 3099

**Do NOT start the viewer alone** — it connects to a dead CDP and fails silently. Always run the full `start-tandem.sh` script.

### Verification

```bash
# Check CDP is responding
curl -s http://127.0.0.1:9222/json/version > /dev/null 2>&1 && echo "CDP OK" || echo "CDP DOWN"

# Check viewer is serving
curl -s http://127.0.0.1:3099/info | python3 -m json.tool
```

### Underlying Architecture

```
Your Desktop Tandem Window
  └─ Electron App ──CDP :9222──▶ electron-viewer.js :3099 ──▶ Hermes API calls
       (your session)                 (HTTP bridge)
```

The Electron app runs on your desktop's X display. The viewer connects to its CDP and proxies screenshots + navigation commands. **Same cookies, same session.**

## Available Endpoints

All POST with JSON body unless marked GET:

| Endpoint | Body | Description |
|----------|------|-------------|
| `/navigate` | `{"url": "..."}` | Navigate current tab |
| `/click` | `{"x": y}` | Click at pixel coords |
| `/click-text` | `{"text": "..."}` | Find button/link by text and click (fuzzy match fallback) |
| `/fill` | `{"selector": "...", "value": "..."}` | Fill form field by CSS selector |
| `/evaluate` | `{"expression": "..."}` | Evaluate arbitrary JS in page context (added Jun 16). Returns `{ok: true, result: <value>}` |
| `/info` | GET | Current page URL + title |
| `/screenshot.png` | GET | Page screenshot |

**IMPORTANT**: If `/evaluate` isn't present on the viewer, it needs to be added. The endpoint was added after initial deployment — patch `electron-viewer.js` to add it:
```javascript
// Insert before the /click-text handler:
if (req.url === '/evaluate' && req.method === 'POST') {
  let body = '';
  for await (const chunk of req) body += chunk;
  const { expression } = JSON.parse(body);
  const result = await cdp.send('Runtime.evaluate', {
    expression, returnByValue: true
  });
  res.writeHead(200, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify({ ok: true, result: result.result?.value }));
  return;
}
```

## CDP Response Structure (critical)

When using `Runtime.evaluate` with `returnByValue: true`, the response nests the value:

```json
// Response shape:
{"id": 1, "result": {"result": {"type": "string", "value": "ACTUAL_VALUE"}}}
// Access in code:
const actualValue = response.result.result.value;  // NOT response.result.value
```

For `DOM.querySelector` responses, the node ID is at:
```js
const nodeId = response.result.nodeId;  // Direct, no nesting
```

## AngularJS Forms

The `fill` endpoint dispatches `input`/`change` events but AngularJS needs model notification.

**IMPORTANT**: Setting `el.value = 'x'` on the DOM does NOT update Angular's model. Angular tracks its model separately. Validation may still fail even though the DOM shows the value.

### Method 1: Scope manipulation (preferred)
```javascript
const scope = angular.element(document.querySelector('[name="mobile"]')).scope();
scope.$apply(function() {
  scope.data.contact.mobile = 'value';
  scope.data.contact.country = 'string:AU'; // Note: "string:" prefix for selects
  scope.data.question_X = 'value'; // For custom questions
  scope.data.question_106 = {Seek: true}; // For checkbox groups (object keyed by value)
});
```

### Method 2: Direct radio/checkbox clicks
Angular radio/checkbox buttons need CLICKS, not checked=true assignment:
```javascript
// Find radio by name + value pair (values are usually numeric strings)
document.querySelector('input[type="radio"][name="question_107"][value="289"]')?.click();
// Always dispatch change event
el.dispatchEvent(new Event('change', {bubbles: true}));
```

### Method 3: Angular ngModel controller (for scope-less pages)
```javascript
const ngModel = angular.element(el).controller('ngModel');
if (ngModel) {
  ngModel.$setViewValue('new value');
  ngModel.$render();
}
```

## React/SPA Forms

### Hidden Select Elements
React often renders dropdowns as `<select>` elements with selectors like `[name="questionnaire.XXX"]`. Use `/fill`:

```bash
curl -s -X POST http://127.0.0.1:3099/fill -d '{"selector":"select[name=\\"questionnaire.AU_Q_6_V_10\\"]","value":"AU_Q_6_V_10_A_14970"}'
```

### React Full-Fill Pattern — All Input Types

For SEEK's React SPA, a single comprehensive fill function handles every input type. Use this in the Quick Apply flow after clicking QA:

```javascript
// Fill ALL form fields in one pass
(() => {
    // 1. TEXTAREAS — use native value setter (el.value = 'x' does NOT trigger React)
    document.querySelectorAll('textarea').forEach(ta => {
        if (!ta.value) {
            const ns = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
            ns.call(ta, 'Yes');
            ta.dispatchEvent(new Event('input', {bubbles: true}));
        }
    });
    // 2. SELECTS — pick first real option
    document.querySelectorAll('select').forEach(s => {
        if ((!s.value || s.value === '') && s.options.length > 1) {
            for (const o of s.options) {
                if (o.value && o.value !== '') { s.value = o.value; s.dispatchEvent(new Event('change', {bubbles: true})); break; }
            }
        }
    });
    // 3. RADIO BUTTONS — click the LABEL, not the input (React needs label clicks)
    const groups = {};
    document.querySelectorAll('input[type="radio"]').forEach(r => {
        if (r.name) { if (!groups[r.name]) groups[r.name] = []; groups[r.name].push(r); }
    });
    for (const radios of Object.values(groups)) {
        if (!radios.some(r => r.checked)) {
            const last = radios[radios.length - 1]; // Most conservative option
            const label = document.querySelector('label[for="' + last.id + '"]');
            if (label) label.click();
            else { last.checked = true; last.dispatchEvent(new Event('change', {bubbles: true})); }
        }
    }
    // 4. CHECKBOXES (privacy policy etc.) — use native setter
    document.querySelectorAll('input[type="checkbox"]').forEach(cb => {
        if (!cb.checked) {
            const ns = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'checked').set;
            ns.call(cb, true);
            cb.dispatchEvent(new Event('change', {bubbles: true}));
        }
    });
})()
```

**Why this works**: React's synthetic event system doesn't respond to direct property mutations. The native prototype setter bypasses React's value interception, and label clicks trigger React's onClick handler properly (unlike calling `.click()` on the radio input directly).

### File Uploads
Use CDP `DOM.setFileInputFiles` directly. **Must click "Upload" label first** to make the `<input type="file">` visible in the DOM:

```javascript
// Step 1: Click upload label to activate file input
await send('Runtime.evaluate', {
  expression: `[...document.querySelectorAll('label')].find(l => l.textContent.includes('Upload a resumé'))?.click() || ''`,
  returnByValue: true
});
await new Promise(r => setTimeout(r, 1000));

// Step 2: Upload file via DOM
const doc = await send('DOM.getDocument');
const query = await send('DOM.querySelector', { nodeId: doc.result.root.nodeId, selector: '#resume-fileFile' });
if (query.result.nodeId) {
  await send('DOM.setFileInputFiles', { nodeId: query.result.nodeId, files: ['/path/to/file.pdf'] });
}

// Step 3: VERIFY the upload actually took effect
await send('Runtime.evaluate', {
  expression: `document.body.innerText.substring(document.body.innerText.indexOf('Resumé'), document.body.innerText.indexOf('Resumé') + 300)`,
  returnByValue: true
});
// The verified filename should appear in the Resume section
```

**CRITICAL PITFALL**: SEEK may silently fall back to a stored profile resume even after a fresh upload. Always verify what resume name appears in the page text after upload. If the wrong filename shows, the user's stored resume was used instead.

### Clicking Radios/Checkboxes by Value
```javascript
const el = document.querySelector('input[type="radio"][name="questionnaire.X"][value="Y"]');
el.click(); el.dispatchEvent(new Event('change', {bubbles:true}));
// Then trigger Angular digest if needed
try { angular.element(el).scope().$digest(); } catch(e) {}
```

## Common Patterns

### SEEK Quick Apply Flow

**Always before submitting: show the CV to the user and ask about cover letter.** Do not default to "Don't include a cover letter" without asking — the user may want one drafted.

**Always verify what resume is actually attached.** SEEK may silently fall back to a stored profile resume after upload — check the page text for the filename.

1. Navigate to job page → click "Quick apply"
2. Upload CV: click "Upload a resume" label, wait 1-2s, then DOM.setFileInputFiles for `#resume-fileFile`
3. **WAIT 2-3 seconds** for the upload to process (the page shows "Loading..." briefly)
4. **VERIFY** the uploaded filename appears in the page text (check `document.body.innerText` for the file name)
5. **ASK THE USER** about cover letter — show CV screenshot with `vision_analyze` on the generated PDF, then ask before proceeding
6. Cover letter: click "Don't include a cover letter" label OR upload/draft one as the user specifies
7. Click "Continue" — may need 2 attempts if upload was still loading (first click validates, second submits)
8. Employer questions: fill `<select>` dropdowns + click radio/checkbox/text inputs
9. Profile step: click "Continue"
10. Review step: click "Submit application"

**Verification steps at each transition:**
```bash
curl -s http://127.0.0.1:3099/info | python3 -c "import json,sys; d=json.load(sys.stdin); print(d[0]['url'])"
```
Expected URL progression for SEEK:
```
/apply -> /apply/role-requirements -> /apply/profile -> /apply/review -> /apply/success
```

### Page Navigation Detection
```bash
curl -s http://127.0.0.1:3099/info | python3 -c "import json,sys; d=json.load(sys.stdin); print(d[0]['url'])"
```

### Screenshot for visual check
```bash
curl -s -o /tmp/check.png http://127.0.0.1:3099/screenshot.png
```

## Pitfalls

- If `/click-text` fuzzy-match hits a `<style>` element, use a more specific selector inside `main` or `[role="main"]`
- Angular `ng-invalid` persists even after `scope.$apply()` if the model didn't change — verify with `document.querySelectorAll('.ng-invalid').length`
- jQuery-less pages: the `fill` endpoint's `angular.element()` call fails silently — still dispatches standard DOM events
- File uploads: must first click "Upload" label to make the `<input type="file">` visible in DOM before `DOM.setFileInputFiles` can find it
- **File upload verification**: After uploading, SEEK may show a brief "Loading..." then revert to the user's stored profile resume. Always check the page text for which filename actually appears.
- **Cover letter**: Never default to "Don't include" — ask the user. They may want one drafted.
- **Multi-step flow patience**: SEEK's Quick Apply has 4-5 transitions (apply -> role-requirements -> profile -> review -> success). After each click, wait 4-5 seconds and verify the URL before proceeding.
- **SEEK text inputs use indirect names**: Fields are named `questionnaire.indirect_<uuid>`. Find them by selector `input[name^="questionnaire.indirect"]` and fill via `/fill` endpoint.
- **SEEK role-requirements validation**: Read `document.body.innerText` for "Before you can continue with the application" to find which fields are still required.
- Timeouts on CDP `send()` commands are common during page transitions — just retry or check via info endpoint
- **Zero-width characters in button text**: SEEK's React UI sprinkles U+2060 (WORD JOINER) characters inside button text. `"Continue⁠"` is actually `"Continue\u2060"`. The `/click-text` fuzzy-match handles this, but when using `Runtime.evaluate` to find buttons, strip zero-width chars or use `textContent.includes('Continue')` instead of `===`:
  ```javascript
  // DON'T:
  if (b.textContent.trim() === 'Continue')
  // DO:
  if (b.textContent.replace(/[\\u200B-\\u200D\\uFEFF\\u2060]/g, '').trim() === 'Continue')
  // Or simpler:
  if (b.textContent.includes('Continue'))
  ```
- **SEEK React form fields use DOM IDs not Angular names**: Unlike the older Angular SEEK forms, the new React SPA uses `<select id="question-AU_Q_6_V_10" name="questionnaire.AU_Q_6_V_10">`. Access via `document.getElementById()` is more reliable than name selectors.
- **Resume is pre-selected via URL UUID on SEEK's new React UI**: After clicking Quick Apply, the `<select data-testid="select-input">` already has a resume UUID value pre-selected. You don't need to upload — just verify the value is non-empty and click Continue. The page may still show "Please select a resumé" as placeholder text even though the value is set.

## Pitfalls (continued)

- **Resume selection ambiguity**: When SEEK lists multiple stored resumes, clicking "Select a resume" opens a dropdown but the uploaded file may not override the stored selection. Explicitly verify.
- **Angular radio/checkbox registration**: Setting `checked = true` on an Angular input does not update the model. You must call `.click()` or `angular.element(input).controller('ngModel').$setViewValue(true)`.

## References

- `references/session-2026-06-16-job-applications-round2.md` — second batch of 11 Quick Apply submissions, React SPA form handling learnings, native value setter patterns.
- `references/job-portal-blocking-patterns.md` — which portals work from container vs. need Tandem (SEEK, LinkedIn, amazon.jobs, Workday, Elmo). Use this to determine the right approach per portal before starting.
- `references/seek-quick-apply-patterns.md` — detailed SEEK form field IDs, Angular patterns, and fill strategies.
- `templates/seek-batch-apply.py` — reusable Python script for batch-processing multiple SEEK Quick Apply jobs. Edit the JOBS list in the script and run.
