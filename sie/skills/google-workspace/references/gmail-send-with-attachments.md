# Gmail Send With Attachments

The `gmail send` CLI command does **not** support attachments. To send
email with a PDF (or any file) attached, use the Gmail API directly via
Python with the existing OAuth token.

## Pattern

```python
import json, base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Load token (same one the setup script creates)
creds = Credentials.from_authorized_user_file(
    '/home/sc/.hermes/google_token.json'
)
if creds.expired:
    creds.refresh(Request())
    json.dump(
        json.loads(creds.to_json()),
        open('/home/sc/.hermes/google_token.json', 'w'),
        indent=2
    )

# Build multipart message
msg = MIMEMultipart('mixed')
msg['To'] = 'recipient@example.com'
msg['Subject'] = 'Subject line'
msg['From'] = 'Sender Name <sender@gmail.com>'

# Plain text body
body = MIMEMultipart('alternative')
body.attach(MIMEText('Email body text here', 'plain'))
msg.attach(body)

# Attach a PDF
with open('/path/to/file.pdf', 'rb') as f:
    att = MIMEBase('application', 'pdf')
    att.set_payload(f.read())
    encoders.encode_base64(att)
    att.add_header('Content-Disposition',
                   'attachment',
                   filename='document-name.pdf')
    msg.attach(att)

# Send
raw = base64.urlsafe_b64encode(msg.as_bytes()).decode('ascii')
service = build('gmail', 'v1', credentials=creds)
result = service.users().messages().send(
    userId='me', body={'raw': raw}
).execute()
print('Sent:', result['id'], result['threadId'])
```

## Pitfalls

- **File paths with spaces** — must be quoted in shell or resolved in Python
- **Filename in Content-Disposition** — use the plain filename, not the full path
- **Token refresh** — always check and refresh before sending, otherwise the API call fails with a 401
- **MIME structure** — must use `mixed` (not `alternative`) as the outermost container when including attachments, with `alternative` nested inside for the text body
