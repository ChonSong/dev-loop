# Document QA Verification Process

## Verification Checklist (Rigor — Do NOT skip steps)

For every generated document/PDF, run these checks in order:

### 1. Programmatic Checks (PyMuPDF)
```python
import fitz
doc = fitz.open(path)

# Page count
assert doc.page_count == expected, f"Expected {expected} pages, got {doc.page_count}"

# Section presence
full_text = ""
for i in range(doc.page_count):
    full_text += doc[i].get_text()
    
checks = ["Sean Cheong", "SKILLS", "SUMMARY", "EXPERIENCE", "PROJECTS", "EDUCATION"]
missing = [c for c in checks if c not in full_text.upper()]
# NOTE: CSS text-transform: uppercase renders headings as uppercase in PDF text

# Rendered font size (NOT CSS value)
blocks = doc[0].get_text('dict')['blocks']
for b in blocks:
    for line in b.get('lines', []):
        text = ''.join([s['text'] for s in line['spans']])
        if 'target text substring' in text.lower():
            actual_pt = line['spans'][0]['size']
            # 9pt body = good. <7pt = too small. >11pt may overflow.

# Blank space measurement
last_y = 0
for b in blocks:
    for line in b.get('lines', []):
        for s in line['spans']:
            if s['text'].strip():
                last_y = max(last_y, line['bbox'][3])
blank_pct = (297 - last_y) / 297 * 100  # A4 = 297mm tall
# Flag if >20% blank on any page
```

### 2. Issues to flag immediately
- Page count != expected → adjust CSS (fonts too large/small, spacing)
- Body text < 8pt rendered → increase CSS font-size (use pt units!)
- Blank space > 20% of page → expand content or increase spacing
- Content section missing → check CSS `overflow` or broken HTML
- File size suspicious (< 200 KB for styled PDF) → check if rendering actually happened

### 3. Vision Check (Secondary — Only After Programmatic Checks Pass)
Run `vision_analyze` with SPECIFIC prompts, NOT generic "rate 1-10":
```
- What is the body text font size relative to the page? Too small or readable?
- How much blank space is at the bottom of each page (percentage)?
- Any cut-off text or overlapping elements?
- Is spacing between sections comfortable or cramped?
```

### 4. User Review
- Always send user the final output to review
- Ask: "Does this meet your acceptance criteria?"
- If rejected, ask specifically what needs to change (don't guess)

## Golden Path (Verified Working)
HTML + Tailwind CDN + Google Fonts + Font Awesome
  → SCP to host 172.19.0.1 via container_key
  → chrome-stable --headless --no-sandbox --print-to-pdf --no-margins
  → SCP PDF back
  → PyMuPDF page count + section check + font size measurement
  → vision_analyze with specific legibility prompts
  → User review

## Tools That Don't Work
- fpdf2: rejected — can't replicate two-column CSS layouts
- weasyprint: missing system libs in container
- Playwright: chromium missing system libs in container, can't render text
- in-container wkhtmltopdf: not installed, can't install (no root)

## SSH Access
- Key: `/home/hermeswebui/.hermes/container_key`
- Host: `172.19.0.1`
- User: `sean`
- This key may be replaced mid-session — check `ls -la /home/hermeswebui/.ssh/` if original key stops working
