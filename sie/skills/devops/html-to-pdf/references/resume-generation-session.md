# Resume/CV Generation Session — June 2026

## QA Process Refined

After generating all 9 PDFs, automated checks passed but initial fpdf2 versions were rejected by the user as "awful." This taught that **fpdf2 is not acceptable for user-facing styled documents** — always use host Chrome.

### How the QA Pass Should Have Gone

1. **Ask the user first:** "I'm about to generate 9 PDFs. What format? What should I check? Want to see a sample first?"
2. **Generate one sample first** — not all 9 at once
3. **QA the sample** with PyMuPDF + vision_analyze
4. **Show the user the evidence** — not just "it looks good", but actual page counts, section presence, vision scores
5. **Get feedback** before batch generating
6. **Batch generate** only after sample is approved
7. **QA each** before uploading to Drive

### QA Enforcement Lessons (June 10)

The user made three explicit corrections:

1. **"They look awful how will you qa documents in future"** — after fpdf2 output. This established: always QA, use proper pipeline, visual fidelity matters.

2. **"All generated media needs to be assessed and you should ask me what to assess and ask questions often not just documents"** — expanded QA scope from just documents to ALL media. Also established the "ask first" pattern: don't assume what to check, ask the user.

3. **"Obviously you should qa the documents i asked that in a previous prompt"** — after the assistant regenerated but failed to present QA evidence. Takeaway: QA AND show evidence. Both are required.

### Spacing Balance Fix (Round 2 — June 10)

After the first Chrome round, user said PDFs had too much white space at the bottom. Fix applied:

- **CSS changes:** body font 8.5→9.5px, sidebar 8→9px, headings 0.6→0.65rem, padding 8→12px, line-height 1.35→1.45, tag padding 1→2px, section margins increased 20%
- **Content:** slightly expanded project descriptions to fill pages
- **Result:** Vision confirmed 8.5/10 both pages, white space resolved, readability improved

**User's exact instruction:** "do a bit of both ensure there is spacing to make it easy to read" — meaning: expand content AND loosen layout. Not one or the other. User prefers readable spacing over compact.

### Automated QA Checklist (used in final pass)

```python
checks = {
    "header_name": "Sean Cheong",
    "skills": "SKILLS",
    "summary": "SUMMARY",
    "experience": "EXPERIENCE",
    "projects": "PROJECTS",
    "footer_email": "seanos1a@gmail.com",
    "education": "EDUCATION",
    "philosophy": "PHILOSOPHY",
    "strengths": "STRENGTHS",
    "tools": "TOOLS",
    "closing": "many more",
}
```

All 9 PDFs passed these checks (search case-insensitive due to CSS text-transform).

### Visual QA Results — Final Round

- **Python-Backend:** 9/10 overall — clean layout, no cut-off text, professional, white space resolved
- **Data-Engineer:** 8.5/10 — all sections present, good spacing
- **Solutions-Engineer:** 8/10 — good, minor content repetition between Skills and Tools sections
- **Vision confirmed:** all 9 PDFs at least 8/10 with improved spacing

### Corrective Actions Taken (Round 1)

1. Switched from fpdf2 to host Chrome pipeline
2. Added "ask first" and "QA is mandatory" sections to the html-to-pdf skill
3. Added content-spacing balance principle to the skill
4. Created QA evidence presentation workflow

### Note: Skill Overlap

The `html-to-pdf` and `print-css` skills both cover Chrome headless PDF generation from a Docker container. They should eventually be consolidated — `print-css` is the CSS/layout resource, `html-to-pdf` is the operational pipeline. A future curator should merge them.

---

## Session Details (for context)

A multi-role CV generation system for Sean Cheong, producing 9 role-specific PDF resumes from a single HTML template.

## Key Files

| File | Purpose |
|------|---------|
| `/workspace/generate_cvs.py` | CV content definitions (9 variations) + `make_html()` template function |
| `/workspace/build_host_pdfs.py` | Full pipeline: generate HTML → SCP to host → Chrome print-to-pdf → retrieve → verify |
| `/workspace/job-search-system.md` | Job search playbook (9 categories, daily workflow, weekly review) |
| `/workspace/cv-output/host-pdfs/` | Final 2-page PDFs (380-435 KB each) |

## CV Variations Generated

1. **Python-Backend** — Junior Software Engineer (general purpose)
2. **Data-Engineer** — ETL, databases, pipelines
3. **Full-Stack** — Frontend + backend, web apps
4. **Solutions-Engineer** — Client-facing tech, pre-sales
5. **ML-AI** — ML engineering, data science
6. **DevOps-Platform** — Docker, CI/CD, infrastructure
7. **Data-Analyst** — BI, dashboards, analytics
8. **Database-Admin** — SQL Server, DBA
9. **Graduate** — Grad programs, consulting, general

## Template Structure

The HTML template (in `make_html()` in generate_cvs.py):
- Two-column layout: 30% sidebar + 70% main
- Navy (#1e3a5f) accent bar header with gradient
- Tailwind CSS via CDN
- Google Fonts (Inter + JetBrains Mono)
- Font Awesome icons for contact
- Page 1: header + sidebar + summary + experience
- Page break (forced) → Page 2: slim header + projects + footer

## Verification Pipeline

1. PyMuPDF: check page count (target: 2)
2. PyMuPDF: extract text, check first/last lines per page
3. Vision: convert page to image at 150 DPI, use vision_analyze to check layout
4. File size check: 350-500 KB for styled PDFs

## Host Connection

- SSH: `sean@172.19.0.1` with key at `/home/hermeswebui/.ssh/id_ed25519`
- Chrome: `/usr/bin/google-chrome-stable` (version 143.x)
- Temp files: `/tmp/sean_cv_html/` and `/tmp/sean_cv_pdf/` on host
