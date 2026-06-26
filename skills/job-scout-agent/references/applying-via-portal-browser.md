# Applying via Portal Browser (Tandem Electron CDP)

When company career portals block the container IP (Cloudflare, etc.) or require interactive form filling with client-side validation, use the **Tandem shared browser** — an Electron app running on the host that shares the user's browser session and cookies.

## Architecture

```
User's Desktop                 Hermes Container
┌─────────────────────┐       ┌──────────────────────┐
│  Tandem Browser      │       │  electron-viewer.js   │
│  (Electron App)      │◄─────►│  (Node server)        │
│  - real Chrome       │ CDP   │  - port 3099          │
│  - user logged in    │ 9222  │  - screenshot viewer  │
│  - has cookies       │       │  - fill/click/navigate │
└─────────────────────┘       └──────────────────────┘
```

The `electron-viewer.js` at `/home/sc/.hermes/scripts/electron-viewer.js` connects to the Electron app's Chrome DevTools Protocol (CDP) at port 9222 and exposes an HTTP API.

## API Endpoints (port 3099)

| Endpoint | Method | Body | Purpose |
|----------|--------|------|---------|
| `/screenshot.png` | GET | — | Returns current page screenshot |
| `/info` | GET | — | JSON: current page title + URL |
| `/navigate` | POST | `{"url": "..."}` | Navigate to URL |
| `/click` | POST | `{"x": N, "y": N}` | Click at pixel coordinates |
| `/fill` | POST | `{"selector": "[name=x]", "value": "..."}` | Fill form field by CSS selector, dispatches input/change events + Angular triggerHandler |
| `/click-text` | POST | `{"text": "Button Text"}` | Click button/link by exact text match (with fuzzy fallback) |

## Starting/Restarting the Viewer

```bash
kill $(lsof -ti :3099) 2>/dev/null; sleep 1
node /home/sc/.hermes/scripts/electron-viewer.js > /tmp/electron-viewer.log 2>&1
```
The first start requires `ws` to be installed at `/home/sc/.hermes/scripts/node_modules/ws` (npm init + npm install ws).

## SEEK Quick Apply Automation

SEEK's Quick Apply flow is a multi-step React form. Unlike Angular portals, SEEK updates its model on DOM events, so standard `element.value` + `dispatchEvent` works — but the flow has specific timing requirements.

### Full Workflow

```
Job Page → Quick Apply → Upload/Select CV → Cover Letter → Continue → 
Role Requirements (selects) → Continue → Profile → Continue → 
Review → Submit application
```

### Step-by-Step

**1. Navigate to job page:**
```
curl -s -X POST http://127.0.0.1:3099/navigate \
  -H "Content-Type: application/json" \
  -d '{"url":"https://au.seek.com/job/JOB_ID"}'
```

**2. Click "Quick apply":**
```
curl -s -X POST http://127.0.0.1:3099/click-text \
  -H "Content-Type: application/json" \
  -d '{"text":"Quick apply"}'
```
Wait 4-5 seconds for the apply page to load.

**3. Upload CV via CDP** (not via the HTTP endpoint — SEEK's React form needs the DOM file input):
```js
// First click "Upload a resumé" label to activate the hidden file input
await send('Runtime.evaluate', {
  expression: `[...document.querySelectorAll('label')].find(l => l.textContent.includes('Upload a resumé'))?.click() || ''`,
  returnByValue: true
});
await new Promise(r => setTimeout(r, 1000));

// Then upload via DOM.setFileInputFiles
const doc = await send('DOM.getDocument');
const q = await send('DOM.querySelector', {
  nodeId: doc.result.root.nodeId,
  selector: '#resume-fileFile'
});
await send('DOM.setFileInputFiles', {
  nodeId: q.result.nodeId,
  files: ['/absolute/path/to/cv.pdf']
});
await new Promise(r => setTimeout(r, 2000));
```

**4. Select "Don't include a cover letter":**
```js
await send('Runtime.evaluate', {
  expression: `[...document.querySelectorAll('label')].find(l => l.textContent.includes("Don't include a cover letter"))?.click() || ''`,
  returnByValue: true
});
```

**5. Click "Continue" — may need 2 attempts** (first triggers validation/upload, second navigates):
```js
await send('Runtime.evaluate', {
  expression: `[...document.querySelectorAll('button')].find(b => b.textContent.trim() === 'Continue')?.click() || ''`,
  returnByValue: true
});
await new Promise(r => setTimeout(r, 4000));
// Check URL — if still /apply, click Continue again
```

**6. Role requirements step** (if URL contains `/role-requirements`):
```js
// Discover all select elements
const selects = await send('Runtime.evaluate', {
  expression: `JSON.stringify(Array.from(document.querySelectorAll('select')).map(s => ({name: s.name, options: Array.from(s.options).slice(0,3).map(o => ({value: o.value, text: o.text.trim().substring(0,30)}))})))`,
  returnByValue: true
});

// Set each select to its first valid option (usually "Australian citizen" or "No experience")
await send('Runtime.evaluate', {
  expression: `(() => {
    document.querySelectorAll('select').forEach(s => {
      const opt = Array.from(s.options).find(o => o.value && o.value.length > 0);
      if (opt) { s.value = opt.value; s.dispatchEvent(new Event('change', {bubbles:true})); }
    });
  })()`,
  returnByValue: true
});

// Click Continue
await send('Runtime.evaluate', {
  expression: `[...document.querySelectorAll('button')].find(b => b.textContent.trim() === 'Continue')?.click() || ''`,
  returnByValue: true
});
```

**7. Profile step** (if URL contains `/profile`): just click Continue.

**8. Review and Submit** (URL contains `/review`):
```js
await send('Runtime.evaluate', {
  expression: `[...document.querySelectorAll('button')].find(b => b.textContent.trim() === 'Submit application')?.click() || ''`,
  returnByValue: true
});
```

**9. Confirm success** (URL ends with `/apply/success`).

### Common SEEK Form Patterns

| Component | Discovery Method | Example |
|-----------|-----------------|---------|
| Resume file input | `#resume-fileFile` | Must click "Upload a resumé" label first |
| Cover letter radios | Labels containing "Don't include" | Click the label text |
| Right-to-work select | `select[name="questionnaire.AU_Q_6_V_10"]` | 11 options, first valid is Australian citizen |
| Experience selects | Various dynamic names like `AU_Q_6A8ACDCD..._V_1` | 8-9 options from No exp to 5+ years |
| AWS/Skills radios | `input[name="questionnaire.AU_Q_..."][value="..."]` | Click by name+value selector |
| Continue button | Exact text "Continue" | May need 2 clicks |
| Submit button | Exact text "Submit application" | On review page |

### Important: CV Upload Verification

**SEEK may silently revert to a stored resume from the user's profile** instead of using the newly uploaded file. After `DOM.setFileInputFiles`, always verify:

```js
const cvStatus = await send('Runtime.evaluate', {
  expression: `(() => {
    const text = document.body.innerText;
    const resumeSection = text.substring(text.indexOf('Resumé'), text.indexOf('Resumé') + 300);
    return resumeSection;
  })()`,
  returnByValue: true
});
console.log('CV status:', cvStatus.result.result.value);
```

Check that the uploaded filename appears. If the page still shows "Please select a resumé" or an older filename, the upload didn't take — retry.

### User Preference: Screenshot Before Submit

**Always take a screenshot of the review page and show it to the user before hitting Submit.** This lets them verify the correct CV is attached and details are right. Screenshots via:
```
curl -s -o /tmp/review-screenshot.png http://127.0.0.1:3099/screenshot.png
```
Then embed with `MEDIA:/tmp/review-screenshot.png`.

## Bypassing Cloudflare

The Tandem Electron app runs on the user's desktop with a real browser fingerprint. Cloudflare challenges resolve in their browser window. The electron-viewer simply mirrors and controls what's visible there. This is the only reliable way to access SEEK and other Cloudflare-protected job boards from the container.

## Amazon.jobs Portal

Amazon.jobs uses `passport.amazon.jobs` for authentication. It's heavily protected against automated access.

### Login Methods

| Method | Works? | Notes |
|--------|--------|-------|
| Amazon.jobs email/password | ✅ Direct form | Fields visible on login page |
| Login with Amazon (Amazon.com account) | ❓ Untested | JS-handled click, likely same popup issue |
| Login with Google | ❌ Blank page | JS-handled click opens about:blank — popup blocked in headless/Electron context |
| Login with Apple / LinkedIn | ❓ Untested | Likely same popup issue |

Both "Login with Google" and "Login with Amazon" links have empty `href` attributes — they use JS event handlers that open authentication popups. These popups are blocked or fail silently in the Tandem Electron browser, leaving the page at `about:blank`.

### Registration

Accessible at `passport.amazon.jobs/createaccount`. The "Create an Amazon.jobs account" link on the login page has `href="/createaccount"` (a real navigation link, unlike the OAuth buttons).

Registration requires:
- Email address
- Password (8+ chars, upper+lower+number+special)
- Confirm password
- **CAPTCHA** — a numeric puzzle: buttons 1-9 with a canvas showing the challenge

### CAPTCHA Types Encountered

| Context | Type | Description |
|---------|------|-------------|
| Registration (`/createaccount`) | Numeric puzzle | Buttons 1-9, canvas, "Confirm" button |
| Post-login confirmation (`/social/lwg/confirm`) | 6-image grid | Clock images, "Confirm"/"Continue" buttons |

### Session Expiry

The `passport.amazon.jobs/social/lwg/confirm` URL expires after a short time. Once expired, it returns **"400 Missing Parameter"** error. Recovery requires a full restart:
1. Navigate back to the job listing on `www.amazon.jobs/en/jobs/<ID>/`
2. Click "Apply now" to trigger the auth flow again
3. Re-authenticate and reach the CAPTCHA page

### Browser Detection Warning

Amazon.jobs displays an alert banner: *"If you're experiencing issues with our website, please try upgrading your current browser or use a different browser."* This suggests aggressive user-agent or capability detection that may interfere with Electron/headless sessions.

### Application Flow

```
Job listing (amazon.jobs/en/jobs/<ID>)
  → Click "Apply now"
  → Login / Register (passport.amazon.jobs)
  → CAPTCHA challenge
  → Confirm email (post-CAPTCHA)
  → Application form (AWS portal, not Amazon.jobs)
  → CV upload → Submit
```

### Handling OAuth Popup Blocking

Since Google/Amazon OAuth popups fail in the Tandem browser, prefer:
1. **Create an Amazon.jobs account** via `/createaccount` (direct navigation, works with email/password)
2. This requires the user to solve the numeric CAPTCHA on the Tandem viewer
3. Once logged in, the apply flow goes through

### Direct Navigation URLs

| Purpose | URL |
|---------|-----|
| Login | `passport.amazon.jobs/` |
| Registration | `passport.amazon.jobs/createaccount` |
| Job listing | `www.amazon.jobs/en/jobs/<JOB_ID>/<slug>` |

## Filling Angular Forms via CDP

AngularJS forms (like the NGS Super Elmo portal) do NOT update their model when you set `element.value` directly. The framework needs its digest cycle triggered.

### Technique: Direct Click by Value

Radio buttons and checkboxes in Angular forms often have no `id` attribute. Find them by `name` + `value`:

```js
// Find and click a radio button by name + value
const el = document.querySelector('input[name="question_107"][value="289"]');
el.click();
el.dispatchEvent(new Event('change', {bubbles: true}));

// Then trigger Angular digest
const scope = angular.element(document.querySelector('[name="mobile"]')).scope();
scope.$digest();
```

### Technique: Scope.$apply for Model Values

When you know the scope structure, set values directly:

```js
const scope = angular.element(document.querySelector('[name="mobile"]')).scope();
scope.$apply(function() {
    scope.data.contact.mobile = '0434968983';
    scope.data.contact.country = 'string:AU';  // Note: prefix for Angular select options
    scope.data.question_96 = 'string:4';       // Select option values
});
```

### Technique: Finding All Radio/Checkbox Values

```js
document.querySelectorAll('input[type="radio"], input[type="checkbox"]').forEach(el => {
    console.log(el.name, el.value, el.checked);
});
```

### Technique: Programmatic Form Submission

When clicking the "Submit" button doesn't work (Angular ng-submit not triggered):

```js
const scope = angular.element(document.querySelector('[ng-controller]')).scope();
scope.$apply(function() { scope.submitApplication(); });
```

### Technique: Field Discovery

To find all form fields with their metadata:

```js
document.querySelectorAll('input:not([type=hidden]), select, textarea').forEach(el => {
    const label = document.querySelector('label[for="' + el.id + '"]');
    console.log({
        name: el.name,
        id: el.id,
        type: el.type || el.tagName,
        placeholder: el.placeholder,
        label: label ? label.textContent.trim() : '(no label)'
    });
});
```

## Common Pitfalls

- **Country select values have `string:` prefix** — AngularJS formats select option values as `string:AU`, not bare `AU`.
- **Radio buttons often lack `id` attributes** — you can't click by `label[for]`. Use `input[name="x"][value="y"]` selector.
- **`querySelector('[name="question_106[]"]')` works** — bracket characters in name attributes are fine in selector strings.
- **The `/click-text` endpoint uses text content matching** — it scrolls to and clicks the first matching button. For Submit buttons on step 3, the scope method (`scope.submitApplication()`) is more reliable than button clicks when Angular doesn't propagate the event.
- **CDP WebSocket connections need proper cleanup** — always call `ws.close()` to avoid resource leaks. A hanging connection blocks subsequent CDP commands.
- **The `pending` Map must use `delete(msg.id)`** not `delete pending.get(msg.id)` — the latter is a no-op in JS.
- **SEEK Quick Apply Continue button may need 2 clicks** — first click triggers validation/upload processing, second navigates to the next step. Always check the URL after clicking Continue.
- **SEEK role-requirements selects have dynamic names** — don't hardcode selector names. Discover them with `document.querySelectorAll('select')` and set each to its first valid option.
- **Always verify the CV actually uploaded on SEEK** — the uploaded filename should appear in the page text. If it still shows "Please select a resumé", the upload failed silently.
