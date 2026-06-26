---
name: playwright-pdf
description: Generate A4 PDFs from HTML using Playwright (Node.js). Covers setup, browser path, rendering options, and common failure modes. Designed for document-generation pipelines (resumes, reports, certificates).
trigger:
  - User asks to "convert HTML to PDF", "generate a PDF", "export to PDF", "make a PDF from HTML"
  - Building a document-generation pipeline that needs styled PDF output
  - After generating HTML from markdown/templates and needing printable output
  - When weasyprint/wkhtmltopdf are unavailable and a browser-based renderer is needed
---

# Playwright HTML-to-PDF

Generate print-quality A4 PDFs from HTML using Playwright's Chromium browser engine. Good for resumes, reports, certificates, and any styled document output.

## Setup

### Install Playwright (project-local)

```bash
cd /path/to/project
npm init -y
npm install playwright
```

### Browser Binary

Playwright downloads its own Chromium to `~/.cache/ms-playwright/`. On this system:

```
~/.cache/ms-playwright/chromium-<version>/chrome-linux64/chrome
```

If the locally-installed Playwright package version differs from the globally-cached browser, you get:

```
browserType.launch: Executable doesn't exist at .../chromium_headless_shell-<version>/...
```

**Fix:** point `executablePath` at the already-installed chromium binary:

```javascript
const browser = await chromium.launch({
  executablePath: '/home/sc/.cache/ms-playwright/chromium-1223/chrome-linux64/chrome'
});
```

To check what's installed:
```bash
ls ~/.cache/ms-playwright/
```

### Verified Working Configuration (June 2026)

```
Chrome: chromium-1223 at ~/.cache/ms-playwright/chromium-1223/chrome-linux64/chrome
Node: v22.22.3
Playwright: latest (installed locally via npm)
```

Install and run:
```bash
cd /tmp && npm init -y && npm install playwright
node /tmp/html2pdf.cjs
```

## Basic Usage

```javascript
const { chromium } = require('playwright');

async function htmlToPdf(html, outputPath) {
  const browser = await chromium.launch({
    executablePath: '/home/sc/.cache/ms-playwright/chromium-1223/chrome-linux64/chrome'
  });
  const page = await browser.newPage({ viewport: { width: 1240, height: 1754 } });  // A4 proportions

  // Load HTML — use 'networkidle' if loading external fonts/CSS
  await page.setContent(html, { waitUntil: 'networkidle', timeout: 30000 });

  // Generate PDF
  await page.pdf({
    path: outputPath,
    format: 'A4',
    margin: { top: '0mm', right: '0mm', bottom: '0mm', left: '0mm' },
    printBackground: true,  // required for colored backgrounds
  });

  await browser.close();
}
```

### Using Local HTML Files

```javascript
await page.goto('file://' + htmlPath, { waitUntil: 'networkidle', timeout: 30000 });
```

Always use absolute paths with `file://` prefix. Relative paths fail:
```
net::ERR_INVALID_URL at file://relative/path.html
```

## Key Options

| Option | Value | Purpose |
|--------|-------|---------|
| `format` | `'A4'` | Standard document size (210×297mm) |
| `margin` | `{ top: '0mm', ... }` | Set all to 0mm for full-bleed; add margins via `@page` CSS |
| `printBackground` | `true` | Required for `background-color`, gradients, and images |
| `viewport` | `{ width: 1240, height: 1754 }` | A4 at ~150dpi; prevents content shifts |

## CSS for Print

```css
@page { size: A4; margin: 0; }
```

Set margin on `@page` — if using `margin: 0` in the Playwright pdf options, add padding in CSS instead:

```css
.page {
  width: 210mm;
  min-height: 297mm;
  padding: 20mm;
}
```

## Taking QA Screenshots

Use the same browser session to capture screenshots for visual QA:

```javascript
await page.screenshot({ path: 'output.png', fullPage: true });
```

Then run vision_analyze on the PNG to check font sizes, spacing, layout, clipping.

## Pitfalls

- **Browser path mismatch**: The locally-installed `playwright` npm package may look for a different browser directory than what's cached. Always set `executablePath` explicitly, or run `npx playwright install` after `npm install playwright`.
- **`networkidle` timeout**: Pages loading external fonts (Google Fonts, Font Awesome) may never reach `networkidle` if the CDN is slow. Fall back to `domcontentloaded` + a manual delay, or embed fonts inline.
- **No raw `**` markers**: If your source content has markdown bold (`**text**`), convert it to `<strong>text</strong>` before passing to Playwright — the browser renders `**` literally, not as bold.
- **Page content not filling**: `page.setContent()` can occasionally render HTML tags as text if the content string has embedded issues (e.g., a join bug like `"\n".join(string)` treating a string as a char array — results in each character separated by a newline in the HTML source). Verify with `page.content()` if rendering looks wrong.
- **Duplicate file names in Drive**: Google Drive allows multiple files with the same name. When replacing files, trash the old IDs first before uploading new ones.
