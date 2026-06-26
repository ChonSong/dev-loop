---
name: google-workspace
description: "Gmail, Calendar, Drive, Docs, Sheets via gws CLI or Python."
version: 1.1.1
author: Nous Research
license: MIT
platforms: [linux, macos, windows]
required_credential_files:
  - path: google_token.json
    description: Google OAuth2 token (created by setup script)
  - path: google_client_secret.json
    description: Google OAuth2 client credentials (downloaded from Google Cloud Console)
metadata:
  hermes:
    tags: [Google, Gmail, Calendar, Drive, Sheets, Docs, Contacts, Email, OAuth]
    homepage: https://github.com/NousResearch/hermes-agent
    related_skills: [himalaya]
---

# Google Workspace

Gmail, Calendar, Drive, Contacts, Sheets, and Docs — through Hermes-managed OAuth and a thin CLI wrapper. When `gws` is installed, the skill uses it as the execution backend for broader Google Workspace coverage; otherwise it falls back to the bundled Python client implementation.

## References

- `references/gmail-search-syntax.md` — Gmail search operators (is:unread, from:, newer_than:, etc.)
- `references/gmail-send-with-attachments.md` — sending email with PDF/file attachments via the Gmail API (the CLI command does not support attachments)
- `references/gmail-marketing-email-extraction.md` — extracting bodies from marketing/tracking-heavy emails that return empty body via `gmail get` (raw MIME decode workaround)
- `references/ssh-host-access.md` — SSH host discovery when Drive operations require host-side access; includes gateway IP pattern, path reference, and sshd setup instructions
- `references/google-drive-rclone-vs-gws.md` — rclone vs gws Google Drive access comparison; includes legacy rclone config, token refresh procedure, and decision guide
- `references/drive-api-patterns.md` — working patterns for folder listing, children API, and search gotchas discovered during active use

## Scripts

- `scripts/setup.py` — OAuth2 setup (run once to authorize)
- `scripts/google_api.py` — compatibility wrapper CLI. It prefers `gws` for operations when available, while preserving Hermes' existing JSON output contract.

## First-Time Setup

The setup is fully non-interactive — you drive it step by step so it works
on CLI, Telegram, Discord, or any platform.

Define a shorthand first:

```bash
GSETUP="python ${HERMES_HOME:-$HOME/.hermes}/skills/productivity/google-workspace/scripts/setup.py"
GSETUP="python ${HERMES_HOME:-$HOME/.hermes}/skills/productivity/google-workspace/scripts/setup.py"

### Step 0: Check if already set up

```bash
$GSETUP --check
```

If it prints `AUTHENTICATED`, skip to Usage — setup is already done.

### Step 1: Triage — ask the user what they need

Before starting OAuth setup, ask the user TWO questions:

**Question 1: "What Google services do you need? Just email, or also
Calendar/Drive/Sheets/Docs?"**

- **Email only** → They don't need this skill at all. Use the `himalaya` skill
  instead — it works with a Gmail App Password (Settings → Security → App
  Passwords) and takes 2 minutes to set up. No Google Cloud project needed.
  Load the himalaya skill and follow its setup instructions.

- **Email + Calendar** → Continue with this skill, but use
  `--services email,calendar` during auth so the consent screen only asks for
  the scopes they actually need.

- **Calendar/Drive/Sheets/Docs only** → Continue with this skill and use a
  narrower `--services` set like `calendar,drive,sheets,docs`.

- **Full Workspace access** → Continue with this skill and use the default
  `all` service set.

**Question 2: "Does your Google account use Advanced Protection (hardware
security keys required to sign in)? If you're not sure, you probably don't
— it's something you would have explicitly enrolled in."**

- **No / Not sure** → Normal setup. Continue below.
- **Yes** → Their Workspace admin must add the OAuth client ID to the org's
  allowed apps list before Step 4 will work. Let them know upfront.

### Step 2: Create OAuth credentials (one-time, ~5 minutes)

Tell the user:

> You need a Google Cloud OAuth client. This is a one-time setup:
>
> 1. Create or select a project:
>    https://console.cloud.google.com/projectselector2/home/dashboard
> 2. Enable the required APIs from the API Library:
>    https://console.cloud.google.com/apis/library
>    Enable: Gmail API, Google Calendar API, Google Drive API,
>    Google Sheets API, Google Docs API, People API
> 3. Create the OAuth client here:
>    https://console.cloud.google.com/apis/credentials
>    Credentials → Create Credentials → OAuth 2.0 Client ID
> 4. Application type: "Desktop app" → Create
> 5. If the app is still in Testing, add the user's Google account as a test user here:
>    https://console.cloud.google.com/auth/audience
>    Audience → Test users → Add users
> 6. Download the JSON file and tell me the file path
>
> Important Hermes CLI note: if the file path starts with `/`, do NOT send only the bare path as its own message in the CLI, because it can be mistaken for a slash command. Send it in a sentence instead, like:
> `The JSON file path is: /home/user/Downloads/client_secret_....json`

Once they provide the path:

```bash
$GSETUP --client-secret /path/to/client_secret.json
```

**Container context:** When running inside a Docker container, `~` may expand
to the container's home, not the host's. Use `write_file` to copy the client
secret to `~/.hermes/google_client_secret.json` instead of using `cp` with
`~` expansion — the terminal's `~` points to the container user's home, not
the host user's.

If they paste the raw client ID / client secret values instead of a file path,
to the container's home, not the host's. Use `write_file` to copy the client
secret to `~/.hermes/google_client_secret.json` instead of using `cp` with
`~` expansion — the terminal's `~` points to the container user's home, not
the host user's.

If they paste the raw client ID / client secret values instead of a file path,
write a valid Desktop OAuth JSON file for them yourself, save it somewhere
explicit (for example `~/Downloads/hermes-google-client-secret.json`), then run
`--client-secret` against that file.

### Step 3: Get authorization URL

**Note:** The `--services` flag described in older documentation does not exist in setup.py.
All available scopes (drive, gmail, calendar, sheets, docs, contacts) are requested in the
default auth URL. This is not configurable per-service at auth time.

```bash
$GSETUP --auth-url
```

Extract the `auth_url` from output and send it to the user. Tell them:
- The browser will fail to load `http://localhost:1` after approval — expected.
- Copy the full redirected URL from the address bar and paste it back.

### Step 4: Exchange the code

Authorization codes are **single-use**. A code can only be exchanged once. If the user has previously opened the auth URL in a different browser tab or pasted a prior code, the exchange fails with `invalid_grant`. The fix is always the same:

1. Run `$GSETUP --auth-url` to generate a fresh auth URL
2. Have the user open it in a **new** browser window or private/incognito tab
3. User approves and pastes the new redirected URL

The `--auth-code` argument accepts either the full redirected URL (`http://localhost:1/?code=...&state=...`) or just the bare code string. Both work. The state parameter is ignored internally.

### Step 5: Verify

```bash
$GSETUP --check
```

Should print `AUTHENTICATED`. Setup is complete — token refreshes automatically from now on.

### Notes

- Token is stored at `~/.hermes/google_token.json` and auto-refreshes.
- Pending OAuth session state/verifier are stored temporarily at `~/.hermes/google_oauth_pending.json` until exchange completes.
- If `gws` is installed, `google_api.py` points it at the same `~/.hermes/google_token.json` credentials file. Users do not need to run a separate `gws auth login` flow.
- To revoke: `$GSETUP --revoke`
- **Docker environments**: When running Hermes in a Docker container, use `write_file()` to place the client secret JSON on the host filesystem rather than `cp` (which may resolve `~` to the container home). If `$HERMES_HOME` is unset, the setup script falls back to `$HOME/.hermes` — verify this resolves to the correct Hermes config directory on your host.

## Usage

All commands go through the API script. Set `GAPI` as a shorthand:

```bash
GAPI="python ${HERMES_HOME:-$HOME/.hermes}/skills/productivity/google-workspace/scripts/google_api.py"
```

### Gmail

```bash
# Search (returns JSON array with id, from, subject, date, snippet)
$GAPI gmail search "is:unread" --max 10
$GAPI gmail search "from:boss@company.com newer_than:1d"
$GAPI gmail search "has:attachment filename:pdf newer_than:7d"

# Read full message (returns JSON with body text)
$GAPI gmail get MESSAGE_ID

# Send
$GAPI gmail send --to user@example.com --subject "Hello" --body "Message text"
$GAPI gmail send --to user@example.com --subject "Report" --body "<h1>Q4</h1><p>Details...</p>" --html
$GAPI gmail send --to user@example.com --subject "Hello" --from '"Research Agent" <user@example.com>' --body "Message text"

# Reply (automatically threads and sets In-Reply-To)
$GAPI gmail reply MESSAGE_ID --body "Thanks, that works for me."
$GAPI gmail reply MESSAGE_ID --from '"Support Bot" <user@example.com>' --body "Thanks"

# Labels
$GAPI gmail labels
$GAPI gmail modify MESSAGE_ID --add-labels LABEL_ID
$GAPI gmail modify MESSAGE_ID --remove-labels UNREAD
```

### Calendar

```bash
# List events (defaults to next 7 days)
$GAPI calendar list
$GAPI calendar list --start 2026-03-01T00:00:00Z --end 2026-03-07T23:59:59Z

# Create event (ISO 8601 with timezone required)
$GAPI calendar create --summary "Team Standup" --start 2026-03-01T10:00:00-06:00 --end 2026-03-01T10:30:00-06:00
$GAPI calendar create --summary "Lunch" --start 2026-03-01T12:00:00Z --end 2026-03-01T13:00:00Z --location "Cafe"
$GAPI calendar create --summary "Review" --start 2026-03-01T14:00:00Z --end 2026-03-01T15:00:00Z --attendees "alice@co.com,bob@co.com"

# Delete event
$GAPI calendar delete EVENT_ID
```

### Drive

```bash
# Search existing files
$GAPI drive search "quarterly report" --max 10
$GAPI drive search "mimeType='application/pdf'" --raw-query --max 5

# Get metadata for a single file
$GAPI drive get FILE_ID

# Upload a local file (auto-detects MIME type)
$GAPI drive upload /path/to/report.pdf
$GAPI drive upload /path/to/image.png --name "Logo.png" --parent FOLDER_ID

# Download (binary files download as-is; Google-native files export to a
# sensible default — Docs→pdf, Sheets→csv, Slides→pdf, Drawings→png)
$GAPI drive download FILE_ID
$GAPI drive download DOC_ID --output ~/doc.pdf
$GAPI drive download DOC_ID --export-mime text/plain --output ~/doc.txt

# Create a folder
$GAPI drive create-folder "Reports"
$GAPI drive create-folder "Q4" --parent FOLDER_ID

# Share
$GAPI drive share FILE_ID --email alice@example.com --role reader
$GAPI drive share FILE_ID --email alice@example.com --role writer --notify
$GAPI drive share FILE_ID --type anyone --role reader        # anyone with link
$GAPI drive share FILE_ID --type domain --domain example.com --role reader

# Delete — defaults to trash (reversible). Use --permanent to skip the trash.
$GAPI drive delete FILE_ID
$GAPI drive delete FILE_ID --permanent
```

### Contacts

```bash
$GAPI contacts list --max 20
```

### Sheets

```bash
# Create a new spreadsheet
$GAPI sheets create --title "Q4 Budget"
$GAPI sheets create --title "Inventory" --sheet-name "Stock"

# Read
$GAPI sheets get SHEET_ID "Sheet1!A1:D10"

# Write
$GAPI sheets update SHEET_ID "Sheet1!A1:B2" --values '[["Name","Score"],["Alice","95"]]'

# Append rows
$GAPI sheets append SHEET_ID "Sheet1!A:C" --values '[["new","row","data"]]'
```

### Docs

```bash
# Read
$GAPI docs get DOC_ID

# Create a new Doc (optionally seeded with body text)
$GAPI docs create --title "Meeting Notes"
$GAPI docs create --title "Draft" --body "First paragraph..."

# Append text to the end of an existing Doc
$GAPI docs append DOC_ID --text "Additional content to append"
```

## Output Format

All commands return JSON. Parse with `jq` or read directly. Key fields:

- **Gmail search**: `[{id, threadId, from, to, subject, date, snippet, labels}]`
- **Gmail get**: `{id, threadId, from, to, subject, date, labels, body}`
- **Gmail send/reply**: `{status: "sent", id, threadId}`
- **Calendar list**: `[{id, summary, start, end, location, description, htmlLink}]`
- **Calendar create**: `{status: "created", id, summary, htmlLink}`
- **Drive search**: `[{id, name, mimeType, modifiedTime, webViewLink}]`
- **Drive get**: `{id, name, mimeType, modifiedTime, size, webViewLink, parents, owners}`
- **Drive upload**: `{status: "uploaded", id, name, mimeType, webViewLink}`
- **Drive download**: `{status: "downloaded", id, name, path, mimeType}`
- **Drive create-folder**: `{status: "created", id, name, webViewLink}`
- **Drive share**: `{status: "shared", permissionId, fileId, role, type}`
- **Drive delete**: `{status: "trashed" | "deleted", fileId, permanent}`
- **Contacts list**: `[{name, emails: [...], phones: [...]}]`
- **Sheets get**: `[[cell, cell, ...], ...]`
- **Sheets create**: `{status: "created", spreadsheetId, title, spreadsheetUrl}`
- **Docs create**: `{status: "created", documentId, title, url}`
- **Docs append**: `{status: "appended", documentId, inserted_at, characters}`

## Rules

1. **Never send email, create/delete calendar events, delete Drive files, share files, or modify Docs/Sheets without confirming with the user first.** Show what will be done (recipients, file IDs, content, share role) and ask for approval. For `drive delete`, prefer the default trash (reversible) over `--permanent`.
2. **Check auth before first use** — run `setup.py --check`. If it fails, guide the user through setup.
3. **Use the Gmail search syntax reference** for complex queries — load it with `skill_view("google-workspace", file_path="references/gmail-search-syntax.md")`.
4. **Calendar times must include timezone** — always use ISO 8601 with offset (e.g., `2026-03-01T10:00:00-06:00`) or UTC (`Z`).
5. **Respect rate limits** — avoid rapid-fire sequential API calls. Batch reads when possible.

## Crossref API (Academic Citation Verification)

For research compilation tasks, Crossref's public API (`api.crossref.org`) is a reliable, token-free way to verify bibliographic metadata. Use `execute_code` with `urllib.request` — do not rely on browser tools.

**Why not browser tools?**
- `delegate_task` with `browser` toolset does web content extraction only — it cannot simulate browser-based file uploads (multipart POST) to Google Drive or similar.
- Browser delegation cannot handle Google Drive upload flows (auth redirects + multipart form POST).
- If the goal is uploading a file to Drive, OAuth setup via this skill is required; browser automation is not a workaround.

**API patterns (verified working):**

```python
import urllib.request, json

def crossref_get(url):
    req = urllib.request.Request(url, headers={
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (research; mailto:research@example.com)"
    })
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

# By DOI
data = crossref_get("https://api.crossref.org/works/10.1080/09650792.2013.856771")
msg = data["message"]
title = msg["title"][0]
authors = [f"{a['given']} {a['family']}" for a in msg["author"]]
year = msg["published-print"]["date-parts"][0][0]

# By ISBN (filter)
data = crossref_get("https://api.crossref.org/works?filter=isbn:9781315456539&rows=3")

# By title query
data = crossref_get("https://api.crossref.org/works?query-title=interviews+kvale+brinkmann&rows=5")
```

**APA7 field mapping from Crossref response:**
- Title: `msg["title"][0]`
- Authors: `msg["author"]` → `{a["given"]} {a["family"]}`
- Year: `msg.get("published-print", msg.get("published-online", {}))["date-parts"][0][0]`
- Journal: `msg["container-title"][0]`
- Volume/Issue: `msg["volume"]`, `msg["issue"]`
- Pages: `msg["page"]`
- DOI: `msg["DOI"]`
- ISBN: `msg["ISBN"]` (list)

**Pitfalls:**
- `title` and `container-title` are always lists — index `[0]`
- `published-print` may not exist; fall back to `published-online`
- Crossref DOI URLs with special characters (e.g. `10.1002/1098-2736(200102)38:2<137::aid-tea1001>3.0.co;2-u`) may need URL encoding
- Filter-based queries (`filter=isbn:...`) work; `query=` alone can be ambiguous
- `query-title=` with spaces must be URL-encoded (`+` or `%20`)

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `NOT_AUTHENTICATED` | Run setup Steps 2-5 above |
| `REFRESH_FAILED` | Token revoked or expired — redo Steps 3-5 |
| `HttpError 403: Insufficient Permission` | Missing API scope — `$GSETUP --revoke` then redo Steps 3-5 |
| `AUTHENTICATED (partial)` or "Token missing scopes" | New write capabilities (Drive write/delete, Docs create/edit) require re-authorization. `$GSETUP --revoke` then redo Steps 3-5 to grant the upgraded scopes. |
| `HttpError 403: Access Not Configured` | API not enabled — user needs to enable it in Google Cloud Console |
| `ModuleNotFoundError` | Run `$GSETUP --install-deps`. If that fails (e.g. no pip module or wrong venv), install directly: `uv pip install google-api-python-client google-auth-oauthlib google-auth-httplib2` |
| `invalid_grant: code_verifier or verifier is not needed` | PKCE conflict with Desktop OAuth client type. `setup.py` has been patched to use `autogenerate_code_verifier=False` — just run `--auth-url` again to generate a fresh non-PKCE URL and redo the code exchange. |
| Advanced Protection blocks auth | Workspace admin must allowlist the OAuth client ID |
| Need to upload a file to Drive but no OAuth configured | (a) Set up OAuth via this skill's setup flow, (b) use Gmail to send the file as an attachment to an address that can access the Drive folder, or (c) have the user drag it in manually. Browser delegation is not a workaround — it cannot handle multipart file POSTs. |
| Crossref query returns empty | Try with `filter=isbn:...` rather than `query-title=`; check for URL-encoding issues with special characters in DOIs |

## Revoking Access

```bash
$GSETUP --revoke
```