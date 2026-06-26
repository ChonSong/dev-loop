# Document Extraction Techniques

## Extracting text from PPTX (Office Open XML)

PPTX and DOCX files are ZIP archives. Extract readable text with Python's `zipfile` + `re`:

### PPTX text extraction
```python
import zipfile, re

with zipfile.ZipFile('presentation.pptx', 'r') as z:
    for name in z.namelist():
        if 'slide' in name and name.endswith('.xml'):
            content = z.read(name).decode('utf-8')
            texts = re.findall(r'<a:t>([^<]*)</a:t>', content)
            print(' | '.join(texts))
```

### DOCX text extraction
```python
import zipfile, re

with zipfile.ZipFile('document.docx', 'r') as z:
    content = z.read('word/document.xml').decode('utf-8')
    texts = re.findall(r'<w:t[^>]*>([^<]*)</w:t>', content)
    print('\n'.join(texts))
```

## Key grep patterns for placeholder detection

```bash
# After generating PPTX — check for leftover placeholders
python -m markitdown output.pptx | grep -iE "xxxx|lorem|ipsum|placeholder|click.*(icon|image|picture)"

# After generating DOCX — similar check
python -m markitdown output.docx | grep -iE "xxxx|lorem|ipsum|placeholder"
```

## LibreOffice conversion for visual QA

```bash
# PPTX → PDF for thumbnail generation
python scripts/office/soffice.py --headless --convert-to pdf output.pptx

# PDF → individual slide images
pdftoppm -jpeg -r 150 output.pdf slide
# Creates slide-01.jpg, slide-02.jpg, ...
```

## Word counting (for justifications)

```python
import re
with open('document.md', 'r') as f:
    content = f.read()

ref_idx = content.find('## References')  # or the references section marker
body = content[:ref_idx]
body_lines = [l for l in body.split('\n') if not l.startswith('#')]
body_text = ' '.join(body_lines)
words = re.findall(r"[a-zA-Z']+", body_text)
print(f'Body word count: {len(words)}')
```

Target: ~500 words for NESA justification (body only, excluding references section).