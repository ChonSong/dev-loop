# Vision QA Prompting Examples (from session 2026-06-12)

## Resume QA (used successfully)

```
CRITICAL QA: I'm printing this resume as a physical document. Answer specifically:

1. BODY TEXT: Is the summary paragraph and experience bullet points readable at standard print scale, or are they too small compared to the section headings?
2. BLANK SPACE: What percentage of the page is unused white space at the bottom? Is it excessive?
3. LINE SPACING: Are the bullet points in Experience too tight/cramped or reasonably spaced for readability?
4. SIDEBAR TAGS: The blue skill badges (Python, FastAPI, etc.) in the left column — are they readable or too small?
5. OVERALL: What's the single biggest visual problem that needs fixing? Be very specific.
```

## Multi-page Resume QA

```
QA on page 2 of this resume. Specific:

1. BODY TEXT: Readable at print scale or too small?
2. BLANK SPACE: What percentage of this page is empty white space? Is it excessive?
3. LINE SPACING: Project bullet points — cramped or well-spaced?
4. CONTENT FIT: Does it look like the page was designed to be page 2, or leftover content that spilled over?
5. OVERALL: Single biggest visual problem on this page?
```

## Resume PDF QA (used 2026-06-15 — caught sidebar rendering bug)

After generating a styled HTML→PDF resume, take a full-page screenshot via Playwright, then:

```
CRITICAL QA: Resume PDF for "[Role]" role.
1. BODY TEXT: Readable or too small? Compare body text to headings.
2. BLANK SPACE: What % empty? Excessive?
3. LAYOUT: Two-column layout working? Any overflow? Fit 1 page?
4. SIDEBAR: Rendering as proper styled content (not raw HTML code)?
5. SKILL TAGS: Clean without ** artifacts or stray markers?
6. EXPERIENCE: Both jobs visible with correct bullet points?
7. PROJECTS: All projects visible?
8. OVERALL: Single biggest problem?
```

**Common failure mode:** If the sidebar shows raw HTML like `<aside class="sidebar">...` as rendered text, the template `.format()` has a variable interpolation bug — the sidebar variable is being `.join()`'d again when it's already a string. Check Python f-string/format call, not the HTML template.

## Image/Design QA

```
I need to evaluate this [design/mockup/screenshot]. Be specific:

1. FONT LEGIBILITY: Can you read all the text easily?
2. SPACING CONSISTENCY: Are margins, padding, and gaps uniform?
3. ALIGNMENT: Are elements properly aligned in a grid or hierarchy?
4. COLOR CONTRAST: Is there sufficient contrast between text and background?
5. OVERALL: What's the single thing that looks most wrong?
```

## Quantitative Backup (Python)

```python
import fitz
doc = fitz.open('file.pdf')
page = doc[0]

# Get font size distribution
spans = []
for b in page.get_text('dict')['blocks']:
    if 'lines' in b:
        for line in b['lines']:
            for s in line['spans']:
                if s['text'].strip():
                    spans.append({'text': s['text'].strip()[:60], 'size': round(s['size'], 1)})

from collections import Counter
sizes = Counter(s['size'] for s in spans)
for sz, cnt in sorted(sizes.items()):
    print(f'  {sz}pt: {cnt}')

# Calculate blank space (PDF coords, A4 = 842pt high)
max_y = max(s['bbox'][3] for s in spans)
blank_pct = (842 - max_y) / 842 * 100
print(f'Blank: {blank_pct:.0f}%')
doc.close()
```
