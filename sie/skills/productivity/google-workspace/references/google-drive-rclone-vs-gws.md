# Google Drive Access: rclone vs gws

Two viable paths for Google Drive access in Hermes. The `google-workspace` skill defaults to the gws/OAuth2 approach. rclone is a valid alternative for users who already have it configured with a valid token.

## When rclone works

If the existing rclone config has a valid (non-revoked) refresh token, `rclone ls gdrive:university/cult1001/` works without any re-auth. The token refreshes automatically on each command.

## When rclone fails permanently — and what to do

rclone fails with `HttpError 400: Bad Request` + `invalid_grant` in two distinct scenarios:

| Cause | Symptoms | Fix |
|---|---|---|
| Access token expired only | `invalid_grant` on first call, succeeds on retry | No fix needed — token auto-refreshes |
| Refresh token revoked | Every call fails; re-auth produces token that immediately fails | Switch to `google-workspace` skill — rclone cannot recover from revoked refresh tokens |

**How to distinguish:** If even a freshly re-authenticated rclone instance fails immediately, the refresh token was revoked (not just the access token expired). This typically happens when the Google OAuth client was deleted and recreated, or when the user explicitly revoked access at myaccount.google.com/permissions.

When rclone fails this way, do not keep trying to reconnect — the only path forward is the `google-workspace` skill's OAuth setup (Steps 1–5 in the main SKILL.md). That OAuth client is properly registered and will produce a durable token.

## rclone Path — Re-auth (only if token is valid but access token expired)

If rclone fails only occasionally (not persistently), a re-auth may recover without switching paths:

```bash
printf 'y\ny\n' | ~/.hermes/rclone --config ~/.hermes/rclone_config/rclone.conf config reconnect gdrive:
```

Prints an auth URL. Open on a machine with a browser. After approval the process completes.

**In a headless container:** Use the PKCE method below, or set up SSH port forwarding:

```bash
# Container: start listener in background
python3 -c "from http.server import HTTPServer, BaseHTTPRequestHandler; ..." &
# Host: SSH reverse tunnel
ssh -R 53682:localhost:53682 sean@172.19.0.1
```

Then run `config reconnect` — browser on host reaches container's listener.

### PKCE method (for headless containers)

Generate the auth URL with PKCE from Python, send it to the user, collect the redirected URL.

**CRITICAL: Authorization codes are single-use.** Always generate a fresh URL. Tell the user to open it in a new/private browser tab — if they open the URL in a tab that already has an active Google session, the code may be consumed silently.

**ALSO CRITICAL: code_verifier must be saved to a file immediately.** The verifier and code are tightly coupled per auth cycle — you cannot re-use a verifier printed alongside an earlier URL with a code from a later redirect.

```python
import urllib.request, urllib.parse, random, string, base64

code_verifier = ''.join(random.choices(string.ascii_letters + string.digits + '-_', k=64))
code_challenge = base64.urlsafe_b64encode(code_verifier.encode()).decode().rstrip('=')

# Save verifier BEFORE sending the URL — never print and reuse
verifier_path = '/tmp/rclone_pkce.txt'
with open(verifier_path, 'w') as f:
    f.write(code_verifier)

client_id = 'YOUR_CLIENT_ID'
redirect_uri = 'http://localhost:53682'

auth_url = (
    'https://accounts.google.com/o/oauth2/auth'
    f'?client_id={client_id}'
    f'&redirect_uri={urllib.parse.quote(redirect_uri)}'
    f'&response_type=code'
    f'&scope={urllib.parse.quote("https://www.googleapis.com/auth/drive")}'
    f'&access_type=offline'
    f'&prompt=consent'
    f'&code_challenge={code_challenge}'
    f'&code_challenge_method=S256'
)
print(auth_url)
```

User opens URL → approves → browser tries `http://localhost:53682/?code=...` (fails, expected) → user copies full URL from address bar and pastes it back. Then exchange immediately:

```python
import urllib.parse

# Read verifier from file — NOT from printed output
with open('/tmp/rclone_pkce.txt') as f:
    code_verifier = f.read().strip()

# Extract code from pasted URL
parsed = urllib.parse.urlparse('USER_PASTED_FULL_URL')
code = urllib.parse.parse_qs(parsed.query)['code'][0]

# Exchange
req = urllib.request.Request(
    'https://oauth2.googleapis.com/token',
    data=f'client_id={client_id}&code={code}&redirect_uri=http://localhost:53682&grant_type=authorization_code&code_verifier={code_verifier}'.encode(),
    headers={'Content-Type': 'application/x-www-form-urlencoded'}
)
with urllib.request.urlopen(req, timeout=10) as r:
    token = json.loads(r.read())
```

Update `~/.hermes/rclone_config/rclone.conf` with the new token JSON.

## gws Path (google-workspace skill — recommended)

The `google-workspace` skill uses proper OAuth2 with automatic token refresh. It is the recommended path for new setups. See Steps 1–5 in the main SKILL.md.

## Decision Guide

| Scenario | Tool |
|---|---|
| Existing rclone config with valid token | rclone — no changes needed |
| rclone fails with `invalid_grant` after fresh re-auth | Switch to `google-workspace` skill |
| New setup, no existing rclone | `google-workspace` skill |
| Need to upload files to Drive | `google-workspace` skill (rclone/browser cannot do multipart upload) |
| Recurring scheduled Drive access | `google-workspace` skill + cronjob |