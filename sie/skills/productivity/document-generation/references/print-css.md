# Print CSS Reference for Chrome Headless PDF Generation

## Key Rules

### 1. Use `pt` not `px` for font sizes
Chrome headless (`--print-to-pdf`) converts CSS `px` at roughly `0.67pt` per `1px`. Setting `font-size: 9.5px` produces ~6.4pt text in the PDF — unreadable.

**DO:**
```css
body { font-size: 10pt; }
.summary-text { font-size: 9pt; }
```

**DON'T:**
```css
body { font-size: 13px; }    /* Renders as ~8.7pt in PDF */
```

### 2. Page Sizing
```css
@page { size: A4; margin: 0; }
body { width: 210mm; }
```

### 3. Page Breaks
```css
.keep-together { page-break-inside: avoid; }
.page-break { page-break-before: always; }
```

**Pitfall:** Hard page breaks with `page-break-before: always` can cause 3-page overflow when page 1 content is long. Better to omit the break and let Chrome auto-paginate when content length varies.

### 4. Recommended Font Sizes (for A4 print)
| Element | Size (Playwright PDF) | Notes |
|---------|----------------------|-------|
| Name / Title header | 18pt | Playwright respects CSS `pt` values — no px/pt conversion issue |
| Role subtitle | 7.5-8pt | uppercase, letter-spaced |
| Section heading | 7.5-8pt | uppercase, letter-spaced |
| Body text | 7.5-9pt | 7.5pt is readable in Playwright PDFs |
| Sidebar text | 7pt | smaller is OK for sidebar content |
| Tags/pills | 6.5-7pt | |
| Sidebar labels | 7pt | |
| Contact info | 7-7.5pt | |
| Bullet items | 7.5pt | |

### 5. Layout
```css
.body-row { display: flex; width: 210mm; }
.sidebar { width: 30%; }
.main { width: 70%; }
```

### 6. Typical Colors (navy/teal theme)
- Navy: `#1e3a5f`
- Navy light: `#2d5a8a`
- Teal/issuer: `#2d7d6f`
- Light bg: `#f8fafc`
- Tag bg: `#e8f0fe`
- Body text: `#475569`

## Page Break Strategy
For content that varies in length:
- Remove hard `page-break-before: always` 
- Use `.keep-together` on each logical block
- Let Chrome auto-paginate naturally
- This prevents 3-page overflow on content-heavy variations

## Measuring Rendered Sizes
CSS `pt` values are NOT what Chrome renders. Always extract from PDF metadata:

```python
doc = fitz.open(path)
page = doc[0]
blocks = page.get_text('dict')['blocks']
for b in blocks:
    if 'lines' in b:
        for line in b['lines']:
            text = ''.join([s['text'] for s in line['spans']])
            if 'target text' in text:
                actual_pt = line['spans'][0]['size']  # This is the real rendered size
```

## Common Pitfalls
- Chrome headless shell (google-chrome-stable) can't render HTML to PDF in Docker — missing libglib-2.0, no GPU. Always use **host** Chrome for `--print-to-pdf`, OR use Playwright in-container with the locally-installed Chromium binary.
- Playwright in-container works for PDF generation. Set `executablePath` to `~/.cache/ms-playwright/chromium-1223/chrome-linux64/chrome`. Install via `npm install playwright`.
- The `container_key` at `/home/hermeswebui/.hermes/container_key` works for SSH. The `~/.ssh/id_ed25519` path may stop working mid-session.
- `--no-margins` flag is required for Chrome headless `@page { margin: 0 }` to take effect.
- `--disable-gpu` flag prevents crashes in Chrome headless mode.
- **Shell loops over filenames with spaces**: `for f in $DIR/CV - *.pdf` breaks. Use `ls "$DIR"/CV*.pdf | while IFS= read -r pdf` or `shlex.quote()` in Python.
- **Playwright font loading**: When `waitUntil: 'networkidle'` times out on slow external font/CDN loads, switch to `domcontentloaded` + a manual wait. Or pre-bundle fonts inline.
- **Raw HTML in rendered output**: If the browser shows `<aside class="sidebar">` as rendered text instead of styled content, check that the template `.format()` call isn't double-joining strings (e.g. `"\n".join(sidebar)` when `sidebar` is already a string).
