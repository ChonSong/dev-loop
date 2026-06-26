# Certificate Retrieval

After completing an online course via browser, share the certificate with the user.

## Flow

1. User completes the course and shares a certificate URL from the platform
2. Navigate to the certificate URL to confirm it loads
3. Use `browser_vision` to show the cert visually (MEDIA: path in response)
4. Report: issuance date, certificate ID, any placeholder fields (e.g. "Awarded To" may be blank)

## Certificate URL Patterns

- BlueDot Impact: `https://bluedot.org/certification?id=<record_id>`
  - The record ID is a Base-encoded string (e.g. `recYgEvns8NV3by8X`)
  - Certificate pages are public and verifiable — no login required to view
  - Can be shared as a link anywhere (LinkedIn, resume, portfolio)

## What to Look For

- **Issuance date** — when the certificate was awarded
- **Certificate ID** — unique identifier for verification
- **Recipient name** — may be blank if the platform uses placeholder text; note this to the user
- **Organization logo** — confirms which entity issued it
- **Course title** — matches the course completed

## Sharing with the User

Use `browser_vision` to capture the certificate page, then include the screenshot inline:

```
MEDIA:/path/to/screenshot.png
```

Include the verifiable URL so they can link to it directly.
