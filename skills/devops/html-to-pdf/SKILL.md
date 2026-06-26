---
name: html-to-pdf
description: Generate production-quality PDFs from styled HTML using host Chrome headless. Covers the full pipeline — container HTML generation, SCP to host, Chrome print-to-pdf, retrieval, and automated verification with PyMuPDF + vision_analyze.
---

# HTML → PDF Pipeline

## When to Use

Any task requiring a polished PDF from styled HTML (CVs, reports, certificates, documentation). The container's headless Chromium cannot render CSS/HTML properly (missing system libs, dbus, GPU stack). The host machine has `google-chrome-stable` with full rendering capability.

## Do NOT Use Programmatic PDF Generators

fpdf2, ReportLab, and similar libraries produce plain PDFs that **cannot replicate** complex CSS layouts (two-column designs, Tailwind CSS, custom fonts, sidebar layouts). If the source is styled HTML, use this pipeline. Only use fpdf2 for simple programmatic PDFs with no CSS layout requirements.

**🚫 fpdf2 for user-facing CVs/resumes — tested and rejected.** The output was rated "awful" by the user — flat, unstyled, no visual fidelity to the original HTML template. fpdf2's `write_html()` handles only basic formatting; it cannot render flexbox, grid, or CSS-based layouts. For any document the user will see or send to others, always use the host Chrome pipeline below.

## Before You Generate: Ask First — This Is Enforced

**Do not charge ahead generating media/documents without user input.** The user explicitly flagged this as a priority and has corrected this behavior. Before creating any PDF, image, or other rendered output:

1. **Ask the user what format they want** — PDF, docx, HTML, or something else?
2. **Ask what QA criteria matter** — page count? visual fidelity? text extractable? ATS-compatible?
3. **Ask if they want to review a sample first** — especially if there's a preferred template or style
4. **Check if the user has an existing template** — search `/workspace/resumes/` or ask
5. **Ask about spacing preference** — some users prefer compact, others want loose/readable. Don't assume.

This applies to ALL generated media, not just PDFs. When in doubt about whether to ask: ask. The user would rather be asked than receive something that misses the mark.

## QA Process — Mandatory for Every Generated Document (NOT Optional)

After generating ANY PDF, you MUST verify it before declaring it done. The user has explicitly corrected this twice — QA is not optional even for "small" changes.

### Ask First — What to Assess

Before generating any media (PDF, image, video, audio — not just documents):

1. **Ask the user what they want you to check** — page count? visual fidelity? text extractable? ATS-compatible? file size? specific sections?
2. **Ask if they want a sample first** — especially for batch generation. Generate one, QA it, show the evidence, get feedback before doing the rest.
3. **Ask about preferences** — compact or readable spacing? any specific template or style reference? existing documents to match?

**The user's explicit rule:** "All generated media needs to be assessed and you should ask me what to assess and ask questions often not just documents."

### The QA Workflow (Not Optional — Never Skip)

After generating:

1. **Run automated checks** (PyMuPDF text extraction, page count, section presence)
2. **Run visual checks** (vision_analyze on rendered page images)
3. **Present the evidence to the user** — don't just verify silently. Show them: "Page 1: 92 lines, ends with X. Page 2: 23 lines, all sections present. Vision: 8.5/10."
4. **Ask for feedback** before uploading or delivering

If you've already generated and verified but didn't present the evidence: go back and show it. The user expects to see the QA results, not just be told "it's good."

### Content-Spacing Balance Principle

When a PDF has excessive whitespace (content too short for the pages):

**Do NOT just compact everything** — the user's instruction was explicit: "do a bit of both ensure there is spacing to make it easy to read."

The correct fix is a combination of:
- **Loosen layout:** increase font sizes (body: 9-9.5px, sidebar: 9px, headings: 11px), padding (sidebar: 10px, main: 12-14px), line-height (1.45-1.5), tag padding (2px 7px), section margins
- **Expand content:** add more detail to descriptions, additional bullet points, slightly longer summary paragraphs

**Vision-validated sweet spot (for A4 2-page resume):**
| Element | Compact (previous) | Readable (validated) |
|---------|-------------------|---------------------|
| Body font | 8.5px | 9-9.5px |
| Sidebar font | 8px | 9px |
| Line-height | 1.35 | 1.45-1.5 |
| Sidebar padding | 8px | 10px |
| Main padding | 10px 12px | 12px 14px |
| Tag padding | 1px 6px | 2px 7px |
| Section spacing | 6-8px | 8-10px |
| Element margin | 1-2px | 2-3px |

When content OVERFLOWS (3+ pages when target is 2): reverse — compact slightly, shorten descriptions, reduce tag count.

### Automated Verification

```python
import fitz, os
from pathlib import Path

pdf_path = "/workspace/output.pdf"
doc = fitz.open(pdf_path)

# 1. Page count
print(f"Pages: {doc.page_count}")

# 2. Content completeness per page
for i in range(doc.page_count):
    text = doc[i].get_text()
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    print(f"Page {i+1}: {len(lines)} lines")
    print(f"  First: {lines[0][:80]}")
    print(f"  Last:  {lines[-1][:80]}")

# 3. Section presence check (case-insensitive, CSS uppercase counts)
checks = ["sean cheong", "skills", "summary", "experience", "projects", "education"]
full_text = "".join(doc[i].get_text().lower() for i in range(doc.page_count))
missing = [c for c in checks if c not in full_text]
if missing:
    print(f"⚠ MISSING SECTIONS: {', '.join(missing)}")

# 4. File size sanity check
size_kb = os.path.getsize(pdf_path) // 1024
print(f"Size: {size_kb} KB")
# Styled PDFs with CDN resources: ~350-500 KB for 2 pages

# 5. ⚠ CRITICAL: Verify rendered font sizes (CSS px ≠ print pt)
page = doc[0]
blocks = page.get_text('dict')['blocks']
font_sizes = set()
for b in blocks:
    if 'lines' in b:
        for line in b['lines']:
            for s in line['spans']:
                t = s['text'].strip()
                if t and not any(c in t for c in [' \n', '\n ']):
                    font_sizes.add(f"{s['size']:.1f}pt")
print(f"Rendered font sizes: {sorted(font_sizes)}")
# Expected: body ~9pt, sidebar ~8pt, headings ~9pt, name ~16-24pt
# If body < 7pt, the CSS used px instead of pt — fix and regenerate

doc.close()
```

### Visual Verification with Proper Vision Prompting

If the document has visual layout (two-column, sidebar, custom colors, tags):

```python
doc = fitz.open(pdf_path)
for i in range(doc.page_count):
    pix = doc[i].get_pixmap(dpi=150)
    pix.save(f"/workspace/page_{i+1}_preview.png")
doc.close()
```

Then use `vision_analyze` on each page image. **CRITICAL: Prompt the model with specific criteria — do NOT ask for a generic "rate 1-10" and trust the result.** The user has explicitly corrected this: "the vision model needs to know what to look for."

**⚠ Never trust a generic 1-10 rating from the vision model.** When this pipeline was first used, the model said "8-9/10 — looks great" while the user said "still looks awful." The model was giving positive ratings because the prompt was vague and the model had no specific criteria to evaluate against. Only when prompted with specific, directive questions did the model surface real issues (excessive whitespace, small font sizes, cramped spacing).

**Rule: If you asked "rate 1-10" or anything similarly vague, the rating is unreliable. Discard it and re-prompt with specific questions.**

### Troubleshooting vision_analyze Failures

When `vision_analyze` returns an error (auth failure, timeout, provider unavailable):

**Understand the provider resolution chain:**

1. Config.yaml `auxiliary.vision` section is the primary source (provider, model, api_key, base_url, timeout)
2. Falls back to **auto-detection** which checks:
   - The user's main provider (e.g. opencode-go) → mapped via `_PROVIDER_VISION_MODELS` in auxiliary_client.py
   - Strict vision backends: `copilot`, `openrouter`, `nous`, `openai-codex`
   - If main provider has no strict backend → falls through to aggregators (OpenRouter first)
3. OpenRouter reads `OPENROUTER_API_KEY` env var; returns 401 if missing/invalid
4. If all aggregators fail, raises "No LLM provider configured for task=vision"

**Free OpenRouter vision models (tested 2026-06-12):**

The preferred approach for document QA vision is OpenRouter free tier. No credits needed:

```yaml
auxiliary:
  vision:
    provider: openrouter
    model: nvidia/nemotron-nano-12b-v2-vl:free
    api_key: ${OPENROUTER_API_KEY}
```

Or the meta-model that auto-routes:
```yaml
auxiliary:
  vision:
    provider: openrouter
    model: openrouter/free
    api_key: ${OPENROUTER_API_KEY}
```

**Confirmed working free vision models on OpenRouter:**

| Model | Quality | Notes |
|-------|---------|-------|
| `nvidia/nemotron-nano-12b-v2-vl:free` | Best | Detailed descriptions, fast. |
| `openrouter/free` | Good | Auto-routes. Good fallback. |
| `nex-agi/nex-n2-pro:free` | OK | Shorter responses. |
| `google/gemma-4-31b-it:free` | Good | Rate-limited (429). |

**The `.env` file must have the actual key (not `***` placeholder).** The `OPENROUTER_API_KEY` env var is read by `_try_openrouter()` via `os.getenv()` — if it's missing or invalid, you get HTTP 401.

**Config file vs env var trap:** the `AUXILIARY_VISION_MODEL` env var (set by gateway at startup from config.yaml) OVERRIDES the config file model. Even if config.yaml says `model: nvidia/nemotron-nano-12b-v2-vl:free`, if the gateway has `AUXILIARY_VISION_MODEL=mimo-v2-omni` from an earlier startup, the stale env var wins. Check with `env | grep AUXILIARY_VISION`. Fix by adding correct values to `.env` (per-turn reload picks them up) or restarting the WebUI.

**Common failure modes:**

| Error | Likely Cause | Fix |
|-------|-------------|-----|
| "Missing Authentication header" (401) | `OPENROUTER_API_KEY` missing/invalid in environment | Set valid key in `.env`. The key must be in the environment, not just config.yaml — `_try_openrouter()` reads `os.getenv()` directly. |
| "No endpoints found for {...}" (404) | Old stale model in `AUXILIARY_VISION_MODEL` env var | `mimo-v2-omni` is dead. Check `env \| grep AUXILIARY_VISION_MODEL` and set to a working OpenRouter free model. |
| "Payment Required" (402) | OpenRouter model is paid tier, no credits | Use a `:free` suffix model (`nvidia/nemotron-nano-12b-v2-vl:free`) or `openrouter/free`. |
| "No LLM provider configured for task=vision" | No working provider at all | Configure `auxiliary.vision` in config.yaml with `provider: openrouter` and `api_key: ${OPENROUTER_API_KEY}` |

**Validation steps:**

1. Check `.env` has real values (not `***` placeholders): `cat ~/.hermes/.env`
2. Check `auxiliary.vision` in config.yaml: `cat ~/.hermes/config.yaml`
3. Check the stale env override: `env | grep AUXILIARY_VISION`
4. If stale, either update `.env` and wait for per-turn reload, or restart the WebUI
5. Direct API test:
```python
import json, urllib.request
# ... (see hermes-auxiliary-config-debug skill for code)

**Effective vision prompt pattern (use exact questions, not ratings):**

For page 1:
```
I need you to do a critical QA assessment of this resume PDF page. Focus only on these specific questions:

1. BODY TEXT SIZE: Is the paragraph text large enough to read comfortably when printed at A4? Compare it visually to the section headings. Is the ratio appropriate?

2. BLANK SPACE: What percentage of the page is empty white space? Is there a large empty area at the bottom?

3. LINE SPACING: Are the bullet points too tight (cramped) or reasonably spaced?

4. SIDEBAR TAGS: Are the skill tags (Python, FastAPI, etc.) readable or too small?

5. OVERALL: Does this look like a professionally formatted printed resume or does the font look too small / spacing off?

Be specific — tell me exactly what's wrong and needs to change.
```

For page 2:
```
Rate page 2 of this resume on: projects readable? any cut-off text? footer present? overall professional look? List specific issues.
```

**Do NOT trust a vision model rating of 8-10/10 without cross-checking.** The user has found these ratings unreliable when the prompt is vague. If the vision model says "looks good" but you're unsure, measure the actual rendered font sizes from the PDF metadata (see step above) and present both sets of evidence to the user.

**After QA, present the evidence to the user — don't just verify silently.** Show them: "Page count: 2. Page 1: 92 lines, body text at 9pt, sections all present. Page 2: 23 lines, projects complete. Vision noted [specific issue]. What do you think?"

The user has corrected this behavior multiple times — QA evidence must be shown, not hidden.

### When to Regenerate

| Issue | Action |
|-------|--------|
| Wrong page count | Adjust font sizes, spacing, or content volume |
| Sections missing | Check HTML template for the missing element |
| Text cut off | Increase page margins or reduce content |
| Excessive whitespace | **Loosen layout** — increase font sizes (body: 9-9.5px, sidebar: 9px), padding (10-14px), line-height (1.45-1.5). Or expand content with more detail. User prefers readable spacing over compact — "do a bit of both." |
| Layout too cramped | Same as whitespace fix — bigger fonts, more padding, looser line-height |
| Layout visually wrong | Fix CSS/HTML and regenerate |
| fpdf2 was used | Switch to host Chrome pipeline |

### See Also

- **`devops/print-css`** — CSS print layout theory, page break rules, content-spacing balance. Use this when you need the CSS/layout concepts behind the pipeline. This skill (`html-to-pdf`) is the operational pipeline; `print-css` is the theory.
- **`devops/go`** — Patching Go files with indentation corruption recovery pattern (git checkout + Python string replace, stop after 2 failed patches).

## What NOT to Do

- Never use fpdf2 for user-facing styled PDFs (the user considers this "awful")
- Never skip QA on generated documents
- Never upload or send a PDF you haven't verified
- Never tell the user "it should be fine" — show evidence from verification

## The Pipeline

### Step 1 — Generate HTML

Create HTML with proper print CSS:
```css
@page { size: A4; margin: 0; }
@media print { .page-break { page-break-before: always; } }
.keep-together { page-break-inside: avoid; }
```

Use CDN resources (Tailwind, Google Fonts, Font Awesome) — the host has internet access:
```html
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<script src="https://cdn.tailwindcss.com"></script>
```

### Step 2 — Transfer to Host

```python
SSH = ["ssh", "-i", "/home/hermeswebui/.hermes/container_key", "-o", "StrictHostKeyChecking=no", "sean@172.19.0.1"]
SCP = ["scp", "-i", "/home/hermeswebui/.hermes/container_key", "-o", "StrictHostKeyChecking=no"]

# Create temp dir on host
subprocess.run(SSH + ["mkdir", "-p", "/tmp/sean_pdf/input"])

# Copy HTML
subprocess.run(SCP + ["/workspace/local.html", "sean@172.19.0.1:/tmp/sean_pdf/input/file.html"])
```

### Step 3 — Convert with Chrome on Host

```python
cmd = (
    f"google-chrome-stable --headless --no-sandbox --disable-gpu "
    f"--print-to-pdf=/tmp/sean_pdf/output.pdf "
    f"--no-margins "
    f"file:///tmp/sean_pdf/input/file.html"
)
subprocess.run(SSH + [cmd], capture_output=True, text=True, timeout=30)
```

- `--no-margins` is required — the CSS `@page { margin: 0; }` alone may not be respected
- `--no-sandbox --disable-gpu` needed for headless mode
- Set `timeout=30` — Chrome takes 5-15s per page

### Step 4 — Retrieve PDF

```python
subprocess.run(SCP + [f"sean@172.19.0.1:/tmp/sean_pdf/output.pdf", "/workspace/output.pdf"])
```

### Step 5 — Verify

```python
import fitz
doc = fitz.open("/workspace/output.pdf")

# Check page count
print(f"Pages: {doc.page_count}")

# Extract text to verify content rendered
for i in range(doc.page_count):
    text = doc[i].get_text()
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    print(f"Page {i+1}: {len(lines)} lines")
    print(f"  First: {lines[0][:80]}")
    print(f"  Last:  {lines[-1][:80]}")

# Check file size (styled PDFs with CDN resources: 350-500 KB for 2 pages)
print(f"Size: {path.stat().st_size // 1024} KB")

# Visual QA with vision_analyze (convert page to image)
pix = doc[0].get_pixmap(dpi=150)
pix.save("/workspace/page_preview.png")
doc.close()
```

Then use `vision_analyze` on the preview image to check layout, cut-off text, sidebar rendering, etc.

### Step 6 — Clean Up Host

```python
subprocess.run(SSH + ["rm", "-rf", "/tmp/sean_pdf"], capture_output=True)
```

## Pitfalls

| Issue | Symptom | Fix |
|-------|---------|-----|
| Blank PDF | 0 KB or 9 KB PDF with no text | Chromium headless shell in container can't render CSS. MUST use host Chrome via SSH. |
| 3+ pages when expecting 2 | Content overflows with proper font sizes | Remove forced `page-break-before: always` — let Chrome auto-paginate. Use `keep-together` classes on individual blocks. A hard page break + proper font sizes = overflow to page 3. |
| Fonts rendering tiny in PDF | CSS `px` values → Chrome converts ~1px→0.75pt in print | Use `pt` units not `px` in print CSS. `9pt` renders as 9pt in the PDF. `9px` renders as ~6pt (too small). Always verify rendered font size by checking `line['spans'][0]['size']` from PyMuPDF's `get_text('dict')`. |
| Missing fonts/Tailwind | Text renders but unstyled | HTML must be served from a location Chrome can access (file:// works). CDN URLs need host internet — which works from host. |
| `@page { margin: 0 }` ignored | Content has unwanted margins | Add `--no-margins` flag to Chrome command. |
| SSH connection refused | Host unreachable | Try both `sean@172.19.0.1` and `sean@localhost`. The Docker host bridge IP may vary. |

### Verifying Rendered Font Sizes (Not CSS Values)

After Chrome converts HTML to PDF, check what actually rendered — CSS values differ from print output:

```python
doc = fitz.open(pdf_path)
page = doc[0]
blocks = page.get_text('dict')['blocks']
for b in blocks:
    if 'lines' in b:
        for line in b['lines']:
            text = ''.join([s['text'] for s in line['spans']])
            if text.strip().startswith('Body text'):
                print(f'Rendered: {line["spans"][0]["size"]:.1f}pt (CSS said 9pt)')
doc.close()
```

If rendered size is 6pt when CSS says 9px, you need to use `9pt` in CSS, not `9px`.

## SSH Configuration

- **⚠ CRITICAL — Always verify the key path before each session.** The SSH key location has changed before. Currently it's at `/home/hermeswebui/.hermes/container_key`. Check `ls ~/.ssh/` and `ls ~/.hermes/container_key` and `ls ~/.hermes/home/.ssh/` to find the current location.
- **Host user:** `sean`
- **Host address:** `172.19.0.1` (Docker bridge IP)
- **Alternative address:** `localhost` (when Docker networking allows)
- **Known hosts:** auto-added via `StrictHostKeyChecking=no`

Reference pattern (use in build scripts):
```python
SSH = ["ssh", "-i", "/home/hermeswebui/.hermes/container_key", "-o", "StrictHostKeyChecking=no", "sean@172.19.0.1"]
SCP = ["scp", "-i", "/home/hermeswebui/.hermes/container_key", "-o", "StrictHostKeyChecking=no"]
```
