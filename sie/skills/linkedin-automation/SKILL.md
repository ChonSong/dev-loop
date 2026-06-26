---
name: linkedin-automation
description: End-to-end LinkedIn automation — profile content, posting, engagement, and analytics via Hermes cron + CDP browser control. Use for any LinkedIn growth task.
version: 3.0.0
author: Hermes
---

# LinkedIn Automation

Full LinkedIn presence management: content creation, profile optimization, posting, engagement tracking, and analytics. Runs via Hermes cron + Chrome DevTools Protocol (CDP) on the host machine.

## Architecture

```
Hermes cron → drafts post → queues to JSONL → CDP publishes to LinkedIn
                                                  ↓
                                            Chrome remote debugging
                                            (port 9222, real browser)
```

## Chrome Remote Debugging Setup (One-Time)

Sean's Chrome must run with remote debugging enabled:

```bash
# On host:
bash /tmp/start-chrome-debug.sh
# Or manually:
pkill -f "google-chrome"
sleep 2
rm -f /home/sean/.config/google-chrome/SingletonLock
nohup /opt/google/chrome/chrome \
  --remote-debugging-port=9222 \
  --remote-allow-origins=* \
  --user-data-dir=/home/sean/.config/google-chrome/Default \
  > /tmp/chrome-debug.log 2>&1 &
```

Verify: `curl http://localhost:9222/json/version` → should return Chrome/143...

**Critical:** Chrome must be launched with `--remote-allow-origins=*` or CDP WebSocket connections get HTTP 403.

## Why CDP Instead of Headless Playwright

LinkedIn's anti-bot detection flags headless Chromium regardless of valid cookies. Even with a saved `li_at` cookie, headless Playwright gets an interstitial login page ("Welcome back → Password"). Solution: control Sean's real Chrome via CDP, which has the real browser fingerprint, extensions, and session.

**Do NOT use Playwright for LinkedIn.** Use CDP exclusively.

## CDP Posting Flow (Working)

The end-to-end flow when the LinkedIn feed is already loaded:

1. **Connect:** `websocket.create_connection(ws_url, timeout=60)` → `ws.settimeout(30)`
2. **Find composer:** Use XPath `//*[text()='Start a post']` → go up to parent `<DIV>` (has `cursor=pointer`)
3. **Click:** `Input.dispatchMouseEvent` mousePressed + mouseReleased at parent center
4. **Wait:** 4 seconds for editor to open
5. **Check editor:** `document.querySelectorAll('[contenteditable="true"]')` → should return ≥1 visible element
6. **Type:** Loop characters with `Input.dispatchKeyEvent` (keyDown + char + keyUp), 40ms delay
7. **Submit:** Tab key repeatedly (up to 20 times) until focused element contains "post" or "share", then Enter

## ⚠️ CRITICAL: Page.navigate Hangs on Slow Pages

**The `Page.navigate` CDP command blocks until the page fully loads.** LinkedIn's feed takes 30-60+ seconds, causing WebSocket timeouts. This is the #1 pitfall.

**NEVER use `Page.navigate` in production code** unless you:
- Set WebSocket timeout to 180+ seconds, AND
- Have a blocking recv loop with a deadline, AND
- Catch the timeout and reconnect

**Better approach:** Assume the tab is already on the LinkedIn feed (Sean's Chrome is always open). If you must navigate, use JavaScript:
```python
# BAD — blocks until page loads
ws.send(json.dumps({"id": 1, "method": "Page.navigate", "params": {"url": "https://www.linkedin.com/feed/"}}))
r = json.loads(ws.recv())  # HANGS HERE for 30-60s

# BETTER — fire-and-forget with short timeout
ws.settimeout(5)
ws.send(json.dumps({"id": 1, "method": "Page.navigate", "params": {"url": "https://www.linkedin.com/feed/"}}))
try:
    r = json.loads(ws.recv())  # Returns quickly or times out
except:
    pass  # Expected — page is loading
time.sleep(15)
# Reconnect (old WS is dead after navigation)
targets = json.loads(urllib.request.urlopen("http://localhost:9222/json/list").read())
```

**Best approach:** Don't navigate at all. The LinkedIn tab persists across Chrome restarts. Just connect and work with whatever page is loaded.

## CDP Element Finding in LinkedIn's React UI

LinkedIn uses dynamically-hashed CSS class names (`_92d5c98a`, `_4a67f2ef`). **Do NOT search by class name.**

**Reliable methods:**
- **XPath for text:** `document.evaluate("//*[text()='Start a post']", ...)` — works consistently
- **GetBoundingClientRect** for position — returns float values, use `Math.round()` in JS or `int(float(x))` in Python
- **Walk up DOM** from text node to find clickable parent (check `cursor: pointer` via `getComputedStyle`)

**Unreliable methods:**
- CSS class selectors (hashed names change per deploy)
- `element.click()` (React synthetic events may not fire — use CDP mouse events instead)
- `scrollIntoView` (doesn't work on LinkedIn's layout)

## CDP Timeout Configuration

```python
ws = websocket.create_connection(ws_url, timeout=60)  # connection timeout
ws.settimeout(30)  # read timeout for individual commands

# For slow operations, temporarily increase:
ws.settimeout(120)

# Always use deadline-based recv in loops, not infinite blocking:
deadline = time.time() + 25
while time.time() < deadline:
    try:
        r = json.loads(ws.recv())
        if r.get("id") == mid:
            return r
    except:
        pass
```

## Tab IDs and n8n Workflows (Optional Fallback)

n8n at `http://172.19.0.1:5678` has webhook-based workflows as a fallback:
- Content Generator: `POST /webhook/linkedin-generate` (returns `{topic, hook, prompt}`)
- Profile Optimizer: `POST /webhook/linkedin-profile` (returns `{headline, about, bannerText, tips}`)
- n8n owner: `hermes@hermes.local` / `HermesN8n2026!`

These generate prompts but **cannot post to LinkedIn** (no API access). Combine with CDP for full pipeline.

## Hermes Cron Jobs

| Job | Schedule | Job ID |
|-----|----------|--------|
| LinkedIn Daily Post | `0 10 * * 1-5` | `72b7b98b3933` |
| LinkedIn Auto Post | `30 10 * * 1-5` | `82fd61e8656d` |
| LinkedIn Engagement | `0 14 * * 1-5` | `6d025087595f` |
| LinkedIn Weekly Audit | `0 10 * * 1` | `ab7b2ccb50a5` |

## Rate Limits (conservative)

- 5 posts/week, 15 comments/day, 5 connection requests/day
- 3-10 second delays between all actions
- Human-like typing: 40ms per character via CDP key events

## Scripts (on host at `/tmp/`)

| Script | Purpose |
|--------|---------|
| `start-chrome-debug.sh` | Restart Chrome with `--remote-debugging-port=9222` |
| `linkedin-queue-post.py` | Queue a post to JSONL |
| `linkedin-post-runner.py` | Publish queued posts (imports linkedin-browser.py) |

## Weekly Audit & Degraded Mode

The LinkedIn Weekly Audit cron (`0 10 * * 1`) runs independently of the posting pipeline. It must produce a report **even when infrastructure is fully down**. Never fail silently.

### Audit Data Sources (in priority order)

| Source | Location | Fallback if unreachable |
|--------|----------|------------------------|
| Post queue | `sean@172.19.0.1:/home/sean/n8n-data/linkedin-post-queue.jsonl` | Local `/opt/data/linkedin-drafts/*.md` |
| Engagement log | `sean@172.19.0.1:/home/sean/n8n-data/linkedin-engagement-log.jsonl` | Mark as "unreachable" |
| Bot log | `sean@172.19.0.1:/home/sean/n8n-data/linkedin-bot.log` | Mark as "unreachable" |
| Browser session | `python3 /workspace/linkedin-browser.py` → CDP | Mark session health as DOWN |
| Profile completeness | CDP browser snapshot | Mark all sections as "unknown" |
| n8n workflows | `http://172.19.0.1:5678` | Mark as "unreachable" |

### Audit output format

Write to `/workspace/linkedin-audit/weekly-YYYY-MM-DD.md` (fallback: `~/linkedin-audit/` or `/opt/data/linkedin-audit/`).

Required sections:
1. **Executive Summary** — overall infrastructure health at a glance
2. **Profile Completeness Score** — score each section (headline, about, featured, skills, photo, banner, creator mode) as ✅/❌/❓
3. **Content Metrics** — posts this week, engagement rate, draft status
4. **Session Health** — table of all components with 🔴/🟡/🟢 status
5. **3 Action Items** — prioritized next-week tasks, labeled by severity (🔴/🟡/🟢)

### Degraded mode principles

When data sources are unreachable:
- **Report that explicitly.** Mark each unavailable section as "UNKNOWN (Data Unreachable)" — never silently skip it.
- **State the impact.** Explain what can't be measured and why.
- **Note the last-known state** from the skill config (cron schedule, posting cadence, etc.) so the audit still has context.
- **Escalate infrastructure issues as the #1 action item** if multiple components are down.
- **Assess reliability** of the report itself — if only 1/7 sources was accessible, say so.

### Pre-flight checklist for audit cron

Before the audit, verify:
1. `ssh sean@172.19.0.1` reachable (if not, mark all host data sources as unreachable)
2. `curl http://localhost:9222/json/version` → Chrome version string (if not, mark CDP/session as DOWN)
3. `curl http://localhost:5678/health` → n8n status (if not, mark n8n as DOWN)
4. `/workspace/linkedin-browser.py` exists and runs (if not, note it)

If all four fail, still produce the report — the audit itself is the signal that infrastructure needs fixing.

## References

- `references/crm-db-fix.md`
- `references/audit-guide.md` — detailed degraded-mode audit procedures
