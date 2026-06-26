# Worked Example: Resume PDF Visual QA

This is the QA workflow and prompts used during the 2026-06-12 session to assess a 2-page resume PDF rendered via Chrome headless.

## Context

- **Artifact:** 2-page resume PDF (A4, printed at standard scale)
- **Purpose:** Physical document that needs to look professional when printed
- **Render method:** HTML → Chrome headless → PDF → PyMuPDF PNG extraction (200 DPI)
- **Model used:** minimax-m3 via opencode-go (after fixing vision provider auth)

## Prompt Template Used

### Page 1 Prompt

```
CRITICAL QA: I'm printing this resume as a physical document. Answer specifically:

1. BODY TEXT SIZE: Is the summary paragraph and the experience bullet 
   points readable at standard print scale, or are they too small compared 
   to the section headings?

2. BLANK SPACE: What percentage of the page is unused white space at the 
   bottom? Is it excessive?

3. LINE SPACING: Are the bullet points in Experience too tight/cramped or 
   reasonably spaced for readability?

4. SIDEBAR TAGS: The blue skill badges (Python, FastAPI, etc.) in the left 
   column — are they readable or too small?

5. OVERALL: What's the single biggest visual problem that needs fixing? 
   Be very specific.
```

### Page 2 Prompt

```
QA on page 2 of this resume. Specific questions:

1. BODY TEXT: Readable at print scale or too small?
2. BLANK SPACE: What percentage of the page is empty white space? Is it 
   excessive?
3. LINE SPACING: Project bullet points - cramped or well-spaced?
4. CONTENT FIT: Does it look like this page was designed to be page 2, or 
   does it feel like leftover content that spilled over?
5. OVERALL: Single biggest visual problem on this page?
```

## Findings

| Metric | Page 1 | Page 2 |
|--------|--------|--------|
| Body text | "requires closer inspection" — slightly small | OK |
| Blank space | ~30% — acceptable | ~60% — excessive |
| Line spacing | Good | Good |
| Tags/badges | Readable but small | N/A |
| Font hierarchy | Headings too large vs body | Minimal visual hierarchy |
| Biggest issue | Font size ratio off | Content too thin for 2 pages |

## Lessons

1. **Split multi-page documents** — QA each page separately, don't assume page 1 represents the whole
2. **Quantity the blank space** — Ask for percentage estimates to identify waste
3. **Compare to reference** — "Compared to section headings" gives a relative anchor for the vision model
4. **State the use case explicitly** — "I'm printing this as a physical document" changes what "too small" means vs screen
