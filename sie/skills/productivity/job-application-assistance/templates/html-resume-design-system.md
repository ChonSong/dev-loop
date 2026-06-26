# HTML Resume Template Reference

This is the canonical HTML resume design system, derived from the user's existing templates (ISS concierge, welfare officer). When generating HTML resumes, replicate this structure exactly — only change the content.

## Layout

```
┌─────────────────────────────────────────────────────┐
│  ACCENT BAR (navy gradient)                         │
│  Name · Role                    Contact details      │
├──────────────┬──────────────────────────────────────┤
│   SIDEBAR    │            MAIN                       │
│   (30%)      │            (70%)                      │
│              │                                       │
│  Tech Stack  │  Professional Summary                 │
│  Education   │  Projects (for tech roles)            │
│  Soft Skills │  Employment History                   │
│  Availability│                                       │
└──────────────┴──────────────────────────────────────┘
```

## Key CSS Variables

| Element | Value |
|---------|-------|
| Accent bar | `linear-gradient(135deg, #1e3a5f 0%, #2d5a8a 100%)` |
| Sidebar bg | `bg-slate-50` |
| Sidebar border | `border-slate-200` |
| Section heading color | `#1e3a5f` (navy) |
| Tag/badge bg | `#e8f0fe` |
| Tag/badge text | `#1e3a5f` |
| Date pill bg | `#1e3a5f` (white text) |
| Accent/issuer | `#2d7d6f` (teal) |
| Body text | `text-slate-600` / `text-slate-700` |
| Body font size | `text-[9.5px]` (main), `text-[11px]` (headings) |
| Name font | `text-2xl font-bold` |
| Font family | Inter (body), JetBrains Mono (tech labels) |
| Page width | 210mm (A4) |

## Section Heading Pattern

```html
<h3 class="sidebar-heading">Section Name</h3>
<hr class="section-rule">
```

With CSS:
```css
.sidebar-heading {
  color: #1e3a5f;
  padding-bottom: 3px;
  margin-bottom: 4px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-size: 0.65rem;
}
.section-rule {
  border: none;
  border-top: 2px solid #1e3a5f;
  margin-bottom: 6px;
}
```

## Tag/Badge Pattern (for tech stack)

```html
<div class="flex flex-wrap gap-0.5 mb-1">
  <span class="tag">Python</span>
  <span class="tag">React</span>
  <span class="tag">PostgreSQL</span>
</div>
```

## Date Pill Pattern

```html
<span class="date-pill">2023 – 2026</span>
<!-- or -->
<span class="date-pill">github.com/ChonSong/gto-wizard-clone</span>
```

## Project Entry Pattern

```html
<div class="mb-2">
  <div class="flex items-baseline justify-between gap-2 mb-0.5">
    <span class="font-semibold text-[9.5px] text-slate-800">Project Name — Description</span>
    <span class="date-pill">github link or tech label</span>
  </div>
  <p class="tech mb-1">Tech1 · Tech2 · Tech3</p>
  <p class="text-[9.5px] text-slate-600 mb-1 leading-relaxed">One-line description.</p>
  <ul class="text-[9.5px] text-slate-600 list-disc list-inside leading-relaxed">
    <li>Bullet point with specific detail</li>
  </ul>
</div>
```

## Employment Entry Pattern

```html
<div class="mb-2">
  <div class="flex items-baseline justify-between gap-2 mb-0.5">
    <span class="font-semibold text-[9.5px] text-slate-800">Job Title</span>
    <span class="date-pill">Date range</span>
  </div>
  <p class="text-[9.5px] issuer font-medium mb-1">Company · Location</p>
  <ul class="text-[9.5px] text-slate-600 list-disc list-inside leading-relaxed">
    <li>Bullet point</li>
  </ul>
</div>
```

## Header Pattern

```html
<header class="accent-bar px-7 py-5 text-white">
  <div class="flex items-center gap-5">
    <div class="flex-grow">
      <h1 class="text-2xl font-bold tracking-tight mb-0.5">Full Name</h1>
      <p class="text-xs font-light tracking-widest uppercase opacity-90">Target Role</p>
    </div>
    <div class="flex-shrink-0 text-right text-[9.5px] space-y-1 opacity-90">
      <p><i class="fas fa-phone mr-2 w-4 text-center"></i>Phone</p>
      <p><i class="fas fa-envelope mr-2 w-4 text-center"></i>Email</p>
      <p><i class="fas fa-map-marker-alt mr-2 w-4 text-center"></i>Location</p>
      <p><i class="fab fa-github mr-2 w-4 text-center"></i>github.com/Username</p>
    </div>
  </div>
</header>
```

## Cover Letter HTML Pattern

Single-column, same accent bar header, body text `text-[10px]`, same color palette. Use `issuer` class for accent color on key phrases. Structure:

```
[Header with name + role + contact]
[Salutation]
[Paragraph 1: Opening — what role, why interested]
[Paragraph 2: What you bring — 3-4 bullet-style points with icons]
[Paragraph 3: Alignment — why this company/environment]
[Paragraph 4: Availability + call to action]
[Sign-off]
```

## Font Imports (required in `<head>`)

```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
```

## Tailwind + Font Awesome (required in `<head>`)

```html
<script src="https://cdn.tailwindcss.com"></script>
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
```

## Print-to-PDF

**For user-initiated printing (browser):**
1. Open the HTML file in Chrome/Edge
2. Ctrl+P (or Cmd+P)
3. Destination: Save as PDF
4. Margins: None
5. Background graphics: ON
6. Save

**For server-side/automated generation (preferred for multi-page):**
```bash
google-chrome-stable --headless --disable-gpu \
  --print-to-pdf=/path/to/output.pdf \
  --print-to-pdf-no-header \
  file:///path/to/input.html
```
- `--print-to-pdf-no-header` removes Chrome's URL/date footer
- The `vaInitialize failed: unknown libva error` message is harmless — ignore it
- For multi-page resumes, use separate `.page` divs (see `templates/html-resume-multipage-example.md`)

**Always verify the output before sending** — use `import fitz; doc = fitz.open('output.pdf')` to check page count and content distribution.

## File Naming Convention

- Resume: `/workspace/resumes/[COMPANY]_[ROLE]_Resume.html`
- Cover letter: `/workspace/resumes/[COMPANY]_Cover_Letter.html`
- Short answers: `/workspace/resumes/[COMPANY]_Short_Answers.md`

## When to Use Each Format

| Format | When to use |
|--------|-------------|
| **docx** | Default for ATS submissions, corporate roles, government |
| **HTML** | When user explicitly requests it, startups, design-forward roles, user has existing HTML templates |
| **markdown** | Quick drafts, inline preview, version control |
