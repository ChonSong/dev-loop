---
name: teac-assignment-writing
description: "Write TEAC (Teacher Education) university assignment portfolios for NSW pre-service teachers. Covers Stage 4–5 Mathematics and HSIE, UBD planning, APA 7th referencing, and DOCX generation from course materials."
version: 1.0.0
author: Hermes Agent
platforms: [linux, macos]
metadata:
  hermes:
    tags: [university, teaching, assignment, NSW, QCT, UBD, mathematics, curriculum]
    related_skills: [ubd-docx-generator, ocr-and-documents, google-workspace]
---

# TEAC Assignment Writing

Write TEAC (Teacher Education) university assignment portfolios for NSW pre-service teachers. Primary use case: TEAC 5019 / TEAC 5020 / TEAC 7157 and similar teacher education subjects requiring Stage 4–5 Mathematics or HSIE subject outlines with UBD framework.

## Workflow

### Step 1: Locate and Extract Source Materials

Students typically submit course materials as a ZIP file downloaded from Turnitin or a learning management system.

```bash
# SSH to host to find the zip in Downloads
ssh -i /home/hermeswebui/.hermes/container_key sean@172.19.0.1 "ls ~/Downloads/*.zip"

# Copy zip from host to container
ssh -i /home/hermeswebui/.hermes/container_key sean@172.19.0.1 "cat /home/sean/Downloads/TEAC5019*.zip" > /workspace/TEAC5019.zip

# Extract using Python (no unzip needed in container)
python3 -c "import zipfile; zipfile.ZipFile('/workspace/TEAC5019.zip').extractall('/workspace/TEAC5019_extracted/')"

# List extracted contents
python3 -c "
import os
for root, dirs, files in os.walk('/workspace/TEAC5019_extracted'):
    for f in files:
        fp = os.path.join(root, f)
        print(f'{os.path.getsize(fp)//1024}KB  {fp}')
"
```

### Step 2: Read All Documents

Use `python-docx` for Word files, `pymupdf` for PDFs. Do NOT try to use `node`, `npm`, or the Node.js `docx` package — it is not available in this container.

```python
# Read DOCX
from docx import Document
doc = Document('/path/to/file.docx')
paras = [p.text.strip() for p in doc.paragraphs if p.text.strip()]

# Read PDF text
import fitz  # PyMuPDF
doc = fitz.open('/path/to/file.pdf')
for i, page in enumerate(doc):
    text = page.get_text()
    if text.strip():
        print(f'--- Page {i+1} ---')
        print(text[:2000])
```

### Step 3: Build Sources Summary

Write a consolidated reference bank to `/workspace/TEAC5019_sources.md` capturing:
- Assignment requirements and rubric criteria
- NESA syllabus codes (MA5-*, C1/C2/P/SP suffix meanings)
- Core vs Path vs Life Skills content distinctions
- Academic references found in course materials

### Step 4: Walk the Design Tree (Collaborative)

Walk one branch at a time with user:

| Branch | Decision |
|--------|----------|
| 1 | Topic selection (core + path pairing) |
| 2 | Class context (year level, stream, diversity) |
| 3 | Duration and lesson structure |
| 4 | Assessment approach |
| 5 | Digital artefact selection |
| 6 | Resource selection |
| 7 | Rationale structure |
| 8 | Draft writing + DOCX generation |

If user says "you decide", make informed assumptions and document them for user review before finalising.

### Step 5: Generate DOCX via python-docx

Use `python-docx` (NOT Node.js docx). Write a build script, run it, verify output.

```python
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

doc = Document()
section = doc.sections[0]
section.page_width  = Inches(8.5)
section.page_height = Inches(11)
section.left_margin = section.right_margin = Inches(1)
section.top_margin  = section.bottom_margin = Inches(1)

# Page break (use OxmlElement approach — add_break does not work reliably)
def pagebreak():
    p = doc.add_paragraph()
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pageBreakBefore')
    pPr.append(pBdr)

doc.save('/workspace/output.docx')
```

### Step 6: Build Separate Resource DOCX Files

Each resource (formative assessment, digital artefact, path investigation) gets its own DOCX file.

---

## NESA Mathematics Syllabus Quick Reference

### Code Format: MA5-ALG-C-01
- **MA5** = Stage 5 (Year 9–10)
- **ALG** = topic (ALG algebra, LIN linear, FNC functions, TRG trigonometry, IND indices)
- **C** = Core | **P** = Path | **SP** = Life Skills
- **N-A** = Number and Algebra strand

### Common Stage 5 Topics
| Code | Topic |
|------|-------|
| MA5-ALG-C-01 | Algebraic Techniques A — simplify/expand algebraic fractions |
| MA5-LIN-C-01 | Linear Relationships — graphing, gradient, intercepts |
| MA5-FNC-P-01 | Functions — function notation, graphing, inequalities |
| MA5-IND-P-01 | Exponential Functions — indices, logarithms link |

---

## APA 7th Quick Reference

```text
Journal: Author, A. A., & Author, B. B. (Year). Title. Journal, Vol(Issue), pages. https://doi.org/

Book: Author, A. A. (Year). Title (ed.). Publisher.

NESA: NSW Education Standards Authority. (2022). Mathematics K–10 2022. NESA.

Lecture (unpublished): Lecturer, A. (Year). Topic [Lecture notes]. Institution.
```

---

## UBD Framework Reference

**Stage 1 — Identify Desired Results:** outcomes, essential questions, big ideas,迁移
**Stage 2 — Evidence:** performance tasks, success criteria, formative checks
**Stage 3 — Learning Plan:** before/during/after; differentiation (core + extension + path)