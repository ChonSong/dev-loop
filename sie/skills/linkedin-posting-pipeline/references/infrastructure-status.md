# LinkedIn Infrastructure Recovery Notes

## Last Audit: 2026-06-01

Full audit at `/opt/data/linkedin-audit/weekly-2026-06-01.md`

## What Broke

1. **Host SSH access** — Key mismatch on `sean@172.19.0.1`
2. **Chrome CDP** — Not running on port 9222
3. **n8n** — Not running on port 5678
4. **Queue scripts** — `linkedin-queue-post.py` does not exist anywhere

## Recovery Checklist

- Restart Chrome with `--remote-debugging-port=9222` on host
- Restart n8n on host (port 5678)
- Fix SSH key access to host
- Create queue post script (none exists)
- Verify LinkedIn session cookies in Chrome profile

## Drafts Awaiting Publication

| Date | Pillar | Status |
|------|--------|--------|
| 2026-06-01 | Build Log | draft |
| 2026-06-03 | Hot Take | draft |
