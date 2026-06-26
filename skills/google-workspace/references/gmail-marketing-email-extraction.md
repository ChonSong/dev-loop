# Gmail: Extracting Bodies from Marketing / Tracking-Heavy Emails

## The Problem

`$GAPI gmail get <ID>` returns an empty `body` field for some emails — typically marketing or recruitment emails with complex MIME structures (tracking pixels, embedded images, multi-part alternatives, and CRM/Dynamics tracking links). The `_extract_message_body()` function in `google_api.py` walks `payload.parts` looking for `text/plain` or `text/html`, but may miss deeply nested or non-standard MIME arrangements.

## The Fix: Raw MIME Decode

Fall back to `format='raw'` on the Gmail API and parse the MIME tree with Python's standard `email` library:

```python
import base64
from email import message_from_bytes
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

creds = Credentials.from_authorized_user_file(
    '/home/sc/.hermes/google_token.json'
)
if creds.expired:
    creds.refresh(Request())

service = build('gmail', 'v1', credentials=creds)

msg = service.users().messages().get(
    userId='me', id='MESSAGE_ID', format='raw'
).execute()

raw = base64.urlsafe_b64decode(msg['raw'].encode('ASCII'))
mime = message_from_bytes(raw)

# Extract plain text
if mime.is_multipart():
    for part in mime.walk():
        if part.get_content_type() == 'text/plain':
            body = part.get_payload(decode=True).decode('utf-8', 'replace')
            break
    else:
        # HTML only — no plain text alternative found
        pass
else:
    body = mime.get_payload(decode=True).decode('utf-8', 'replace')
```

## Why `gmail get` Returns Empty Bodies

The `google_api.py` script requests `format='full'` and calls `_extract_message_body()`, which:

1. Checks `payload.body.data` — often empty for complex MIME (the body is in `parts`, not in `payload.body`)
2. Walks `payload.parts` searching for `text/plain` or `text/html` — works for most emails but can miss nested MIME (e.g. `multipart/alternative` containing `multipart/related` containing `text/plain`)

Marketing emails from CRM systems (Dynamics, HubSpot, Mailchimp) frequently use 3+ level MIME nesting with tracking pixels, `cid:` image references, and `multipart/report` sections that throw off shallow walkers.

## Quick Usage

```bash
GAPI="python ${HERMES_HOME:-$HOME/.hermes}/skills/productivity/google-workspace/scripts/google_api.py"
# Identify the message first
$GAPI gmail search "from:lumifygroup.com" --max 5
# Then decode raw with the Python snippet above
```
