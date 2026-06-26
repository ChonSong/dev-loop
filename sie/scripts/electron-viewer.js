#!/usr/bin/env node
/**
 * Electron Viewer v2 — connects to the Tandem Electron app's CDP
 * and serves a screenshot viewer WITHOUT navigating any existing page.
 * Shares the same session/cookies as the user.
 */
const http = require('http');
const WebSocket = require('ws');

const CDP_URL = 'http://127.0.0.1:9222';
const VIEWER_PORT = 3099;

// ── CDP session ──
class CDPSession {
  constructor(ws) {
    this.ws = ws;
    this.id = 0;
    this.pending = new Map();
  }

  static async connect(pageTarget) {
    const ws = new WebSocket(pageTarget.webSocketDebuggerUrl);
    await new Promise((resolve, reject) => {
      ws.on('open', resolve);
      ws.on('error', reject);
    });
    const session = new CDPSession(ws);
    ws.on('message', (data) => session._onMessage(data));
    return session;
  }

  _onMessage(data) {
    try {
      const msg = JSON.parse(data.toString());
      if (msg.id && this.pending.has(msg.id)) {
        this.pending.get(msg.id)(msg);
        this.pending.delete(msg.id);
      }
    } catch (e) {
      console.error('[CDP] Parse error:', e.message);
    }
  }

  async send(method, params = {}) {
    const id = ++this.id;
    this.ws.send(JSON.stringify({ id, method, params }));
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        this.pending.delete(id);
        reject(new Error(`CDP timeout: ${method}`));
      }, 15000);
      this.pending.set(id, (msg) => {
        clearTimeout(timer);
        if (msg.error) reject(new Error(msg.error.message));
        else resolve(msg.result);
      });
    });
  }
}

// ── Main ──
async function main() {
  console.log('[Viewer] Connecting to Electron CDP...');

  // Get all page targets
  const res = await fetch(`${CDP_URL}/json`);
  const targets = await res.json();
  const pages = targets.filter(t => t.type === 'page');
  
  if (pages.length === 0) throw new Error('No page targets found');

  // Find a webview target (user's tabs), not the main shell page
  // Webviews share cookies with the main Tandem session
  const webview = pages.find(p => p.type === 'webview')
    || pages.find(p => p.url.includes('newtab.html'))
    || pages.find(p => p.url.startsWith('file://'))
    || pages[0];
  
  console.log('[Viewer] Targeting webview:', webview.title, webview.url);

  // Connect to this webview WITHOUT navigating
  const cdp = await CDPSession.connect(webview);
  await cdp.send('Page.enable');
  await cdp.send('DOM.enable');
  
  // Don't navigate — just observe

  console.log('[Viewer] Connected — observing page without navigating');

  // HTTP server
  const server = http.createServer(async (req, res) => {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') {
      res.writeHead(204);
      res.end();
      return;
    }

    try {
      if (req.url === '/screenshot.png') {
        const result = await cdp.send('Page.captureScreenshot', { format: 'png', fromSurface: true });
        const img = Buffer.from(result.data, 'base64');
        res.writeHead(200, {
          'Content-Type': 'image/png',
          'Content-Length': img.length,
          'Cache-Control': 'no-cache, no-store, must-revalidate',
        });
        res.end(img);
        return;
      }

      if (req.url === '/info') {
        const fetchRes = await fetch(`${CDP_URL}/json`);
        const allTargets = await fetchRes.json();
        const info = allTargets.filter(t => t.type === 'page' || t.type === 'webview').map(t => ({
          id: t.id, title: t.title, url: t.url
        }));
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(info));
        return;
      }

      if (req.url === '/navigate' && req.method === 'POST') {
        let body = '';
        for await (const chunk of req) body += chunk;
        const { url } = JSON.parse(body);
        await cdp.send('Page.navigate', { url });
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true }));
        return;
      }

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

      if (req.url === '/fill' && req.method === 'POST') {
        let body = '';
        for await (const chunk of req) body += chunk;
        const { selector, value } = JSON.parse(body);
        const result = await cdp.send('Runtime.evaluate', {
          expression: `(() => {
            const el = document.querySelector('${selector.replace(/'/g, "\\'")}');
            if (!el) return JSON.stringify({error: 'not found'});
            const tag = el.tagName.toLowerCase();
            if (tag === 'select') {
              el.value = '${value.replace(/'/g, "\\'")}';
              el.dispatchEvent(new Event('change', {bubbles:true}));
            } else {
              el.value = '${value.replace(/'/g, "\\'")}';
              el.dispatchEvent(new Event('input', {bubbles:true}));
              el.dispatchEvent(new Event('change', {bubbles:true}));
            }
            // Notify Angular
            try { angular.element(el).triggerHandler('input'); angular.element(el).triggerHandler('change'); } catch(e) {}
            return JSON.stringify({ok: true, tag: tag});
          })()`,
          returnByValue: false
        });
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, result: 'filled' }));
        return;
      }

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

      if (req.url === '/click-text' && req.method === 'POST') {
        let body = '';
        for await (const chunk of req) body += chunk;
        const { text } = JSON.parse(body);
        await cdp.send('Runtime.evaluate', {
          expression: `(() => {
            const btns = Array.from(document.querySelectorAll('button, a, input[type="submit"], [role="button"]'));
            const target = btns.find(b => (b.textContent || b.value || '').trim() === '${text.replace(/'/g, "\\'")}');
            if (target) { target.scrollIntoView(); target.click(); return 'CLICKED'; }
            // Try contains
            const fuzzy = btns.find(b => (b.textContent || b.value || '').trim().includes('${text.replace(/'/g, "\\'")}'));
            if (fuzzy) { fuzzy.scrollIntoView(); fuzzy.click(); return 'CLICKED_FUZZY'; }
            return 'NOT FOUND';
          })()`,
          returnByValue: true
        });
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, result: 'clicked' }));
        return;
      }

      // Serve viewer HTML
      res.writeHead(200, { 'Content-Type': 'text/html' });
      res.end(`<!DOCTYPE html>
<html><head><title>Electron Viewer</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#1a1a2e;color:#e0e0e0;font-family:system-ui,sans-serif;display:flex;flex-direction:column;height:100vh}
.toolbar{display:flex;gap:8px;padding:8px 16px;background:#16213e;align-items:center;border-bottom:1px solid #0f3460;flex-shrink:0}
.toolbar input{flex:1;padding:8px 12px;border:1px solid #0f3460;border-radius:6px;background:#1a1a2e;color:#e0e0e0;font-size:14px}
.toolbar button{padding:8px 16px;border:none;border-radius:6px;background:#e94560;color:white;cursor:pointer;font-weight:600}
.toolbar button:hover{background:#c73650}
.toolbar .title{font-size:12px;color:#888;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:200px}
.viewer{flex:1;display:flex;align-items:center;justify-content:center;background:#0d0d1a;overflow:hidden;padding:4px}
.viewer img{max-width:100%;max-height:100%;border-radius:4px;cursor:crosshair}
.statusbar{padding:4px 16px;background:#16213e;font-size:11px;color:#666;border-top:1px solid #0f3460;display:flex;justify-content:space-between;flex-shrink:0}
</style></head><body>
<div class="toolbar">
  <form style="flex:1;display:flex;gap:6px" onsubmit="navigate(event)">
    <input type="url" id="urlInput" placeholder="URL..." value="about:blank">
    <button type="submit">Go</button>
  </form>
  <span class="title" id="pageTitle">—</span>
  <button onclick="refresh()">⟳</button>
</div>
<div class="viewer">
  <img id="screenshot" src="/screenshot.png" alt="Viewer">
</div>
<div class="statusbar"><span id="status">Connected to Electron</span><span id="urlDisplay">—</span></div>
<script>
const img=document.getElementById('screenshot'),input=document.getElementById('urlInput'),title=document.getElementById('pageTitle'),urlD=document.getElementById('urlDisplay');
setInterval(()=>{img.src='/screenshot.png?'+Date.now()},2000);
async function navigate(e){e?.preventDefault();await fetch('/navigate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url:input.value})});refresh()}
async function refresh(){img.src='/screenshot.png?'+Date.now();try{const r=await fetch('/info');const pages=await r.json();if(pages.length){input.value=pages[0].url;title.textContent=pages[0].title;urlD.textContent=pages[0].url}}catch(e){}}
img.onclick=async(e)=>{const rect=img.getBoundingClientRect();const x=(e.clientX-rect.left)*(img.naturalWidth/rect.width||1);const y=(e.clientY-rect.top)*(img.naturalHeight/rect.height||1);await fetch('/click',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({x,y})});setTimeout(refresh,500)};
refresh();setInterval(refresh,5000);
</script></body></html>`);
    } catch (e) {
      console.error('[HTTP] Error:', e.message);
      res.writeHead(500, { 'Content-Type': 'text/plain' });
      res.end('Error: ' + e.message);
    }
  });

  server.listen(VIEWER_PORT, () => {
    console.log(`[Viewer] Electron viewer at http://localhost:${VIEWER_PORT}`);
    console.log(`[Viewer] Same session as Tandem Electron — observing without navigating`);
  });
}

main().catch(e => {
  console.error('[Fatal]', e);
  process.exit(1);
});
