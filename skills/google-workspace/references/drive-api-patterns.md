# Drive API — Working Patterns & Gotchas

## CLI Syntax (google_api.py)

### Search
```bash
GAPI="python ${HERMES_HOME:-$HOME/.hermes}/skills/productivity/google-workspace/scripts/google_api.py"

# Simple search (quoted string)
$GAPI drive search "quarterly report" --max 10

# Complex queries with quotes inside — use --raw-query to avoid shell quoting issues
$GAPI drive search --raw-query "fullText contains 'resume' and mimeType != 'application/vnd.google-apps.folder'" --max 20
```

**Gotcha:** Single quotes inside double-quoted strings get mangled by the CLI argument parser. Always use `--raw-query` for queries containing quotes or special characters.

### Download
```bash
# File ID is POSITIONAL — NOT --file-id
$GAPI drive download FILE_ID --output /workspace/resumes/resume.pdf

# For Google-native files (Docs), export to pdf:
$GAPI drive download DOC_ID --output resume.pdf

# For docx files:
$GAPI drive download DOC_ID --output resume.docx
```

**Gotcha:** `drive download --file-id FILE_ID` will error with `unrecognized arguments`. The file_id is a positional argument. Always use `--output` to specify local path (otherwise defaults to CWD with original filename).

### Upload
```bash
$GAPI drive upload /path/to/file.docx --name "Custom Name.docx"
```

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
- `unrecognized arguments: --file-id` — file_id is positional, not a flag

## Auth token expiry

OAuth tokens can expire or be revoked. If any drive command fails with auth errors:

```bash
GSETUP="python ${HERMES_HOME:-$HOME/.hermes}/skills/productivity/google-workspace/scripts/setup.py"
$GSETUP --auth-url
# User opens URL in browser, copies redirected URL with code= parameter
$GSETUP --auth-code "PASTE_CODE_OR_FULL_URL_HERE"
```

The `--auth-code` accepts either the full redirected URL (`http://localhost:1/?code=...&state=...`) or just the bare code string. Both work. The state parameter is ignored internally.
