# Chrome 143 Screenshot Workarounds

## The Bug

Chrome 143.0.7499.40 (headless) has a bug where `--screenshot` writes a PNG file with IHDR (image header) but no IDAT chunks (actual pixel data). The file is always exactly ~21,646 bytes regardless of viewport size. It cannot be opened or decoded.

**Symptom**: `python3 -c "import struct; open('file.png','rb')..."` shows `INVALID PNG - no IDAT data`.

## Fix A: `--dump-dom --screenshot` combo (most reliable)

```bash
google-chrome-stable --headless --disable-gpu \
  --dump-dom --screenshot=/tmp/page.png \
  --window-size=1600,900 <url> >/dev/null 2>&1
```

Adding `--dump-dom` forces Chrome to complete the paint cycle before writing the file. The `--dump-dom` output is sent to stdout — redirect to `/dev/null`.

## Fix B: `--print-to-pdf` (always works)

```bash
google-chrome-stable --headless --disable-gpu \
  --print-to-pdf=/tmp/page.pdf \
  --window-size=1600,900 <url>
```

Produces a valid PDF. A rendered graph at 1600x900 yields 40-70KB PDF. Blank/corrupted pages yield <10KB.

PDFs cannot be displayed inline in Hermes WebUI MEDIA protocol. Use as a size heuristic only.

## Fix C: Chrome DevTools Protocol (Node.js + ws)

Full working script:

```javascript
const { spawn } = require("child_process");
const http = require("http");
const WebSocket = require("ws");
const fs = require("fs");

const chrome = spawn("google-chrome-stable", [
  "--headless", "--disable-gpu",
  "--remote-debugging-port=9222",
  "--window-size=1600,900",
  "https://example.com"
]);

setTimeout(() => {
  http.get("http://localhost:9222/json/version", (res) => {
    let d = "";
    res.on("data", c => d += c);
    res.on("end", () => {
      const info = JSON.parse(d);
      const sock = new WebSocket(info.webSocketDebuggerUrl);
      sock.on("open", () => {
        sock.send(JSON.stringify({id:1, method:"Page.enable"}));
        setTimeout(() => {
          sock.send(JSON.stringify({
            id:2, method:"Page.captureScreenshot",
            params:{format:"png"}
          }));
        }, 3000);
      });
      sock.on("message", (msg) => {
        const m = JSON.parse(msg);
        if (m.id === 2 && m.result?.data) {
          fs.writeFileSync("/tmp/screenshot.png",
            Buffer.from(m.result.data, "base64"));
          console.log("OK");
          chrome.kill();
          process.exit(0);
        }
      });
      setTimeout(() => { chrome.kill(); process.exit(1); }, 25000);
    });
  });
}, 3000);
```

Run: `node script.js` (requires `ws` npm package: `npm install ws`)

## Validation

Check if the PNG is valid:

```python
import struct
with open('/tmp/page.png','rb') as f:
    d = f.read()
pos = 8
while pos < len(d):
    l = struct.unpack('>I', d[pos:pos+4])[0]
    ct = d[pos+4:pos+8]
    if ct == b'IDAT':
        print(f'VALID PNG - {l} bytes IDAT')
        break
    pos += 12 + l + 4
else:
    print('INVALID PNG - no IDAT data')
```

## Why it happens

The bug is in Chrome's `--screenshot` implementation for the headless mode. It opens the output file and writes the PNG headers eagerly (IHDR, pHYs, etc.) but the actual pixel data (IDAT) is deferred until the page's `load` event fires. If the page never fires `load` (due to infinite JS execution, async rendering, or a very large inline script), Chrome exits without ever writing the IDAT chunk. The file on disk has the headers but no image content.

The `--dump-dom` workaround forces Chrome to wait for the page to render because it needs the computed DOM for output.
