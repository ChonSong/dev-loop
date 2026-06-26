---
name: print-css
description: CSS print layout rules (@page, page-break, print media queries) for HTML-to-PDF conversion. Covers the CSS/layout theory — for the full operational pipeline (SSH to host Chrome, file transfer, QA verification), use devops/html-to-pdf.
triggers:
  - "css print layout"
  - "page break css"
  - "@page rules"
  - "print stylesheet"
  - "multi-page html layout"
  - "overflow page content"
  - "content balancing across pages"
when_to_use:
  - You need to understand CSS print rules (@page, page-break-*, print media queries)
  - You're troubleshooting page break issues in headless Chrome output  
  - You need the CSS/layout theory behind HTML→PDF generation
  - ⚠ For the FULL OPERATIONAL PIPELINE (SSH, host Chrome commands, file transfer, QA), use devops/html-to-pdf
---

# Print CSS / HTML→PDF

Convert HTML to multi-page PDF using CSS print rules. This skill covers the CSS/layout theory. For the full operational pipeline (generating HTML, transferring to host, running Chrome, retrieving PDFs, and QA verification), use `devops/html-to-pdf`.

## ⚠ CRITICAL: Use `pt` NOT `px` for Print CSS

Chrome headless converts CSS `px` at ~0.75pt per px in PDF output. A CSS `font-size: 9px` renders as `~6pt` in the PDF — too small for print.

**Always use `pt` units for print CSS font sizes, padding, and spacing.**

| CSS | Rendered in PDF | Verdict |
|-----|-----------------|---------|
| `font-size: 9px` | ~6pt | Too small |
| `font-size: 9pt` | 9pt | Good |
| `padding: 8px` | ~6pt in print | Too tight |
| `padding: 8pt` | 8pt | Good |

To verify rendered sizes:
```python
page = doc[0]
blocks = page.get_text('dict')['blocks']
for b in blocks:
    if 'lines' in b:
        for line in b['lines']:
            for s in line['spans']:
                if s['text'].strip():
                    print(f"Rendered: {s['size']:.1f}pt — '{s['text'][:40]}'")
                    break
```

## CSS Print Layout Rules

### Basic Setup

```css
@page {
  size: A4;
  margin: 0;
}

body {
  width: 210mm;
  margin: 0;
  background: white;
}
```

### Page Break Controls

```css
.keep-together { page-break-inside: avoid; }
.page-break { page-break-before: always; }
```

**How to use:**
- `keep-together` → Apply to individual items (experience entries, project cards) so they don't split across pages
- `page-break` → Put between page blocks to force a new page

### Two-Page Resume Layout Pattern

The verified pattern for a 2-page resume:

**Page 1:** Full header (name + title + contact) + two-column body (30% sidebar, 70% main) with Summary + Experience
**Page 2:** Slim header (name + title + GitHub) + full-width Projects + footer bar

Structure as separate `<div>` blocks with `page-break-before` between them:

```html
<!-- PAGE 1 -->
<div>
  <header>...</header>
  <div class="body-row">
    <div class="sidebar">...</div>
    <div class="main">...</div>
  </div>
</div>

<div class="page-break"></div>

<!-- PAGE 2 -->
<div style="display:flex;flex-direction:column;min-height:297mm;">
  <header class="slim">...</header>
  <div class="content">...</div>
  <div class="footer" style="margin-top:auto;">...</div>
</div>
```

> **Important:** Do NOT wrap each page in a separate `.page` div with fixed height (`height: 297mm`). Chrome's print engine treats them as one continuous document, causing content overflow between them. Use a single document with `page-break-before: always` between page blocks.

### Page Break Pitfalls

1. **`page-break-inside: avoid` on flex containers** — Chrome may ignore it. Apply to individual block-level children instead.
2. **Margin collapse across page breaks** — Top margins of elements starting a new page may collapse. Use padding instead.
3. **Backgrounds on page breaks** — `@page { margin: 0 }` eliminates all print margins. For margins, use the CSS `@page { margin }` plus `--no-margins` flag.
4. **`min-height: 297mm` on page 2 wrapper** — Helps the footer push down with `margin-top: auto`. This is fine because there's no `overflow: hidden` to clip content.
5. **`overflow: hidden` clips content** — Never add `overflow: hidden` to page containers. It will clip sidebar content and project sections.
6. **`page-break-before` inside flex row** — Putting break-before on an element inside `display: flex; flex-direction: row` causes the flex container to split unpredictably. Use separate block-level containers.
7. **Flexbox + page breaks don't mix** — Don't rely on `page-break-*` inside a `display: flex` container. Use block-level containers with explicit `page-break-before`.
8. **Text extraction is case-sensitive** — PyMuPDF `get_text()` returns rendered case. CSS `text-transform: uppercase` makes headings appear all-caps in extraction. Always use case-insensitive checks.
9. **Forced page breaks cause 3-page overflow with proper `pt` font sizes** — When using proper print font sizes, `page-break-before: always` between page 1 and page 2 causes content to overflow to page 3. **Fix:** Remove the hard page break entirely. Let Chrome auto-paginate with `keep-together` classes on individual blocks. The auto-pagination produces clean 2-page output.

## Content-Spacing Balance

When a PDF has excessive whitespace (not enough content for the pages):

**Do NOT just compact everything** — the user wants readable spacing. The correct fix is both:
- **Loosen layout:** increase font sizes, padding, line-height, margins
- **Expand content:** add more detail to descriptions, additional bullet points

**Validated sweet spot for A4 2-page resume:**

| Element | Compact | Readable (approved) |
|---------|---------|---------------------|
| Body font | 8.5px | 9-9.5px |
| Sidebar font | 8px | 9px |
| Line-height | 1.35 | 1.45-1.5 |
| Sidebar padding | 8px | 10px |
| Main padding | 10px 12px | 12px 14px |
| Tag padding | 1px 6px | 2px 7px |
| Section spacing | 6-8px | 8-10px |

When content overflows (3+ pages when target is 2): reverse — compact slightly, shorten descriptions, reduce tag count.

## Ask Before Generating — This Is Enforced

The user has explicitly directed: "All generated media needs to be assessed and you should ask me what to assess and ask questions often not just documents."

Before generating ANY PDF or other media output:
1. Ask what format and style the user wants
2. Ask what QA criteria matter (page count? visual fidelity? ATS-compatible?)
3. Ask if they want to review a sample first — especially for batch generation
4. Ask about spacing preference (compact vs readable)
5. Check for existing templates/styles to match

This applies to ALL generated media, not just PDFs.

## Chrome Headless PDF Generation

Only the host machine's `google-chrome-stable` (NOT the container's headless Chromium) can render styled HTML to PDF correctly.

### Command

```bash
google-chrome-stable --headless --no-sandbox --disable-gpu \
  --print-to-pdf=/path/to/output.pdf \
  --no-margins \
  file:///absolute/path/to/input.html
```

### Key Flags

| Flag | Purpose |
|------|---------|
| `--headless` | No GUI |
| `--disable-gpu` | Prevents GPU errors in headless mode |
| `--print-to-pdf=<path>` | Output file path |
| `--no-margins` | Suppresses Chrome's default print margins (VALID flag despite some docs saying otherwise) |
| `--no-sandbox` | Required in container/host headless mode |
| `file:///path.html` | Input HTML (absolute path with `file:///` prefix) |

### CDN / External Resources

Headless Chrome fetches external resources. The host has internet access, so CDN links work:
```html
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<script src="https://cdn.tailwindcss.com"></script>
```

### Chrome via SSH to Host Is the Only Acceptable Path for Styled PDFs

When the container's Chromium cannot render CSS/HTML properly (missing system libraries `libglib-2.0.so.0`, dbus errors), **do NOT fall back to fpdf2 for user-facing documents.**

**🚫 fpdf2 is explicitly rejected for styled documents** — tested and user-rated as "awful." fpdf2 cannot replicate two-column CSS layouts (flexbox, grid, sidebar), custom fonts with proper styling, tag/badge components, gradient headers, or any visual design beyond plain paragraph text. Its `write_html()` handles only basic formatting.

**Never use fpdf2 for documents the user will see or send to others.** Only use it for throwaway internal scratch PDFs (plain-text reports, data dumps).

**The only acceptable pipeline for styled PDFs:** generate HTML → SCP to host → `google-chrome-stable --headless --print-to-pdf` → SCP back. See `devops/html-to-pdf` for the full operational pipeline including SSH commands, QA process, and verification.

### Troubleshooting: Chrome in Container

When Chrome headless produces blank PDFs (0 chars extracted via PyMuPDF), the Chromium browser process is launching but its renderer can't composite pages. The dbus errors are symptomatic, not causal. The fix is NOT to debug Chrome in the container — it's to use host Chrome via SSH.

## QA Verification

After generating any PDF, verify before delivering. See `devops/html-to-pdf` for the complete QA workflow with code and vision check examples.

Key checks:
- Page count (expected vs actual)
- Text extraction by page (first/last lines, all sections present — case-insensitive)
- File size sanity (styled PDFs: 350-500 KB for 2 pages)
- Visual check via vision_analyze on rendered page images

## Common Pitfalls Summary

1. **Broken file refs** — HTML saved from Windows has `file:///C:/` paths. Replace with CDN links.
2. **Tailwind CDN vs inlined** — CDN needs internet at render time. Host has internet.
3. **Font Awesome missing** — If FA CDN unavailable, icons render as blank squares. Add fallback text.
4. **Page break before empty elements** — Apply `break-before` to the section container, not the heading.
5. **`--no-margins` is a VALID Chrome headless flag** — Despite some docs saying otherwise, `google-chrome-stable --headless --print-to-pdf --no-margins` works and produces margin-less output consistent with `@page { margin: 0; }` CSS. Always use both CSS `@page { margin: 0; }` AND the `--no-margins` flag for reliable margin-less output.
6. **vaInitialize error** — `ERROR:vaapi_wrapper` is harmless in headless mode. Ignore.
7. **Flexbox + page breaks don't mix** — Don't rely on `page-break-*` inside flex containers.
8. **Separate `.page` divs overflow** — Multi-page div wrappers overflow unpredictably. Use `page-break-before` between blocks instead.
9. **write_file partial-read bug** — If a file was read with `offset`/`limit` pagination, `write_file` may not persist. Write to temp file and `mv` via terminal.
10. **fpdf2 for styled documents** — NEVER use fpdf2 for user-facing styled documents. Only host Chrome via SSH.

## References

- `references/resume-print-session.md` — Session transcript: two-page resume conversion from HTML, including page break edge cases, CDN path fixes, and layout iterations
- `devops/html-to-pdf` — The full operational pipeline: HTML generation, SCP to host, Chrome conversion, retrieval, QA verification
