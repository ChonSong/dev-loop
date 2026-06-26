# Resume HTML → PDF Sessions

## Session 2026-06-10 — Junior Software Engineer Resume

Source: `/workspace/Sean_Cheong___Junior_Software_Engineer.html`  
Output: `/workspace/Sean_Cheong___Junior_Software_Engineer.pdf` (2 pages, ~460 KB)

### Approach Used

After 4 failed attempts with `.page` wrapper divs and flexbox, the working approach was:

**Single document flow with `page-break-before` between page blocks.** No `.page` wrappers with fixed height. Each page is a self-contained `<div>` with its own layout, separated by `<div class="page-break">`.

### Page Layouts

- **Page 1:** Full header + two-column (30% sidebar, 70% main) with Summary + Experience
- **Page 2:** Slim header (name + title + GitHub) + full-width Projects section + footer bar
- **Footer on page 2:** Thin border-top with name, email/phone, GitHub — anchors the page

### CSS Approach

```css
@page { size: A4; margin: 0; }
body { width: 210mm; }
.no-break { page-break-inside: avoid; }
.page-break { page-break-before: always; }
```

Used inline styles for layout (not Tailwind utility classes, which can behave differently in print).

### Sidebar Additions

Added to fill page 1 sidebar to ~85% height:
- Education expanded with **Thesis** and **Coursework** sections
- **Key Tools & Environment** section with Linux, Git, VS Code, curl, SSH, Docker tags
- Kept Modeling Philosophy shorter (trimmed parenthetical)

### Edge Cases Hit

1. **write_file partial-read failure** — File was previously read with `offset`/`limit` pagination; subsequent `write_file` appeared to succeed (`bytes_written: 19054`) but didn't persist. Verified by checking file still had original Windows file references. Fix: re-read the whole file first.

2. **`.page` divs don't page correctly** — Two separate `.page` divs with `height: 297mm` each caused content from page 1 to overflow onto page 2, and content from page 2 onto page 3. Adding `@media print { .page { height: auto; } }` made it worse (all content merged into one flow).

3. **`overflow: hidden` clips content** — Adding `overflow: hidden` to `.page` divs clipped sidebar content (Coursework, Key Tools sections were invisible in PDF).

4. **`page-break-before` inside flex row** — Putting break-before on an element inside `display: flex; flex-direction: row` causes the flex container to split unpredictably. Both columns can break independently.

5. **Text extraction case sensitivity** — PyMuPDF `get_text()` returns text in the rendered case. `"Professional Summary"` with title case doesn't match `"PROFESSIONAL SUMMARY"` in all-caps headings. Always use case-insensitive checks or look at the actual text.

6. **vision_analyze reliability** — The vision model may miss small text sections. Cross-check with direct text extraction when something appears missing.

### Chrome Command

```bash
google-chrome-stable --headless --disable-gpu \
  --print-to-pdf=/home/sean/workspace/output.pdf \
  --print-to-pdf-no-header \
  file:///home/sean/workspace/input.html
```

### Verification Method

```python
import fitz
doc = fitz.open('/workspace/output.pdf')
for i in range(len(doc)):
    pix = doc[i].get_pixmap(dpi=200)
    pix.save(f'/workspace/page_{i+1}.png')
# Then vision_analyze each page image
```

## Future Sessions

Add new resume-to-PDF sessions as date-stamped entries below.
