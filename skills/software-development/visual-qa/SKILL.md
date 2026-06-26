---
name: visual-qa
description: Quality assurance of visual output using vision models — PDFs, images, screenshots, HTML artifacts, and design mockups.
trigger:
  - User asks you to "check if this looks good" or "QA this visual output"
  - After generating a PDF, image, HTML artifact, or design
  - Before delivering visual output that must meet quality or style standards
---

# Visual QA Methodology

Use vision models to assess visual output quality when the user expects production-grade results. This covers PDFs, screenshots, rendered HTML, images, and design mockups.

## Core Principle

**Prompt with specific measurable criteria, not generic ratings.**

A prompt like "rate 1-10" or "does this look good" produces unreliable, vague assessments from vision models. Instead:

1. **List the exact dimensions to evaluate** (font size, white space, line spacing, color contrast, alignment)
2. **Ask comparison questions** ("compare body text to headings — is the ratio appropriate?" )
3. **Request specific measurements** ("what percentage of the page is blank?")
4. **Ask for a single biggest problem** — forces the model to prioritize

## Prompt Template

```
CRITICAL QA: [describe what's being assessed — printed resume, web screenshot, design mockup]

Answer specifically:
1. BODY TEXT: Is it readable or too small? Compare to headings.
2. BLANK SPACE: What percentage is empty? Is it excessive?
3. [DIMENSION]: [specific question]
4. [DIMENSION]: [specific question]
5. OVERALL: What's the single biggest visual problem? Be specific.
```

## What to Check

| Domain | Dimensions to Prompt For |
|--------|--------------------------|
| Resumes / Docs | Body text size, blank space %, line spacing, heading hierarchy, sidebar readability |
| Web / UI | Font legibility, spacing consistency, alignment, color contrast, information density |
| Images / Graphics | Subject clarity, text overlays, color harmony, resolution, cropping |
| Presentations | Slide density, font hierarchy, chart readability, whitespace balance |

## Pitfalls

- **Do NOT ask "rate 1-10"** — vision models give inflated, unreliable numeric scores
- **Do NOT trust a single assessment** — vision models miss subtle issues; cross-reference with quantitative PDF measurements (pyMuPDF/fitz can extract exact font sizes and content positions)
- **Do NOT ask yes/no questions** — "is it good?" gives a useless answer
- **Verify blank space claims** — the vision model's % estimate can differ significantly from actual PDF measurements
- **Exponential blank space exaggeration** — vision models tend to overestimate blank space on pages with sparse content; always cross-check with numerical data when possible
- **vision_analyze cannot read PDF files directly** — attempting to pass a `.pdf` file path to `vision_analyze` will fail with "Invalid image source". Always convert the PDF to a PNG screenshot first (via Playwright, Puppeteer, or `pdftoppm`) before running visual QA. The screenshot preserves the rendered layout exactly as a human would see it.
- **`page.screenshot()` may not reflect final PDF** if the HTML uses print-specific CSS (`@page`, `page-break`, `display: none` on screen). Screenshot from the HTML source, not from the PDF viewer. If you must screenshot from a PDF, render it as an image via `mutool draw` or `pdftoppm`.

## Quantitative Backup

Pair vision QA with numerical measurements when PDFs are involved:
- PyMuPDF (fitz): extract font sizes, content bounding boxes, blank space calculations
- Compare rendered font distribution against CSS declarations to catch rendering discrepancies

## Document Generation + QA Pipeline

When the task is "regenerate X as a PDF and QA it" (resumes, reports, cover letters, CVs), the full pipeline is:

### Step 1 — Source → Styled HTML

Generate an HTML document with inline CSS from the source content (markdown, plain text, JSON). Use a single self-contained HTML file with:
- Inline `<style>` block — no external dependencies
- Print-oriented CSS (`@page { size: A4; margin: ... }`)
- Font stack that renders cleanly in headless browsers (system fonts or Google Fonts via `<link>`)
- Class-based selectors for the QA measurement targets (`.heading`, `.body-text`, `.sidebar`, `.bullet`)

For **multiple variants** (e.g. different role-targeted CVs from a shared source), build a generator script that:
1. Reads each variant's markdown source
2. Injects it into a shared HTML template
3. Outputs one HTML file per variant

### Step 2 — HTML → PDF

Convert HTML to PDF using one of:
- **WeasyPrint** (`pip install weasyprint`): `weasyprint input.html output.pdf` — best CSS support for print, handles `@page` rules, page breaks, and font embedding. Preferred for documents.
- **Puppeteer/Chromium headless**: `page.pdf({ format: 'A4', printBackground: true })` — better for complex layouts with JS rendering. Use the chrome-libs setup from the `ui-qa-pipeline` skill if Chromium is in a container.
- **wkhtmltopdf**: Fallback if neither is available.

### Step 3 — Visual QA

Apply the visual-qa methodology (see above) to each generated PDF:
1. Open PDF in browser or as an image via `vision_analyze`
2. Use the **Prompt Template** with document-specific criteria (body text size, blank space %, line spacing, heading hierarchy)
3. Cross-check quantitative measurements with PyMuPDF (`fitz`)
4. Iterate: fix CSS → regenerate → re-QA until acceptable

Common iteration targets:
- **Too much blank space**: reduce margins, increase font size, or add content
- **Text too small**: bump body font by 1pt. Starting default for body: 9pt minimum (this user rejected 7.5pt)
- **Line spacing too tight**: bump to 1.6-1.8 for body text, 1.55-1.65 for bullets (this user rejected 1.5)
- **Content overflows page 2**: tighten line-height or reduce whitespace
- **Bad page break**: add `page-break-inside: avoid` to sections

**Critical — font size & spacing starting defaults for this user:**
- Body text (bullets, descriptions): 9-9.5pt minimum. Never below 9pt.
- Section headings: 9-10pt, bold
- Main name heading: 18-22pt
- Role subtitle: 8-9pt, uppercase, wide letter-spacing
- Skill tags: 7-8pt
- Line heights: 1.6-1.8 for all running text. Below 1.5 = too cramped.
- Blank space target: below 25% of page. Hard limit 35%.
- When content is sparse, increase font and spacing to fill the page — don't leave large whitespace and don't try to pad with filler content.

### Step 4 — Deliver

Upload the final PDFs to the destination:
- **Google Drive**: use the `productivity/google-workspace` skill's Drive API (`$GAPI drive upload`)
- **Local file**: save under the session workspace
- On Drive uploads, overwrite existing PDFs by uploading to the same parent folder with the same name

### Trigger conditions

Use this pipeline when the user asks to:
- "Regenerate my resumes/CVs as PDFs"
- "Generate and QA a document from source"
- "Make me a PDF version of X and check it looks good"
- "Create variants of this document for different roles"

### Tips

- **Name the output files consistently** so Drive overwrite works (e.g. `CV - {Role}.pdf`)
- **Batch QA after generation** — generate all variants first, then QA them in parallel to avoid vision API rate limits mid-pipeline
- **Reserve 3-5 browser_vision calls per document** for thorough QA (one per page + one overall)
- **Reference the `references/resume-generation-pipeline.md`** file for a concrete session example with markdown CVs
