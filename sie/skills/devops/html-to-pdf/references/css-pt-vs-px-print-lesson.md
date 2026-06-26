# CSS `pt` vs `px` for Print — Lesson from June 2026

## The Problem

CSS `px` values are not rendered at the same size in Chrome headless PDF output. Chrome converts:
- **1px → ~0.75pt** in print

This means `font-size: 9px` in CSS renders as `~6pt` in the PDF — far too small for a printed resume.

## How We Found It

The user complained twice that the PDFs looked "awful" with "small font size." We had CSS at `9.5px` but the PDF extracted showed body text at `6.4pt`. After switching to `9pt`, body text rendered at exactly `9.0pt` in the PDF.

## The Fix

**Use `pt` units for ALL sizes in print CSS, never `px`.**

| CSS | Rendered in PDF | Verdict |
|-----|-----------------|---------|
| `font-size: 9px` | ~6pt | Too small |
| `font-size: 9pt` | 9pt | Good |
| `font-size: 10pt` | 10pt | Good for body text |
| `padding: 8px` | ~6pt in print | Too tight |
| `padding: 8pt` | 8pt | Good |

This applies to: `font-size`, `padding`, `margin`, `line-height` (unitless is fine), `gap`, and spacing properties.

## How to Verify

After generating a PDF, check what actually rendered:

```python
doc = fitz.open(pdf_path)
page = doc[0]
blocks = page.get_text('dict')['blocks']
body_sizes = set()
for b in blocks:
    if 'lines' in b:
        for line in b['lines']:
            text = ''.join([s['text'] for s in line['spans']])
            if text.strip().startswith('Body text start'):
                body_sizes.add(f"{line['spans'][0]['size']:.1f}pt")
print(f"Body text rendered at: {body_sizes}")
doc.close()
```

If body text renders below 7pt when you expected 9pt+, the CSS used `px` instead of `pt`.

## Page Break Balance Lesson

When using proper `pt` font sizes, forced page breaks (`page-break-before: always`) cause 3-page overflow. The fix:

**Remove the hard page break entirely.** Let Chrome auto-paginate. Use `keep-together` on individual blocks to prevent bad splits. The auto-pagination produces clean 2-page output.

```html
<!-- BAD: forced break causes 3 pages with proper font sizes -->
<div class="page-break"></div>

<!-- GOOD: no break, Chrome auto-handles pagination -->
<!-- (remove the page-break div entirely) -->
```