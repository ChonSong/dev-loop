# CDP via Native Node WebSocket — No `npm install` Required

When the container has no working Chromium but you can SSH to a host that does, this is the cleanest runtime-testing recipe. Node 22+ ships a built-in `WebSocket` global, so you don't need the `ws` npm package. The whole script lives in a single `.mjs` file you can `scp` to the host and run.

## Why this beats the CLI flags

- `--screenshot` is buggy in Chrome 143+ (writes IHDR but no IDAT chunks — empty/corrupt PNGs).
- `--print-to-pdf` works but requires a vision model to interpret the PDF, and lacks easy DOM inspection.
- The CDP recipe gives you: real screenshots via `Page.captureScreenshot`, full DOM inspection via `Runtime.evaluate`, and **event-driven capture of every uncaught exception** via `Runtime.exceptionThrown`. The exception capture is the killer feature — you find bugs the CLI flags can't surface.

## The host side

For the hermes-webui container:
- **Host IP**: `172.19.0.1` (Docker bridge — `localhost` is refused)
- **SSH key**: `/home/hermeswebui/.hermes/container_key`
- **SSH user**: `sean@172.19.0.1`
- **Chrome binary**: `/opt/google/chrome/chrome`
- **Node binary**: `/usr/bin/node` (v22+ has native `WebSocket`)

## Common pitfall: which WebSocket to connect to

`http://127.0.0.1:PORT/json/version` gives you the **browser-wide** WebSocket. That one does NOT have `Page.enable` (you'll get `'Page.enable' wasn't found`). The right target is a **page target** — get it from `http://127.0.0.1:PORT/json/list` and find the one with `type === 'page'`.

## Full working template (debug a live web page)

```javascript
import { spawn } from 'node:child_process';
import { setTimeout as sleep } from 'node:timers/promises';
import http from 'node:http';
import fs from 'node:fs';

const URL = 'https://example.com/';
const CHROME = '/opt/google/chrome/chrome';
const PORT = 9876;
const PROFILE = '/tmp/chrome-test-' + Date.now();
fs.rmSync(PROFILE, { recursive: true, force: true });

const REPORT = { url: URL, console: [], errors: [] };

const chrome = spawn(CHROME, [
  '--headless=new', '--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage',
  '--hide-scrollbars', '--incognito', '--disable-cache',
  '--remote-debugging-port=' + PORT,
  '--user-data-dir=' + PROFILE,
  '--window-size=1440,900',
], { stdio: ['ignore', 'pipe', 'pipe'] });

chrome.stderr.on('data', d => process.stderr.write('[chrome] ' + d));

async function getPageWsUrl() {
  for (let i = 0; i < 60; i++) {
    try {
      const r = await new Promise((res, rej) => {
        http.get('http://127.0.0.1:' + PORT + '/json/list', resp => {
          let body = '';
          resp.on('data', c => body += c);
          resp.on('end', () => res(JSON.parse(body)));
        }).on('error', rej);
      });
      const page = r.find(t => t.type === 'page');
      if (page) return page.webSocketDebuggerUrl;
    } catch (e) {}
    await sleep(500);
  }
  throw new Error('No page target');
}

const wsUrl = await getPageWsUrl();
const ws = new WebSocket(wsUrl);
await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });

let id = 0;
const pending = new Map();
ws.addEventListener('message', ev => {
  const m = JSON.parse(ev.data);
  if (m.id != null && pending.has(m.id)) {
    pending.get(m.id)(m);
    pending.delete(m.id);
    return;
  }
  if (m.method === 'Runtime.consoleAPICalled') {
    const args = (m.params.args || []).map(a =>
      a.value ?? a.description ?? JSON.stringify(a));
    REPORT.console.push({ type: m.params.type, text: args.join(' ') });
  } else if (m.method === 'Runtime.exceptionThrown') {
    const e = m.params.exceptionDetails;
    REPORT.errors.push({
      msg: e.exception?.description || e.text,
      text: e.text,
      line: e.lineNumber, col: e.columnNumber, url: e.url,
      stack: e.stackTrace?.callFrames?.map(
        f => `${f.functionName || '<anon>'} @ ${f.url}:${f.lineNumber}:${f.columnNumber}`
      ).join('\n'),
    });
  } else if (m.method === 'Network.responseReceived') {
    if (m.params.response.status >= 400) {
      REPORT.responses_error = REPORT.responses_error || [];
      REPORT.responses_error.push({
        url: m.params.response.url,
        status: m.params.response.status,
      });
    }
  }
});

function send(method, params = {}) {
  return new Promise((res, rej) => {
    const i = ++id;
    pending.set(i, m => m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result));
    ws.send(JSON.stringify({ id: i, method, params }));
  });
}

await send('Network.setCacheDisabled', { cacheDisabled: true });
await send('Page.enable');
await send('Page.navigate', { url: URL });
await sleep(12000); // give CDN scripts + inline JS time to settle

// Inspect DOM state, count elements, read globals
const info = await send('Runtime.evaluate', {
  expression: `JSON.stringify({
    title: document.title,
    canvasCount: document.querySelectorAll('canvas').length,
    bodyChildren: document.body.childElementCount,
    // any globals you care about
    nodes: typeof nodes !== 'undefined' ? nodes.length : 'undef',
    edges: typeof edges !== 'undefined' ? edges.length : 'undef',
  }, null, 2)`,
  returnByValue: true,
});

const shot = await send('Page.captureScreenshot', { format: 'png' });
fs.writeFileSync('/tmp/screenshot.png', Buffer.from(shot.data, 'base64'));

console.log('TITLE:', JSON.parse(info.result.value).title);
console.log('CONSOLE (' + REPORT.console.length + '):');
REPORT.console.forEach(c => console.log('  [' + c.type + ']', c.text.slice(0, 300)));
console.log('ERRORS (' + REPORT.errors.length + '):');
REPORT.errors.forEach(e => {
  console.log('  EXCEPTION:', e.msg);
  console.log('   at:', e.url + ':' + e.line + ':' + e.col);
  if (e.stack) console.log('  stack:\n    ' + e.stack.split('\n').join('\n    '));
});

chrome.kill();
process.exit(0);
```

## Run it on the host

```bash
# From the container
scp -i /home/hermeswebui/.hermes/container_key test.mjs sean@172.19.0.1:/tmp/test.mjs
ssh -i /home/hermeswebui/.hermes/container_key sean@172.19.0.1 "cd /tmp && node test.mjs"

# Pull screenshots back
scp -i /home/hermeswebui/.hermes/container_key sean@172.19.0.1:/tmp/screenshot.png /workspace/
```

## Iteration loop (for GitHub-Pages hosted fixes)

1. `git add` + `git commit` + `git push` from the container.
2. Wait 15-20s for GitHub Pages to rebuild.
3. Re-run the script. Pass `?v=` cache buster to the URL (`'https://example.com/?v=' + Date.now()`).
4. Use `--incognito --disable-cache` + `Network.setCacheDisabled({ cacheDisabled: true })` — even with all three, Chrome can still cache inline scripts in memory. The `?v=` query string is the most reliable cache buster.
5. Re-test until `ERRORS (0)`.

## When to fall back to a subagent

If you need visual confirmation via a vision-capable model and the host has no vision model available, delegate the screenshot analysis:

```python
delegate_task(
  goal='Open /workspace/screenshot.png and describe any visual bugs, blank areas, or rendering issues.',
  toolsets=['vision', 'file'],
)
```

The subagent can also do the CDP work itself if you give it the recipe above plus `toolsets=['terminal', 'file']` (it'll need to write the script to a file the host can see, or scp the file).

## Why not just `delegate_task(toolsets=['browser'])`?

It works, but the subagent returns a self-reported summary. The CDP recipe gives you:
- Raw event capture you can grep programmatically
- The exact line number of every exception
- A screenshot file you can `scp` back and inspect yourself
- A `REPORT` JSON you can diff between runs

For one-shot triage, the subagent is fine. For a fix-deploy-retest loop, the CDP recipe wins.
