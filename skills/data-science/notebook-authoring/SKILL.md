---
name: notebook-authoring
description: Create Jupyter notebooks (.ipynb) programmatically via Python generator scripts. Covers notebook JSON structure, cell authoring, lint verification, and Drive upload.
category: data-science
triggers:
  - user asks to create a notebook, .ipynb, Jupyter file, or interactive tutorial
  - task involves producing executable code cells with explanatory markdown
  - user wants coded examples alongside written guidance
  - delivering a data exercise, workshop, or interactive training material
---

# Notebook Authoring

Create rich .ipynb notebooks by writing Python generator scripts. This avoids raw JSON editing and gives you linting/validation before the notebook is built.

## Workflow

```
Write gen_notebook.py → python3 gen_notebook.py → AGGP_*.ipynb → Upload to Drive
```

## Notebook JSON Structure

Every .ipynb requires this skeleton:

```python
notebook = {
    "nbformat": 4,
    "nbformat_minor": 4,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "name": "python",
            "version": "3.10.0"
        }
    },
    "cells": [...]
}

with open("output.ipynb", "w") as f:
    json.dump(notebook, f, indent=1)
```

## Cell Functions

Write helper functions to avoid repeating JSON boilerplate:

```python
# Markdown cell
def M(lines):
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [s + '\n' for s in lines]
    })

# Code cell
def C(lines):
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [s + '\n' for s in lines]
    })
```

### Cell Types and Their Structure

| Cell Type | Key Fields | Notes |
|-----------|-----------|-------|
| markdown | cell_type='markdown', source=[...] | source is a list of strings (one per line) |
| code | cell_type='code', execution_count=None, outputs=[], source=[...] | outputs empty on creation |
| raw | cell_type='raw', source=[...] | Rarely used; for nbconvert |

## Writing Cell Content

**Pass lines as a LIST of strings** — this avoids escaping issues with multiline strings embedded in Python:

```python
# GOOD: list of lines
M([
'# Title',
'',
'Some **bold** text.',
])

# BAD: single multi-line string that contains unescaped quotes
M("""Some text with "quotes" and apostrophe's""")
```

### String Escaping Pitfalls

When building the generator script (which itself is a Python file), watch for:

1. **Triple-quote nesting** — if a cell contains ```python or """ inside it, use single-line lists to avoid closing the outer string
2. **Apostrophes in strings** — "can't", "don't", "it's" inside single-quoted strings cause SyntaxError. Use double quotes for the outer delimiters, or use the list-of-lines pattern above
3. **Trailing backslash in ASCII art** — `\'` at the end of a single-quoted Python string is an *escaped single quote*, not a backslash character. Python includes the quote in the string content (string never closes), producing `SyntaxError: unterminated string literal`. **Fix:** double the backslash — `\\'` produces a literal backslash followed by the closing quote:
   ```python
   # BROKEN: \\' is an escaped quote, string continues past the comma
   '                 /        \\',
   
   # FIXED: \\\\' produces a literal \\, then ' closes the string
   '                 /        \\\\',
   ```
4. **Backslash escaping** — regex patterns like `r'[^a-z0-9_]'` in f-strings need doubled braces `{{` and `}}` for literal braces

```python
# APOSTROPHE FIX: Use list of lines instead of a single string
# This avoids the "can't" problem:
M([
'Generate realistic datasets. Each run creates different data so you cannot memorise answers.',
])
```

## Verification Steps

1. **Lint the generator script** — `write_file` auto-runs Python syntax check. If it reports errors, fix before executing.
2. **Run the generator** — `python3 gen_notebook.py` must exit cleanly
3. **Verify the notebook** — check `jupyter nbconvert --to script --stdout file.ipynb | head` or just inspect the JSON
4. **Check cell counts** — confirm markdown + code cells match expectations
5. **Remove the generator script** — clean up `gen_notebook.py` after successful generation unless it serves as documentation

## Uploading to Drive

```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Get credentials from the google_api helper
sys.path.insert(0, "/path/to/google_api/dir")
from google_api import get_credentials

creds = get_credentials()
service = build('drive', 'v3', credentials=creds)

# .ipynb MIME type might not be in the upload script's dict
# Add it if missing: '.ipynb': 'application/x-ipynb+json'

media = MediaFileUpload(str(file_path), mimetype=mime_type, resumable=True)
file = service.files().create(body=metadata, media_body=media, fields='id, webViewLink').execute()

# Make publicly shareable
permission = {'type': 'anyone', 'role': 'reader'}
service.permissions().create(fileId=file_id, body=permission).execute()
```

## Common Pitfalls

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| Unexpected SyntaxError in generator | Python fails to parse gen_notebook.py at a line with `\'` | Trailing backslash in single-quoted string is an escaped quote, not a literal backslash. Use `\\'` instead. |
| Manual cell edit lost on regenerate | Manually patched the .ipynb JSON, then re-ran gen_notebook.py — handwritten cell is gone | Decide: patch the generator OR the notebook. Never both. Regenerating from the generator overwrites all manual JSON edits. |
| Notebook doesn't render in Jupyter | JSON is malformed | Validate with `json.load()` before writing. Check nbformat = 4. |
| Drive upload returns no link or 404 | MIME type missing from upload script's dict | Add `'.ipynb': 'application/x-ipynb+json'` to the MIME type dictionary before the `mime_types.get()` fallback. |
| Code cells missing `execution_count` | Cells show "In [ ]" instead of "In [1]" | Set `execution_count: None` for all new code cells |
| Notebook too large | >10MB triggers slow rendering | Reduce output bloat. Use `%%capture` for heavy cells. |
