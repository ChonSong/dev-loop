# LinkedIn Audit — Degraded Mode Procedures

Detailed guide for when the LinkedIn Weekly Audit cron runs and infrastructure is partially or fully unavailable.

## Scenario Matrix

| Scenario | What to do |
|----------|------------|
| All sources reachable | Full audit: profile score + content metrics + session health |
| Host unreachable, local data available | Partial audit: use local drafts, mark host sources unreachable |
| Chrome/CDP down | Mark session health DOWN, profile sections as unknown |
| n8n down | Mark n8n as unreachable, note last-known cron config |
| Everything down | Minimal audit: infrastructure report + action items to restore |

## SSH Access Notes

- Host: `172.19.0.1`, user: `sean`
- SSH key may be at `~/.ssh/id_ed25519` (hermes user) or `/home/hermes/.ssh/id_ed25519` (root)
- If SSH fails with "Permission denied", the key is not authorized on the host — do NOT retry endlessly, mark as unreachable and move on
- The host is a Docker container on the same network; if SSH is down, try `localhost` as fallback (different container)

## Chrome/CDP Recovery

If Chrome CDP is not responding on port 9222:
1. This is expected if the host machine was rebooted or Chrome crashed
2. Chrome must be restarted with `--remote-debugging-port=9222 --remote-allow-origins=*`
3. Script: `bash /tmp/start-chrome-debug.sh` (on host)
4. The LinkedIn tab persists across Chrome restarts — session cookies survive

## n8n Recovery

If n8n is not responding on port 5678:
1. n8n is a separate service on the host
2. Check: `systemctl status n8n` or `docker ps | grep n8n` (on host)
3. n8n is a fallback for content generation — posting works via CDP directly

## Local Data Locations

When host is unreachable, check these local paths:
- `/opt/data/linkedin-drafts/*.md` — draft posts (may be stale)
- `~/linkedin-audit/` or `/opt/data/linkedin-audit/` — previous audit reports
- `/opt/data/skills/linkedin-automation/` — skill config with cron job IDs

## Report Reliability Scoring

At the end of every audit, include a reliability note:

| Sources Available | Reliability |
|-------------------|-------------|
| 6-7 / 7 | HIGH — full confidence |
| 4-5 / 7 | MEDIUM — some gaps |
| 2-3 / 7 | LOW — significant blind spots |
| 0-1 / 7 | MINIMAL — infrastructure is down, audit is a recovery signal |

## Cron Job Reference

| Job | Schedule | Job ID | Purpose |
|-----|----------|--------|---------|
| LinkedIn Daily Post | `0 10 * * 1-5` | `72b7b98b3933` | Publish queued post |
| LinkedIn Auto Post | `30 10 * * 1-5` | `82fd61e8656d` | Auto-generate + post |
| LinkedIn Engagement | `0 14 * * 1-5` | `6d025087595f` | Comment/engage |
| LinkedIn Weekly Audit | `0 10 * * 1` | `ab7b2ccb50a5` | This job |

If the audit finds zero posts were made all week, check whether the posting crons are still registered: `hermes cron list`
