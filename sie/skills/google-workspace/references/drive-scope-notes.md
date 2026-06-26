# Drive Scope Notes — June 2026

## `drive.readonly` vs `drive.file`

The original OAuth scopes included `https://www.googleapis.com/auth/drive.readonly`, which is **insufficient for file uploads.** The API call `files().create()` returns `HttpError 403: Insufficient Permission` when the token only has read-only Drive access.

**Fix:** Change scope to `https://www.googleapis.com/auth/drive.file`:

```python
# In setup.py and google_api.py, change:
"https://www.googleapis.com/auth/drive.readonly",
# to:
"https://www.googleapis.com/auth/drive.file",
```

Then re-authenticate (the old token will fail to refresh because scopes changed):

```
$GSETUP --revoke
$GSETUP --auth-url  # generates new URL with drive.file scope
<user authorizes>
$GSETUP --auth-code <code>
$GSETUP --check  # should say AUTHENTICATED
```

## Why `drive.file` and not `drive`

- `drive.file` — Per-file access. Can create/upload/modify files the app creates or is explicitly granted access to. This is the recommended scope for apps that don't need full Drive visibility.
- `drive` — Full Drive access. Can see, modify, and delete ALL files. Over-permissioned for most use cases.
- `drive.readonly` — Read only. Uploads fail with 403.

## Token Refresh Failure After Scope Change

When scopes change, the stored refresh token cannot be used because it was granted for different scopes. The refresh fails with:

```
invalid_grant: Token has been expired or revoked.
```

**Fix:** `$GSETUP --revoke` then re-authenticate from scratch. The old token must be fully revoked before a new one with different scopes can be created.
