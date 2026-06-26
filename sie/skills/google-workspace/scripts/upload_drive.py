#!/usr/bin/env python3
"""Upload files to Google Drive and return shareable links.

Usage:
  python3 upload_drive.py <file_path> [file_name]

Uses the existing google_api.py auth mechanism (get_credentials()).
Sets the uploaded file to "anyone with link can view".
Returns the shareable link.
"""

import json
import sys
import os
from pathlib import Path

# Add the google_api.py directory to path
sys.path.insert(0, str(Path.home() / ".hermes/skills/productivity/google-workspace/scripts"))
from google_api import get_credentials

def upload_file(file_path, file_name=None):
    """Upload a file to Google Drive and return a shareable link."""
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    creds = get_credentials()
    service = build('drive', 'v3', credentials=creds)

    file_path = Path(file_path)
    if not file_path.exists():
        print(f"ERROR: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    file_name = file_name or file_path.name

    # Determine MIME type
    suffix = file_path.suffix.lower()
    mime_types = {
        '.html': 'text/html',
        '.pdf': 'application/pdf',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.md': 'text/markdown',
        '.txt': 'text/plain',
    }
    mime_type = mime_types.get(suffix, 'application/octet-stream')

    file_metadata = {
        'name': file_name,
        'mimeType': mime_type,
    }

    media = MediaFileUpload(str(file_path), mimetype=mime_type, resumable=True)
    file = service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()

    file_id = file.get('id')

    # Make it shareable (anyone with link can view)
    permission = {
        'type': 'anyone',
        'role': 'reader',
    }
    service.permissions().create(fileId=file_id, body=permission).execute()

    # Get the shareable link
    link = f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"

    print(f"uploaded: {file_name}")
    print(f"link:     {link}")
    return link

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 upload_drive.py <file_path> [file_name]")
        sys.exit(1)

    file_path = sys.argv[1]
    file_name = sys.argv[2] if len(sys.argv) > 2 else None
    upload_file(file_path, file_name)
