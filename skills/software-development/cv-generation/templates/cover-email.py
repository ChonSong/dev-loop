#!/usr/bin/env python3
"""
Cover email + CV attachment sender.
Usage: python3 cover-email.py <recipient> <subject> <cv-pdf-path>

Sends via Gmail API using credentials at ~/.hermes/google_token.json.
Attaches the PDF and sends the cover email body.
"""
import sys, json, base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

RECIPIENT = sys.argv[1] if len(sys.argv) > 1 else 'info@harveyrobinson.com.au'
SUBJECT = sys.argv[2] if len(sys.argv) > 2 else 'Application — Sean Cheong'
CV_PATH = sys.argv[3] if len(sys.argv) > 3 else '/tmp/cv.pdf'

# Build cover body — CUSTOMISE PER ROLE
BODY = f"""Hi,

I'm a soon-to-graduate Data Science student from Western Sydney University who has been running production infrastructure throughout my degree.

I run a self-hosted multi-container platform: 9 Docker containers behind Cloudflare Tunnel (17 ingress rules), systemd-managed services with security hardening, GitHub Actions CI/CD matrix builds, and eval-driven pipelines with promptfoo for adversarial testing.

I've shipped event-driven automation in Go (WebSocket message bus subscriber → signed HTTP webhook fan-out with retry and dead-letter queue), migrated 2.45 GB SQL Server databases into Dockerized Linux containers, and built a tick-based autonomous development pipeline with automated code review loops.

My home lab is a production-grade infrastructure that I built, broke, fixed, and iterated on. Your role asks for someone who builds things, pulls them apart, and puts them back together — that's exactly how I work.

CV attached.

GitHub: github.com/ChonSong

Thanks,
Sean
"""

creds = Credentials.from_authorized_user_file('/home/sc/.hermes/google_token.json')
if creds.expired:
    creds.refresh(Request())
    json.dump(json.loads(creds.to_json()), open('/home/sc/.hermes/google_token.json','w'), indent=2)

msg = MIMEMultipart('mixed')
msg['To'] = RECIPIENT
msg['Subject'] = SUBJECT
msg['From'] = 'Sean Cheong <seanos1a@gmail.com>'

body = MIMEMultipart('alternative')
body.attach(MIMEText(BODY, 'plain'))
msg.attach(body)

with open(CV_PATH, 'rb') as f:
    att = MIMEBase('application', 'pdf')
    att.set_payload(f.read())
    encoders.encode_base64(att)
    att.add_header('Content-Disposition', 'attachment', filename='CV.pdf')
    msg.attach(att)

raw = base64.urlsafe_b64encode(msg.as_bytes()).decode('ascii')
service = build('gmail', 'v1', credentials=creds)
result = service.users().messages().send(userId='me', body={'raw': raw}).execute()
print(f'SENT: {result["id"]} {result["threadId"]}')
