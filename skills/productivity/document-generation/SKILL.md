---
name: document-generation
description: "Generate polished HTML+CSS documents, convert to PDF via Playwright (in-container) or host Chrome headless, and QA-verify output. Covers resume/CV generation, formal documents, and any print-quality output requiring visual fidelity."
category: productivity
---

# Document Generation Pipeline

## When to Use
- User asks for a resume, CV, report, poster, or any document intended for print or PDF delivery
- Output must match a visual reference or template
- User has rejected fpdf2 / server-side PDF libs as insufficient for styled output

## Pipeline (Verified Working)

### CV-Targeting Pipeline: Research → Repo Audit → PDF

When the user asks for a tailored CV for a specific role, use this 4-phase pipeline.

### Phase 1 — Company & Role Research
1. Research the company: size, sector, culture, tech stack, recent news
2. Research the role: specific skills asked for, salary band, seniority level
3. Identify which of the user's existing CV variants (if any) is the closest match
4. Note specific keywords and requirements from the ad to weave into the CV

### Phase 2 — Repo Catalog Audit for CV Content
The user's owned repos (via seans-reporepo at `/home/sc/repos/seans-reporepo/owned/`) are the primary source of CV content. Do NOT assume which projects belong — audit the catalog:

1. Read the owned repo markdown files, filtering by relevance to the target role
2. For each candidate repo, note: description, tags, language, key content summary
3. Rank repos into tiers:
   - **Tier 1 (direct hit)** — repos directly demonstrating the exact skills asked for
   - **Tier 2 (breadth signal)** — shows engineering rigour but less directly relevant
   - **Tier 3 (skip)** — wrong domain, too frontend-heavy, data-science-only, or abandoned
4. Present the ranked tiers to the user for vetting before writing the CV
5. Incorporate the user's content exclusions ("don't include repo X") — some repos may be strong signals but the user has reasons to exclude them (e.g. `casaos-agent`, `hermes-sync`). Respect exclusions without arguing.

### Phase 3 — Source Code Deep-Dive for Technical Depth
The user wants specific technical details from actual source code, not high-level descriptions. For each Tier 1 repo selected:

1. Read key source files: Dockerfile, docker-compose.yml, main.go/index.ts, config structures, systemd units, Makefile, CI/CD configs
2. Extract specific details:
   - **Libraries and versions** (e.g. `nhooyr.io/websocket v1.8.10`, `gorilla/mux v1.8.1`)
   - **Architecture patterns** (e.g. semaphore-based concurrency via buffered chan, health cascades, dead-letter queue)
   - **Concrete numbers** (e.g. 2.45 GB backup, 9 containers, 17 ingress rules, 269 MB→94 MB compression)
   - **Security configurations** (e.g. NoNewPrivileges, ProtectSystem=strict, HMAC-SHA256 signing)
   - **Infrastructure details** (e.g. multi-stage Docker builds, cross-compile targets, dual build orchestrators)
3. Weave these specifics into CV bullet points — each bullet should name at least one concrete technology or number

### Phase 4 — Page Count Decision Framework

Before generating the HTML, decide **1 page vs 2 pages**. Do not default to "maybe" — make a call.

**Prefer 1 page when:**
- Role is early-career / graduate / junior (0-3 years experience) — 2 pages signals padding
- The role is placed through a recruitment agency — recruiters scan in ~6 seconds
- Content (selected Tier 1 + Tier 2 repos) fits on 1 page with tight formatting (10pt body, 1.8 line spacing)
- The user doesn't have 8+ years of professional experience to fill 2 pages

**Prefer 2 pages when:**
- Role is senior / lead / principal — 1 page signals you have nothing to say
- Content genuinely overflows after reasonable tightening (body text below 8pt)
- The user explicitly wants a comprehensive portfolio overview
- Multiple distinct career phases that can't be compressed

**Default for Sean (this user):** 1 page for early-career roles. Fit the content by tightening spacing (adaptive spacing per char-count tiers) before considering truncation or a second page.

**Pitfall:** Don't cut essential content to fit 1 page — drop Tier 2 projects instead. Quality of remaining bullets matters more than total count.

### Phase 5 — Generate, Convert, Upload
Follow the HTML Generation → PDF Conversion → Drive Upload pipeline below. After PDF generation:
- Measure blank space programmatically with Playwright (see `references/blank-space-measure.js`)
- Target <5% blank space; tighten/loosen spacing if needed
- Upload both PDF and source markdown to Drive via the Google Workspace skill

### Philosophy Box (CV Differentiator)
When the user has a distinctive intellectual framework (e.g. Principle of Parsimony, Occam's Razor, PAC learning theory), include it as a subtle visual element on the CV:

```html
<div class="phil-box">
  <strong>Engineering Philosophy — Principle of Parsimony:</strong>
  Given multiple models with equivalent predictive accuracy, the simplest is
  favoured. Grounded in PAC learning theory, VC dimension, and Minimum
  Description Length — applies as much to system architecture as to machine
  learning.
</div>
```

Style it with a muted background (`#f8fafc`) and accent left border (`border-left: 2px solid #2d7d6f`). Keep the text smaller (8pt) and secondary-colour so it doesn't compete with the main content. Place it right after the summary.

### Eval-Driven Dev & Promptfoo as CV Content
When the user's development process includes promptfoo or autonomous agent loops, include these as engineering credibility signals:
- promptfoo: LLM-as-judge eval framework, adversarial red-teaming (OWASP LLM categories), evasion strategies (base64, leetspeak, rot13), cost/latency assertions
- Coach/Player loop: tick-based autonomous dev with evidence-gated review, checkpoint.json state persistence, separate agent roles per task type
- Emphasise the *systems thinking* angle, not the AI novelty — these are eval infrastructure and process automation

## Pre-Step: Parse Markdown Sources (when applicable)
When the source material is markdown (CVs, docs, reports), parse it into structured data before generating HTML. The markdown CVs in this system have a consistent format:
```
# CV-v{num}-{role}.md — For {Role Description}
## Summary
## Skills
**Category:** skill, skill, skill
**Category2:** skill, skill
## Experience
**Job Title** (Employment Type)
Description line.
- Bullet detail
## Projects
**Project Name** (Tech, Stack)
Description.
## Education
```
Use a Python parser that:
- Separates contact lines (before first `##` heading) from section content
- Splits `##` sections by heading name
- Parses `**Category:** skill, skill` lines into (category, [skills]) tuples
- Detects `**Title** (Tag)` lines to split experience/project entries
- Cleans bold markers (`**`) from text before rendering
- Handles entries with only descriptions (no bullets) — still render them
- Escapes `&` to `&amp;` in titles/descriptions

**Pitfall:** `"\n".join(sidebar)` on an already-joined string joins individual characters with newlines. `render_sidebar()` returns a string; pass it directly to `.format()` without a second `.join()`.

### Step 1 — HTML Generation
- Generate HTML with proper print CSS (see `references/print-css.md`)
- Use Tailwind CDN, Font Awesome CDN, and Google Fonts (Inter recommended)
- Use `@page { size: A4; margin: 0; }`
- Use `page-break-inside: avoid` on `.keep-together` blocks
- Do NOT use hard page breaks unless content is guaranteed to fit
- Better: let Chrome auto-paginate with `keep-together` classes
- For batch generation, write a Python script that reads all markdown files and outputs HTML files to an output directory
- For two-column resume layout: header spans full width, sidebar=30% (skills, education, strengths), main=70% (summary, experience, projects)

### Step 2 — Convert to PDF (two options)

**Option A — Playwright in-container (preferred when available):**
```bash
cd /project/dir && npm install playwright  # one-time setup
node -e "
const {chromium} = require('playwright');
(async()=>{
  const b = await chromium.launch({executablePath: '/home/sc/.cache/ms-playwright/chromium-1223/chrome-linux64/chrome'});
  const p = await b.newPage({viewport:{width:1240,height:1754}});
  await p.setContent(html, {waitUntil:'networkidle'});
  await p.pdf({path:'output.pdf', format:'A4', margin:{top:'0mm',right:'0mm',bottom:'0mm',left:'0mm'}, printBackground:true});
  await b.close();
})();
"
```
- Chromium binary at `~/.cache/ms-playwright/chromium-1223/chrome-linux64/chrome`
- Install playwright via npm (already available at npx level)
- Set `executablePath` explicitly — auto-detection may fail for locally-installed npm packages
- Single-file CJS script (`.cjs` extension or set `type: module`) is simplest for one-off converts

**Option B — Host Chrome headless (legacy, via SSH):**
```bash
google-chrome-stable --headless --no-sandbox --disable-gpu \
  --print-to-pdf=output.pdf \
  --no-margins \
  file:///input.html
```
- Chrome at `/usr/bin/google-chrome-stable`
- Copy HTML files to host via SCP first

### Step 3 — Verify Output
- Use `vision_analyze` with **specific measurable criteria**, not generic ratings
- Take a screenshot first via Playwright, then analyze it:

```node
const {chromium} = require('playwright');
const b = await chromium.launch({executablePath:'...'});
const p = await b.newPage({viewport:{width:1240,height:1754}});
await p.goto('file://path.html', {waitUntil:'networkidle'});
await p.screenshot({path:'page.png', fullPage:true});
```

Then QA with vision:
```
CRITICAL QA: [document type]
1. BODY TEXT: Readable or too small?
2. BLANK SPACE: What % empty? Excessive?
3. LAYOUT: Two-column working? Any overflow? Fit 1 page?
4. SKILL TAGS: Any ** artifacts or raw HTML visible?
5. CONTENT: All expected sections visible?
6. OVERALL: Single biggest problem?
```

**Pitfall:** If raw HTML appears in the rendered page (e.g. `<aside class="sidebar">` shown as text), the HTML template has a `.format()` or variable interpolation bug — check that sidebar/main content variables aren't being passed through `"\n".join()` unnecessarily.

### Step 4 — Upload (Google Drive)
Use the `productivity/google-workspace` skill's Drive API script:
```bash
GAPI="python3 $HOME/.hermes/skills/productivity/google-workspace/scripts/google_api.py"
# First trash old files
$GAPI drive delete FILE_ID
# Then upload new ones
$GAPI drive upload /path/to/file.pdf --parent FOLDER_ID --name "Display Name.pdf"
```
- Delete (trash) old files before uploading if replacing — Drive allows duplicate names
- Trashed files are reversible
- **Pitfall:** Shell loops over files with spaces in names need `while IFS= read -r` or `shlex.quote()` in Python. `for f in $DIR/CV - *.pdf` breaks on spaces.

## Print CSS Reference
See `references/print-css.md` for: page sizing, font size tables for Playwright vs host Chrome, color theme, page break strategy, and container-specific pitfalls (Playwright executable path, shell quoting, ".join()" bugs).

## Extracting Text from JS-heavy Job Portals
When a job listing page is a JavaScript SPA (Elmo Talent, Workday, etc.),
see `references/cdp-page-text-extraction.md` for the CDP WebSocket pattern
to extract page text, find job links, and read full descriptions.

## Page Filling (Adaptive Spacing)

To fill an A4 page to <5% blank space when content volume varies between documents:

**Character-count density detection** — more reliable than line count because long bullet text wraps:

```python
char_count = len(summary) + len(all job/project text) + len(strengths)
if char_count < 2500:    # Lean
    sec_gap=28, item_gap=22, bullet_gap=8, line_h=2.3, bline_h=2.2
elif char_count < 3500:  # Medium
    sec_gap=22, item_gap=18, bullet_gap=5, line_h=2.1, bline_h=2.0
else:                    # Dense
    sec_gap=18, item_gap=16, bullet_gap=4, line_h=2.0, bline_h=1.9
```

Apply `font-size` and inline `line-height` to body text and bullets per tier.

**Flexbox footer push** — push a footer block to the bottom of the page regardless of content volume:

```css
.page { display: flex; flex-direction: column; min-height: 297mm; }
.body-div { display: flex; flex: 1; min-height: 0; }        /* fills vertical */
.main { width: 74%; display: flex; flex-direction: column; flex: 1; }  /* stretch */
.footer { margin-top: auto; }                                 /* push to bottom */
```

The `min-height: 0` on the body div is essential — without it, flex children can't shrink below their content height and `flex: 1` won't distribute correctly.

**Bold marker cleanup** — user's markdown often uses `**text**` for emphasis in bullet points. Convert to HTML `<strong>` before rendering:

```python
def md_bold_to_html(text):
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = text.replace("**", "")  # cleanup unmatched
    return text
```

Apply to ALL text content: titles, descriptions, bullets, summary, tech tags, sidebar items.

**Blank space verification** — do NOT trust vision model estimates (they consistently over-report blank space at 20-45% when actual is <1%). Measure with Playwright:

```javascript
const metrics = await page.evaluate(() => {
  const page = document.querySelector('.page');
  const footer = document.querySelector('.footer');
  return {
    pageHeight: page.getBoundingClientRect().height,
    footerBottom: footer ? footer.getBoundingClientRect().bottom : null,
    blankPercent: ((pageHeight - footerBottom) / pageHeight * 100).toFixed(1)
  };
});
```

## QA Verification
⚠️ **Do NOT trust vision_analyze ratings blindly** — the auxiliary vision model may be unreliable. Always:
1. **Measure** rendered font sizes from PDF metadata (PyMuPDF)
2. **Count** pages and lines per page
3. **Check** section presence (all expected content in text extraction)
4. **Flag** blank space >20% of page to user
5. Only then use vision_analyze as a **secondary** check with specific prompts about font size, whitespace, and legibility — NOT generic "rate 1-10"

## User Preferences
- Sean wants polished dark-themed output matching reference design
- Rejects half-baked PDFs (fpdf2, simple programmatic layouts)
- Must ask before generating — "what format, QA criteria, style?"
- Check in during multi-step work with tradeoffs
- Direct, action-oriented communication
