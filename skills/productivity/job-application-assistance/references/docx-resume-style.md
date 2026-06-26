# DOCX Resume Style Reference

Two styles are in use. Pick the right one for the job.

---

## Style A: Academic / Portfolio (TEAC, university assignments)

Used for: TEAC5019/5020 portfolios, academic submissions, documents with tables and structured layouts.

Key traits:
- Times New Roman, 11pt body / 12pt h2 / 13pt h1
- Dark navy header backgrounds (`1F4E79`) with white text
- Alternating table row colors (`FFFFFF` / `E8F0F7`)
- Cover page with centered title
- Section dividers (`─` × 72)
- Header rows: `set_cell_bg(cell, "1F4E79")` with white bold 9pt text

---

## Style B: Professional / Job Application (preferred for resumes)

Used for: Job applications, professional resumes, ATS-submitted documents.

**Key traits:**
- Single column, clean, no tables
- No colored backgrounds or fancy formatting
- ATS-friendly (no text boxes, no columns, no images)
- Conversational but professional first-person voice
- Section order: Title/Contact → Professional Summary → Core Skills → Qualifications → Employment History → Additional

### Page Setup

```python
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

doc = Document()
section = doc.sections[0]
section.page_width  = Inches(8.5)
section.page_height = Inches(11)
section.left_margin = section.right_margin = Inches(0.75)
section.top_margin  = section.bottom_margin = Inches(0.75)
```

### Heading Styles

```python
def h1(text):
    """Section heading — UPPERCASE, bold, navy color, with bottom border line"""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(4)
    run = p.add_run(text.upper())
    run.font.size = Pt(11)
    run.font.bold = True
    run.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)
    # Bottom border line
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), '4')
    bottom.set(qn('w:space'), '1')
    bottom.set(qn('w:color'), '1F4E79')
    pBdr.append(bottom)
    pPr.append(pBdr)
    return p

def h2(text):
    """Job title line — bold, company separated by │"""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(2)
    run = p.add_run(text)
    run.font.size = Pt(10)
    run.font.bold = True
    return p

def body(text, bold=False, italic=False, indent=False):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(3)
    if indent:
        p.paragraph_format.left_indent = Inches(0.25)
    run = p.add_run(text)
    run.font.size = Pt(10)
    run.font.bold = bold
    run.font.italic = italic
    return p

def bullet(text, level=0):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.space_after = Pt(2)
    if level:
        p.paragraph_format.left_indent = Inches(0.25 * level)
    run = p.add_run(text)
    run.font.size = Pt(10)
    return p

def divider():
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    run = p.add_run('─' * 90)
    run.font.size = Pt(8)
    run.font.color.rgb = RGBColor(0xCC, 0xCC, 0xCC)
    return p
```

### Header Block

```python
# Name — centered, large, navy
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run('SEAN CHEONG')
run.font.size = Pt(18)
run.font.bold = True
run.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)

# Contact line — centered, grey
p2 = doc.add_paragraph()
p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
run2 = p2.add_run('Sydney, NSW  │  0434 968 983  │  seanos1a@gmail.com')
run2.font.size = Pt(10)
run2.font.color.rgb = RGBColor(0x55, 0x55, 0x55)
```

### Skills Section Format

Skills are rendered as bold skill name + dash + detail, NOT as a table:

```python
skills = [
    ("Customer Service", "High-volume phone and in-person support — hundreds of interactions"),
    ("Stakeholder Communication", "Professional, empathetic communication with diverse clients"),
    # ...
]
for skill, detail in skills:
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(2)
    run = p.add_run(f'• {skill}')
    run.font.size = Pt(10)
    run.font.bold = True
    run2 = p.add_run(f'  —  {detail}')
    run2.font.size = Pt(10)
```

### Job Entry Format

```python
# Job title: "Role  │  Company, Location" — bold 10pt
h2('Domestic Support Officer  │  Australian Unity, Sydney, NSW')
# Subtitle: italic context line
body('In-person and over-the-phone personalised support for clients', italic=True)
# Bullets
bullet('Handled high-volume customer enquiries via phone and in person...')
bullet('Maintained a high standard of dignity and respect...')
```

### Color Palette

| Use | Hex | Notes |
|-----|-----|-------|
| Name | `1F4E79` | Dark navy |
| Section headings | `1F4E79` | Dark navy, UPPERCASE |
| Body text | `000000` | Black (implicit) |
| Contact/subtitles | `555555` | Mid grey |
| Divider | `CCCCCC` | Light grey |

### Key Rules

- **Always use `python-docx`** — NOT Node.js `docx` package
- **Page breaks**: Use `OxmlElement('w:pageBreakBefore')` — `add_break()` does not work reliably
- **Margins**: 0.75"–1" all sides
- **Save path**: `/workspace/resumes/[COMPANY]_[ROLE]_Resume.docx`
- **ATS compatibility**: single-column, no tables, no text boxes, no images, no headers/footers
- **Tone**: Conversational first-person. "A smooth sea never made a skilled sailor" — personality is welcome. Avoid corporate boilerplate ("I am a highly motivated individual...").
- **Qualifications section**: Include relevant certs, degrees (note "in progress" if applicable), and compliance items (police check, WWCC) if required by the role
- **Additional section**: Brief paragraph on outside interests + availability/driver's licence if relevant

### Resume Structure Template

```
[NAME] — centred, 18pt, navy, bold
[Contact line] — centred, 10pt, grey

──────────────────────────────────────────────────────

PROFESSIONAL SUMMARY — h1 style (UPPERCASE, navy, bottom border)
[2-3 paragraphs, conversational, first-person]

CORE SKILLS
• Skill Name  —  Detail sentence
• Skill Name  —  Detail sentence

QUALIFICATIONS
• Certificate, Institution
• Degree (in progress), University
• Compliance items (police check, WWCC)

EMPLOYMENT HISTORY

Job Title  │  Company, Location — h2 (bold, 10pt)
Context subtitle — italic 10pt
• Bullet point with specific metrics
• Bullet point with specific metrics

[repeat for each role]

ADDITIONAL
[Brief paragraph: outside interests, tech skills, availability, driver's licence]
```
