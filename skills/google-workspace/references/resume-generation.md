# Resume Generation — Preferred Format

## Format Decision: docx over HTML

**docx is the default for job applications.** Reasons:
- ATS systems parse docx natively; HTML→PDF can introduce parsing issues
- Hiring managers expect docx/PDF; docx lets them open, annotate, copy-paste
- python-docx pipeline is already established (see templates/resume-template.py)
- No browser rendering step needed

**Exception:** If the job posting explicitly requests PDF, generate docx first then convert:
```bash
libreoffice --headless --convert-to pdf resume.docx
```

## Style Guide (from TEAC portfolio precedent)

Established formatting from `build_portfolio_v2.py` — use for all professional documents:

| Element | Value |
|---------|-------|
| Font | Times New Roman |
| Body text | 11pt |
| H1 | 13pt, bold, UPPERCASE |
| H2 | 12pt, bold |
| H3 | 11pt, bold, italic |
| Header background | `1F4E79` (dark navy) |
| Header text | White, bold |
| Row colors | `FFFFFF` / `E8F0F7` alternating |
| Margins | 1" all sides |
| Table text | 9pt |
| Dividers | `─` * 72, 9pt, grey `B4B4B4` |

## Template

See `templates/resume-template.py` for a reusable starter that produces a clean, ATS-friendly docx resume with the above styling. Modify content, keep structure.

## Usage Pattern

1. User provides job description + any existing resume/reference files
2. Search Google Drive for previous resumes: `GAPI drive search "name contains 'resume'" --max 10`
3. If previous resume exists, match its formatting style
4. Generate new resume as docx using python-docx with the style guide above
5. Save to workspace, offer PDF conversion if needed
