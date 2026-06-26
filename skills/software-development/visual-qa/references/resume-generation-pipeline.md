# Resume/CV Generation Pipeline (Session Example)

This reference captures the concrete pattern from a session where 9 markdown CVs were regenerated as PDFs with visual QA and uploaded to Google Drive.

## Source Structure

The job search folder on Drive (`Sean Cheong — Job Search 2026`) contained:

```
CV - {Role}.md              # source markdown per variant
CV - {Role}.pdf              # existing PDF (to be replaced)
```

9 variants: Python Backend, Data Engineer, Full Stack, Solutions Engineer, ML AI, DevOps Platform, Data Analyst, Database Admin, Graduate.

Each markdown source followed this structure:

```markdown
# CV-v1-{role}.md — For {Target} roles

Sean Cheong
email | phone | location
github.com/ChonSong

## Summary
One-paragraph summary tailored to the role.

## Skills
**Languages:** ...
**Backend:** ...
**Frontend:** ...
**DevOps:** ...
**Data / ML:** ...

## Experience
**Role — Company/Context**
- bullet points with **emphasized text**

## Projects
**Project Name** (tech stack)
Description

## Education
Degree — University
```

## HTML Template Design

Use a single-column or two-column layout. Key CSS decisions:

```css
@page {
  size: A4;
  margin: 2cm 2.2cm;
}
body {
  font-family: 'Inter', 'Segoe UI', Helvetica, Arial, sans-serif;
  font-size: 10pt;
  line-height: 1.5;
  color: #1a1a1a;
}
h1 { font-size: 18pt; margin-bottom: 0.2em; }  /* Name */
h2 { font-size: 13pt; border-bottom: 1px solid #ccc; }  /* Section headers */
```

### QA criteria specific to resumes

| Criterion | Target | Check method |
|-----------|--------|-------------|
| Body text size (bullets, descriptions) | 9-9.5pt minimum | vision_analyze; user will reject below 9pt |
| Section headings | 9-10pt | Should be bold and clearly larger than body |
| Role subtitle | 8-9pt, uppercase, letter-spaced | Below name |
| Skill tags | 7-8pt | Legible at full-page view |
| Line spacing (body text) | 1.6-1.8 | Below 1.5 is cramped |
| Line spacing (bullets) | 1.55-1.65 | Ensure gap between consecutive lines |
| Blank space (A4=842pt) | target <25%, hard limit <35% | fitz: `(842 - max_y) / 842 * 100` |
| Sidebar width | 28-30% | Content must not overflow or wrap oddly |
| Page break | no orphans, sections intact | vision per page |

**IMPORTANT — starting defaults:** Never start with body text below 9pt or line spacing below 1.6. This user has rejected 7.5pt/1.5 spacing. If content is sparse relative to page size, increase font size (up to ~10pt) and spacing to fill the page rather than leaving excessive whitespace.

## Google Drive Integration

Pattern for uploading regenerated PDFs:

```bash
GAPI="python ${HERMES_HOME:-$HOME/.hermes}/skills/productivity/google-workspace/scripts/google_api.py"

# Upload with parent folder ID so it lands in the right place
$GAPI drive upload /path/to/CV-Python-Backend.pdf \
  --name "CV - Python-Backend.pdf" \
  --parent FOLDER_ID
```

The folder ID is persistent — store it in memory to avoid re-searching on subsequent sessions.

## Common Parser Pitfalls (Markdown → HTML)

### `**Bold Markers**` in skill lines

Markdown like `**Languages:** Python, TypeScript` needs the `**` stripped _before_ splitting on `:`. Naive `strip("\*")` only removes leading/trailing characters, leaving `**Languages` intact. Clean with a dedicated function:

```python
re.sub(r'\*\*', '', text).strip()
```

### `**Bold Markers**` inside bullet or description content

Markdown in source files often uses `**` for emphasis within prose:

```markdown
- Restored a **2.45 GB SQL Server backup** (SQL Server 2019) into a Dockerized Linux container
```

When rendering to HTML, these `**` markers must be converted to `<strong>` tags, not stripped:

```python
def md_bold_to_html(text):
    """Convert **text** to <strong>text</strong> and strip remaining * markers."""
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = text.replace("\*\*", "")  # cleanup any unmatched markers
    return text
```

Apply this to ALL text content entering the HTML renderer: bullet text, descriptions, summary text, job titles. The browser renders literal `**` asterisks as-is, so failing to convert produces visible `**2.45 GB**` in the output — a clear error the user will flag.

### `str.join()` on a string instead of a list

When refactoring a function from returning a list to returning a joined string, an old call site like:

```python
sidebar="\n".join(sidebar),  # sidebar is now a string, not a list
```

...silently joins individual characters with newlines, turning `<aside>...</aside>` into `<\n a\n s\n i\n d\n e\n...` — which the browser renders as raw text. The fix: remove the `join()` wrapper when the variable is already a string.

### Markdown → HTML bold pipeline overview

When processing markdown with `**bold**` markers, the pipeline is:

1. **Parse** — extract text content from markdown structure, keeping `**` markers intact
2. **Render** — call `md_bold_to_html()` on all text content entering HTML (bullets, descriptions, titles, summary)
3. **Output** — the HTML contains `<strong>text</strong>` which the browser renders correctly

Do NOT strip `**` before parsing — the parser needs to identify section boundaries correctly (e.g., `**Job Title**` vs `**Skill Category:**`), and stripping early loses that signal.

### Experience entries not being split

Entries like:

```markdown
**Database Developer & Analyst — OneTag HMAS Sydney** (Contract/Freelance)
- bullet 1

**Freelance Software Developer** (Self-Employed)
- bullet 2
```

Need a stateful parser that saves the current entry on encountering `**...**` and starts a new one. A naive loop collecting all bullets under one title merges entries together.

### Projects without bullets

Some projects have only a description (no `- ` bullets). The parser must still emit them — don't gate project output on `if current_bullets:`.

## Playwright PDF Generation (Container Environment)

### Chromium binary path

Playwright in containers often has browsers at a non-standard path. Check and use:

```javascript
const browser = await chromium.launch({
  executablePath: '/home/sc/.cache/ms-playwright/chromium-1223/chrome-linux64/chrome'
});
```

### Headless shell vs regular Chrome

The npm package `playwright` at v1.60 looks for `chromium_headless_shell-1223` — this binary may not exist if Chrome was installed by an older Playwright version. Always check `~/.cache/ms-playwright/` for what's actually installed. Fall back to the plain `chrome-linux64/chrome` path.

### Font rendering

Google Fonts (Inter, JetBrains Mono) render via `<link>` tags when the headless browser has network access. Font Awesome icons render from CDN. Use `waitUntil: 'networkidle'` to ensure fonts load before PDF capture.

### File naming for Drive overwrite

Drive's API does NOT overwrite by name. To replace an existing file, you must either:
- Delete the old file first, then upload the new one with the same name to the same parent
- Or use the Drive API to update the file content by file ID

The simplest pattern is: upload with `--name` and `--parent`, which creates a new file alongside the old one. Then delete the old file by its returned file ID.

## Two-Column Resume Template Pattern

```html
<!-- HEADER: full-width accent bar -->
<header style="background: linear-gradient(135deg, #1e3a5f 0%, #2d5a8a 100%); padding: 14px 22px; color: white;">
  <div style="display: flex; align-items: center; gap: 20px;">
    <div style="flex: 1;"><h1>Name</h1><p class="role-title">ROLE</p></div>
    <div style="flex-shrink: 0; text-align: right;">contact icons + text</div>
  </div>
</header>

<!-- BODY: sidebar + main -->
<div style="display: flex; flex: 1;">
  <aside class="sidebar" style="width: 28%; background: #f8fafc; padding: 14px 12px;">
    <!-- skill categories, education, focus/strengths -->
  </aside>
  <main style="width: 72%; padding: 14px 16px;">
    <!-- summary, experience, projects -->
  </main>
</div>
```

### Key CSS for A4 print

```css
@page { size: A4; margin: 0; }  /* no default page margins — control via padding */
.page { width: 210mm; min-height: 297mm; }  /* exact A4 dimensions */
html, body { margin: 0; padding: 0; background: white; }
body { font-family: 'Inter', sans-serif; font-size: 11pt; }
```

### Sidebar skill tag styling

```css
.tag {
  background: #e8f0fe; color: #1e3a5f; font-size: 7.5pt;
  font-weight: 500; padding: 3px 9px; border-radius: 5px;
  display: inline-block; margin: 1.5px;
}
```

### Experience entry structure

```html
<div style="display:flex; align-items:baseline; justify-content:space-between; gap:8px;">
  <span class="job-title">Job Title</span>
  <span class="date-pill">Contract/Freelance</span>
</div>
<p class="job-sub">Brief description of the engagement</p>
<p class="bullet">• Bullet point</p>
```

## Visual QA Findings for Resume PDFs

| Finding | Cause | Fix |
|---------|-------|-----|
| Sidebar renders as raw HTML code | `"\n".join(sidebar)` where sidebar is already a string | Remove join; pass the string directly |
| 30-40% blank space at page bottom | Content naturally concise | Accept for one-pagers; expand if user requests |
| Skill tags show `**` prefixes | `strip("\*")` doesn't remove inline markers | Use `re.sub(r'\*\*', '', text)` instead |
| Bullet text shows literal `**` markers | `**text**` in source passed raw to HTML | Apply `md_bold_to_html()` to all text content |
| Font Awesome icons missing | CDN not loaded before PDF capture | Use `waitUntil: 'networkidle'` in Playwright |
| Vague blank space reports from vision | Vision model exaggerates sparse pages | Cross-check with fitz; prompt for %, not opinion |

## Iteration Pattern

1. Generate all N HTML files from markdown + shared template
2. Screenshot 2-3 variants for visual QA
3. Fix CSS/parser issues in the template
4. Batch-regenerate all PDFs
5. Sample-QA the fixed variants
6. Upload to Drive (with confirmation)

This avoids regenerating N PDFs per CSS iteration — fix the template once, regenerate all.
