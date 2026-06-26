---
name: ubd-docx-generator
description: Generate filled .docx UbD (Understanding by Design) lesson plan templates using Node.js docx npm package. Used when Alto asks for a filled-in DOCX template rather than markdown.
version: 1.0.0
license: MIT
metadata:
  hermes:
    tags: [education, curriculum, UbD, DOCX, nodejs]
    related_skills: [curriculum-design]
---

# UbD DOCX Generator

## When to Use

Trigger when the user asks to:
- Return a filled-in DOCX template
- Convert an outline to a Word document
- Generate a `.docx` version of lesson plans, unit of work, or portfolio submission

## Preferred Approach: python-docx

**python-docx is installed and works in the Hermes container** (v1.2.0, installed via `pip install python-docx`). Use python-docx directly via terminal or execute_code — do NOT install Node.js dependencies unless specifically requested.

```python
from docx import Document
doc = Document()
# ... build document ...
doc.save('/path/to/output.docx')
```

**Confirmed working imports in this environment:**
```python
from docx import Document
from docx.shared import Pt, Inches, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
```

**Key API patterns (python-docx v1.2.0):**

```python
# Page margins
section = doc.sections[0]
section.page_width = Inches(8.5)
section.page_height = Inches(11)
section.left_margin = section.right_margin = section.top_margin = section.bottom_margin = Inches(1)

# Headings
p = doc.add_heading('Title', level=1)  # level 1-4
p.alignment = WD_ALIGN_PARAGRAPH.LEFT
p.runs[0].font.size = Pt(14)
p.runs[0].font.bold = True

# Body paragraph
p = doc.add_paragraph()
p.paragraph_format.space_after = Pt(6)
run = p.add_run('text')
run.font.size = Pt(11)

# Bullet
p = doc.add_paragraph(style='List Bullet')
run = p.add_run('text')
run.font.size = Pt(11)

# Page break (reliable method)
p = doc.add_paragraph()
pPr = p._p.get_or_add_pPr()
pBdr = OxmlElement('w:pageBreakBefore')
pPr.append(pBdr)

# Table with header row shading
def set_cell_bg(cell, hex_color):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_color)
    tcPr.append(shd)

# Table row
row = table.rows[r]
row.cells[0].text = 'value'
for cell in row.cells:
    set_cell_bg(cell, 'FFFFFF')
    for para in cell.paragraphs:
        for run in para.runs:
            run.font.size = Pt(9)
```

## Node.js Fallback (only if python-docx unavailable)

If for any reason python-docx is not available, fall back to Node.js `docx` npm package:

```bash
mkdir -p /tmp/node_proj && npm --prefix /tmp/node_proj install docx
```

Then use `require('/tmp/node_proj/node_modules/docx')` in a `.cjs` script.

> **Why not always use Node.js?** The skill's original guidance recommended Node.js because earlier versions of this skill claimed `pip` was unavailable. This is now outdated — python-docx works and is simpler for single-file document generation.

## Pitfalls

1. **Always use `Inches()` not `In`** — `In` does not exist in `docx.shared`. Use `Inches(1)` for all size values.
2. **Page break** — use `w:pageBreakBefore` XML trick shown above; do NOT use `run.add_break()` with a manually constructed `CT_Br` element — it throws `KeyError` on some versions.
3. **Table cell shading** — `ShadingType.CLEAR` is a Node.js docx constant, not python-docx. In python-docx, set shading via raw XML as shown above (`OxmlElement('w:shd')` with `w:val='clear'`, `w:color='auto'`, `w:fill=hex_color`).
4. **`paragraph_format.space_after`** — takes a `Pt()` value, not a plain number.

## Relevant Skills

- `curriculum-design` — contains the NESA UbD content structure, syllabus outcomes, glossary, and justification framework needed to fill the template
- `curriculum-design` also has a `references/document-extraction.md` covering how to extract text from PPTX/DOCX files for source analysis (zipfile+regex approach).

## Setup

```bash
npm config set cache /tmp/npm-cache
npm install --prefix /tmp/node_proj docx
```

## Quick-Start

1. Copy the template script at `templates/ubd_docx_gen.cjs` to your working directory
2. Fill in the `UNIT` constant with topic-specific content (year, stage, topic, outcomes, etc.)
3. Add remaining content sections (assessment, blocks, lessons, justification)
4. Run: `node ubd_docx_gen.cjs`
5. Output: `TEAC_5003_UbD_Filled.docx`

## Required Dependencies

```bash
npm config set cache /tmp/npm-cache
npm install --prefix /tmp/node_proj docx
```

Then `require('/tmp/node_proj/node_modules/docx')` in the script.

## Key API Patterns (docx v1.1.2)

```javascript
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  HeadingLevel, WidthType, ShadingType, TableLayoutType, VerticalAlign, PageBreak
} = require('/tmp/node_proj/node_modules/docx');

// Header cell (blue shading)
function hCell(text) {
  return new TableCell({
    children: [new Paragraph({ children: [new TextRun({ text, bold: true })], spacing: { after: 40 } })],
    shading: { fill: "D9E2F3", type: ShadingType.CLEAR, color: "auto" },
    verticalAlign: VerticalAlign.CENTER,
  });
}

function dCell(text) {
  return new TableCell({
    children: [new Paragraph({ children: [new TextRun({ text })], spacing: { after: 40 } })],
    verticalAlign: VerticalAlign.CENTER,
  });
}

function bCell(text) {
  return new TableCell({
    children: [new Paragraph({ children: [new TextRun({ text, bold: true })], spacing: { after: 40 } })],
    verticalAlign: VerticalAlign.CENTER,
  });
}

function row(cells) { return new TableRow({ children: cells }); }

function makeTable(rows) {
  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    layout: TableLayoutType.FIXED,
    rows,
  });
}

function pb() {
  return new Paragraph({ children: [new PageBreak()], spacing: { before: 0, after: 0 } });
}

// Build document
const doc = new Document({
  sections: [{
    properties: { page: { margin: { top: 1080, bottom: 1080, left: 1080, right: 1080 } } },
    children: [h1("Title"), makeTable([row([hCell("H"), dCell("Data")])]), pb(), /* more content */],
  }],
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync('/opt/data/cache/documents/Output.docx', buffer);
});
```

## Pitfalls

1. **opts spreading into TableCell** — always destructure `width` out first: `const { width, ...cellOpts } = opts`
2. **`.cjs` vs `.js`** — if `/tmp/package.json` has `"type": "module"`, use `.cjs` extension
3. **`ShadingType.CLEAR` requires `color: "auto"`** — without it, the table rendering throws `TypeError: Cannot read properties of undefined (reading 'slice')`
4. **`npm install` permission errors** — always use `--prefix /tmp/node_proj` to avoid `chown` failures on `/opt/data/home/.npm`

## Relevant Skills

- `curriculum-design` — contains the NESA UbD content structure, syllabus outcomes, glossary, and justification framework needed to fill the template
