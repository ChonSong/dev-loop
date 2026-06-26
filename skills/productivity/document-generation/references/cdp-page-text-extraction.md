# CDP Page Text Extraction

When a job listing or career portal uses JavaScript SPAs (like Elmo Talent
or Workday), curl and browser snapshots often can't extract the full text.
Use the Chrome DevTools Protocol (CDP) WebSocket to run JavaScript directly
in the page context.

## Prerequisites

- Chrome running with `--remote-debugging-port=9222` (or equivalent Electron
  process listening on that port)
- `ws` npm package installed

## Setup

```bash
npm install ws
```

## Pattern

```javascript
// connect-cdp-and-extract.mjs
import WebSocket from 'ws';

const CDP_URL = 'http://127.0.0.1:9222';

async function main() {
  // 1. Get page targets
  const res = await fetch(`${CDP_URL}/json`);
  const targets = await res.json();
  const target = targets.find(t => t.type === 'page');

  // 2. Connect via WebSocket
  const ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise(r => ws.on('open', r));
  let id = 0;
  const pending = new Map();

  ws.on('message', d => {
    const m = JSON.parse(d.toString());
    if (m.id !== undefined && pending.has(m.id)) {
      pending.get(m.id)(m);
      pending.delete(m.id);
    }
  });

  // 3. Helper to send CDP commands
  const send = (method, params = {}) => new Promise((resolve, reject) => {
    const mid = ++id;
    pending.set(mid, resolve);
    ws.send(JSON.stringify({ id: mid, method, params }));
    setTimeout(() => { if (pending.has(mid)) { pending.delete(mid); reject('timeout'); } }, 15000);
  });

  // 4. Navigate to target page
  await send('Page.navigate', { url: 'https://example.com/careers/job/123' });
  await new Promise(r => setTimeout(r, 4000));

  // 5. Extract page text via Runtime.evaluate
  const result = await send('Runtime.evaluate', {
    expression: `document.body.innerText`,
    returnByValue: true
  });

  // 6. Parse the response
  // CDP response shape: {id, result: {result: {type, value}}}
  const text = result?.result?.result?.value || '';
  console.log(text);

  ws.close();
}
main().catch(e => console.error('Err:', e.message));
```

## Finding Links in SPAs

Elmo Talent, Workday, and similar portals render job links as JavaScript-
managed elements, not plain `<a href>` tags. To find job URLs:

```javascript
// Get all <a> elements and filter for job-related ones
const r = await send('Runtime.evaluate', {
  expression: `(() => {
    const links = document.querySelectorAll('a');
    return JSON.stringify(
      Array.from(links)
        .filter(a => a.href && a.textContent.trim())
        .slice(0, 20)
        .map(a => ({href: a.href, text: a.textContent.trim().substring(0, 60)}))
    );
  })()`,
  returnByValue: true
});
const links = JSON.parse(r?.result?.result?.value || '[]');
```

The response includes `{href, text}` pairs. Job links often follow patterns
like `/careers/job/view/{id}` (Elmo) or `/job/{Requisition-ID}` (Workday).

## Known Job Portal URL Patterns

| Portal | URL Pattern | Example |
|--------|------------|---------|
| Elmo Talent | `{base}/careers/job/view/{id}` | `https://ngssuper.elmotalent.com.au/careers/careers/job/view/160` |
| Workday | `{base}/job/{location}/{Req-ID}` | `https://wehi.wd3.myworkdayjobs.com/en-US/WEHI/job/Parkville/Junior-Research-Data-Engineer_JR3743` |

## Pitfalls

- **Result value access:** CDP `Runtime.evaluate` with `returnByValue: true`
  returns the value at `result.result.value` (nested `.result`), NOT at
  `result.value` directly. Log the full response to debug.
- **Page navigation timeout:** The CDP session can time out during
  `Page.navigate` if the page is slow or never fires the expected event.
  Use a generous `setTimeout` after navigating.
- **Cross-origin restrictions:** Runtime.evaluate runs in the page context
  and cannot access iframe content. For Google sign-in buttons rendered in
  iframes (GSI), CDP mouse clicks at iframe coordinates can work.
- **Target selection:** Electron apps (Tandem Browser) may have both `page`
  and `webview` type targets. For SPA content, prefer the `page` target
  when available; `webview` targets may not support all CDP commands.
