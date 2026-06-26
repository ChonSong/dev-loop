# Google Drive Upload Workaround

The `google_api.py` CLI only supports `drive search` and `drive download` — it does NOT have a `drive upload` command. The SKILL.md documents `drive upload` in the usage section but this is aspirational; the CLI returns `invalid choice: 'upload'` if you try it.

## Working Upload Script

When you need to upload a file to Drive, use this Python script (already created at `/workspace/scripts/upload_drive.py`):

```bash
python3 /workspace/scripts/upload_drive.py <file_path> [file_name]
```

This script:
1. Imports `get_credentials()` from `google_api.py` (reuses existing OAuth token)
2. Uses `googleapiclient` directly to upload the file
3. Sets the file to "anyone with link can view" (reader permission)
4. Returns the shareable link

## Verification

Tested and working — used to upload resume files and generate shareable links.
