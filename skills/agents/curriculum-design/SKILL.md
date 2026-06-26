---
name: curriculum-design
description: "Design NESA UbD (Understanding by Design) Stage 3 units of work for Commerce and related subjects — Scope & Sequence, lesson plans with original resources, and 500-word justifications."
version: 1.0.0
license: MIT
metadata:
  hermes:
    tags: [education, curriculum, UbD, NESA, lesson-planning, assessment]
    related_skills: [writing-plans, powerpoint]
---

# Curriculum Design — NESA UbD Units

## When to Use

Trigger when the user asks to:
- Design a unit of work using Understanding by Design (UbD)
- Create lesson plans for a NESA Commerce, Business Studies, or related subject
- Write a 500-word justification linking UbD to QTM, AITSL, and NESA continuums
- Produce assessment tasks, rubrics, or scaffolded resources for Stage 5/6

## Prerequisites

Before writing anything, extract and read the source documents:
1. The assignment brief/task description (from PPTX or DOCX)
2. The syllabus content (from the Scope & Sequence DOCX)
3. The UbD template structure
4. The NESA outcomes codes

**Extraction technique for PPTX/DOCX:**
```python
import zipfile, re
with zipfile.ZipFile('filename.pptx', 'r') as z:
    for name in z.namelist():
        if 'slide' in name and name.endswith('.xml'):
            content = z.read(name).decode('utf-8')
            texts = re.findall(r'<a:t>([^<]*)</a:t>', content)
            print(' | '.join(texts))
```

## UbD Stage 3 Unit Structure

### Page 1 — Unit Overview (Cover Page)
```
| Field | Detail |
| Year & Stage | e.g., Year 10, Stage 5 |
| Core Topic | e.g., The Work Environment |
| Duration | 25 hours — Term 3 (8–10 weeks) |
| Unit Focus | 2-3 sentence overview of what students will learn |
| Key Inquiry Questions | Numbered list (3-4 questions driving the unit) |
| Syllabus Outcomes | CO5-COM-01, CO5-RRI-01, etc. in full + Life Skills codes |
| Prior Learning | What students already know from earlier units |
| Differentiation | UDL framework notes — content/process/product for diverse learners |
```

### Page 2 — Assessment Summary
- **Assessment for learning**: Pre-tests, exit tickets, observation checklists, learning journals
- **Assessment as learning**: Peer feedback tasks, self-assessment against criteria, ICT quizzes
- **Assessment of learning (summative)**: Formal task with name, due date, weighting, outcomes assessed
- Include the formal task descriptor (cut from Assignment 1)

### Pages 3–7 — 5-Hour Teaching Blocks
One block per page (landscape orientation):
```
| Content | Teaching & Learning Strategies | Resources | Assessment |
```
5 blocks × 5 hours = 25 hours total (one term)

## Three Lesson Plans — Required Structure

Each 60-minute lesson must include:

| Component | Detail |
|---|---|
| Date/Duration | Term X, Week Y — 60 minutes |
| Learning Objectives | 2-3 objectives (students will be able to...) |
| Syllabus Outcomes | CO5 codes in full |
| Differentiation | EAL/D, disability, extension — specific strategies |
| Lesson Sequence | Time-stamped table: 0–5 min, 5–15 min, etc. |
| Original Resources | Named and fully described |

**Three mandatory original resources:**
1. **Pre-test** (Lesson 1) — diagnostic MCQ + short answer, 10 questions, extension questions on back
2. **ICT Resource** (Lesson 2) — interactive quiz (Google Forms/Genially), scenario-based, instant feedback
3. **Literacy Writing Activity** (Lesson 3) — TEEC scaffold (Topic/Evidence/Explanation/Citation) or equivalent

**Lesson 3 literacy rubric elements:**
- Topic sentence (clear position statement)
- Evidence ( Fair Work Act / NES citation)
- Explanation (links evidence to argument)
- Citation (APA 7th in-text)

## 500-Word Justification — Required Sections

Word count: 500 words (body only; references are additional)

Must cover ALL five:
1. **UbD** — Wiggins & McTighe (2005) backward design process; goals → assessment → instruction alignment
2. **QTM** — NSW DoE (2003): Quality Learning Environment, Explicit Quality Feedback, Deep Understanding
3. **AITSL** — AITSL (2020): Standards 2.1, 3.2, 5.1 minimum
4. **NESA Learning Continuums** — NESA (2019): Literacy/Numeracy continuums and differentiation
5. **Syllabus alignment** — NESA (2024): explicit outcome codes linked to activities

**References (APA 7th):**
- AITSL (2020) Australian Professional Standards for Teachers
- Fair Work Ombudsman — relevant pages
- NESA (2019) Learning Continuums
- NESA (2024) Commerce Stage 5 Syllabus
- NSW DoE (2003) Quality Teaching Model
- Wiggins & McTighe (2005) Understanding by Design, 2nd ed.

## Creating Filled DOCX Templates (Node.js docx)

`python-docx` is often unavailable in the Hermes container (no `pip`, no `ensurepip`). Use the **Node.js `docx` npm package** instead:

```bash
npm config set cache /tmp/npm-cache
npm install --prefix /tmp/node_proj docx
```

Then `require('/tmp/node_proj/node_modules/docx')`.

**Reliable docx API patterns (v1.1.2):**

```javascript
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  HeadingLevel, WidthType, ShadingType, TableLayoutType, VerticalAlign, PageBreak
} = require('/tmp/node_proj/node_modules/docx');

// Helper — header cell (blue shading)
function hCell(text) {
  return new TableCell({
    children: [new Paragraph({ children: [new TextRun({ text, bold: true })], spacing: { after: 40 } })],
    shading: { fill: "D9E2F3", type: ShadingType.CLEAR, color: "auto" },
    verticalAlign: VerticalAlign.CENTER,
  });
}

// Helper — data cell
function dCell(text) {
  return new TableCell({
    children: [new Paragraph({ children: [new TextRun({ text })], spacing: { after: 40 } })],
    verticalAlign: VerticalAlign.CENTER,
  });
}

// Helper — bold data cell
function bCell(text) {
  return new TableCell({
    children: [new Paragraph({ children: [new TextRun({ text, bold: true })], spacing: { after: 40 } })],
    verticalAlign: VerticalAlign.CENTER,
  });
}

// Table row
function row(cells) {
  return new TableRow({ children: cells });
}

// Heading paragraphs
function h1(text) {
  return new Paragraph({ text, heading: HeadingLevel.HEADING_1, spacing: { before: 300, after: 150 } });
}
function h2(text) {
  return new Paragraph({ text, heading: HeadingLevel.HEADING_2, spacing: { before: 200, after: 100 } });
}
function p(text) {
  return new Paragraph({ children: [new TextRun({ text })], spacing: { after: 80, line: 276 } });
}

// Page break
function pb() {
  return new Paragraph({ children: [new PageBreak()], spacing: { before: 0, after: 0 } });
}

// Build table
new Table({
  width: { size: 100, type: WidthType.PERCENTAGE },
  layout: TableLayoutType.FIXED,
  rows: [
    row([hCell("Header"), hCell("Header")]),
    row([bCell("Bold Label"), dCell("Value")]),
  ],
});

// Document
const doc = new Document({
  sections: [{
    properties: { page: { margin: { top: 1080, bottom: 1080, left: 1080, right: 1080 } } },
    children: [ /* paragraphs, tables, page breaks */ ],
  }],
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync('/output/path.docx', buffer);
});
```

**Pitfalls with docx API:**
- Never spread opts into `TableCell` — destructured `width` first, pass the rest as `...cellOpts`
- `ShadingType.CLEAR` requires `color: "auto"` explicitly
- Use `.cjs` extension (not `.js`) if `/tmp/package.json` has `"type": "module"`
- `TableLayoutType.FIXED` prevents width calculation errors

## Common Pitfalls

- **Outcome codes**: Always write full codes (CO5-COM-01), not abbreviated versions
- **Word count on justification**: Count excluding headers and references; aim for 500–520 words body
- **Differentiation**: Be specific — name the strategy (e.g., "EAL/D: bilingual glossary cards"), not just "differentiated"
- **Resources**: All original resources must be named and fully described within the lesson plan
- **APA 7th**: In-text citations use (Author, year); references use hanging indent, correct capitalisation
- **DOCX output**: Alto prefers `.docx` filled template, not markdown outlines. Always produce both.
- **DOCX via Node.js**: `pip` unavailable in Hermes — use `npm install --prefix /tmp/node_proj docx` instead
- **Outcome codes**: Always use current NESA 2024 CO5-XXX-01 codes — NOT legacy COM5-1/COM5-2 codes found in older templates. TEAC 5003 (2026) uses the current format.

## References

- `references/nesa-commerce-syllabus.md` — NESA Stage 5 Commerce syllabus extracts: core topic structure, The Work Environment content/outcomes/glossary, Assignment 1 task descriptor, 500-word justification framework
- `references/document-extraction.md` — Python techniques for extracting PPTX/DOCX text via zipfile+regex, placeholder detection, visual QA conversion, word counting
- `references/teac5019-mathematics.md` — TEAC 5019 Mathematics Stage 5 reference bank: NESA outcomes, pedagogical framework (constructivism, fading technique, differentiation), proven 5-week Algebraic Techniques→Functions unit design, three-resource design patterns, APA 7th core citation set, word budget guidance

## Output Files

Produce both:
1. Markdown files (for drafting/editing): `Unit_of_Work_UbD_[Topic].md`, `Lesson_Plans_[Topic].md`, `500_Word_Justification.md`
2. Filled DOCX template (for submission) — use the `ubd-docx-generator` skill to create `TEAC_5003_UbD_Work_Environment_Filled.docx`

## Related Skills

- **`ubd-docx-generator`** — generates filled `.docx` UbD templates using Node.js `docx` npm package. Use this when the user asks for a Word document output. Installs `docx` to `/tmp/node_proj` (no `pip` needed in Hermes).