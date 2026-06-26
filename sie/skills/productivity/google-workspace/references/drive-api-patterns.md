# Drive API — Working Patterns & Gotchas

## List folder contents (children)

The `folderId` parameter is the correct approach for listing a folder's direct children:

```python
url = f"https://www.googleapis.com/drive/v3/files?folderId={folder_id}&fields=files(id,name,mimeType,modifiedTime,webViewLink)&pageSize=50"
req = urllib.request.Request(url, headers={"Authorization": f"Bearer {access_token}"})
```

**Note:** The `drive search` command in `google_api.py` does NOT support `folderId` as a parameter — it only accepts a plain text query. Using `folderId` via the search endpoint returns `400 Invalid Value`.

## Search within a folder

The Drive API doesn't support `name contains 'X' and 'Y' in parents` compound queries the same way the UI does. Use the children endpoint for folder traversal; use simple text search for global file discovery.

## Token access

The token file stores the access token under the key `"token"`, NOT `"access_token"`:

```python
with open(token_path) as f:
    token = json.load(f)
access_token = token["token"]  # NOT token["access_token"]
```

## Downloading binary files (PDF, DOCX, etc.)

Use `?alt=media` on the file endpoint:

```python
url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media"
req = urllib.request.Request(url, headers={"Authorization": f"Bearer {access_token}"})
with urllib.request.urlopen(req) as r:
    data = r.read()
```

## PDF text extraction

`pdftotext` (poppler) is not installed in the sandbox. Use `pymupdf` (`fitz`) instead:

```python
import subprocess
subprocess.run(["pip", "install", "pymupdf", "-q"])
import fitz
doc = fitz.open("/tmp/resume.pdf")
text = "".join(page.get_text() for page in doc)
```

## Confirmed working API endpoints

| Purpose | Endpoint |
|---------|----------|
| List folder children | `GET /drive/v3/files?folderId={id}&fields=files(...)&pageSize=50` |
| Get file metadata | `GET /drive/v3/files/{id}` |
| Download binary | `GET /drive/v3/files/{id}?alt=media` |
| Search all files | `GET /drive/v3/files?q={query}&fields=files(...)` |

## Common errors

- `400 Invalid Value` on search — query string is malformed or uses unsupported operators
- `400` on children with `q=` — `folderId` param must be a query param, not inside the `q` string
- Token missing scopes — re-run `$GSETUP --revoke` then re-authenticate