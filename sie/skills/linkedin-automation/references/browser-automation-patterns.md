# Playwright Browser Automation Patterns — LinkedIn

Patterns, pitfalls, and configuration for LinkedIn automation via Playwright.

## Core Pattern: Saved Session

```python
from playwright.sync_api import sync_playwright
import json

SESSION_FILE = "/home/sean/n8n-data/linkedin-session.json"

session_data = json.loads(open(SESSION_FILE).read())
browser = playwright.chromium.launch(headless=True, slow_mo=200)
context = browser.new_context(user_agent=session_data.get("user_agent", ""))
context.add_cookies(session_data["cookies"])
page = context.new_page()
```

**One-time setup**: Run `linkedin-login.py` with `headless=False` — user manually logs in, script saves cookies.

## Session Validation

On every bot start, verify the session is still valid:

```python
page.goto("https://www.linkedin.com/feed/")
time.sleep(3)
if "checkpoint" in page.url or "login" in page.url:
    # Session expired — alert user, do NOT attempt actions
    return False
```

LinkedIn sessions typically last 30-90 days. No reliable way to refresh programmatically — user must re-login.

## Human-Like Behavior (Critical)

LinkedIn has aggressive bot detection. Mitigations:

```python
# Random delays between actions
def human_delay(min_s=3, max_s=10):
    time.sleep(random.uniform(min_s, max_s))

# Launch flags to reduce detection
browser = playwright.chromium.launch(
    headless=True,
    slow_mo=200,  # adds 200ms to every action
    args=[
        "--disable-blink-features=AutomationControlled",
        "--no-sandbox",
    ],
)
```

**Never do**:
- Actions faster than 3 seconds apart
- More than 5 posts in a week
- More than 15 comments in a day
- Headless mode without `--disable-blink-features=AutomationControlled`
- Using Playwright's `click()` without prior `hover()` on important buttons

## Posting via LinkedIn Editor

LinkedIn's post editor is notoriously fiddly:

```python
# 1. Click "Start a post"
page.locator('button:has-text("Start a post")').click()
time.sleep(2)

# 2. Find the contenteditable editor
editor = page.locator('[contenteditable="true"], .editor-content, [role="textbox"]')
editor.click()

# 3. Type character by character (human-like)
for char in text:
    page.keyboard.type(char, delay=random.randint(20, 80))

# 4. Submit
page.locator('button:has-text("Post")').click()
```

**Pitfall**: The editor may not be ready immediately after clicking "Start a post". Always wait 2-3s and verify the contentinteractive element is visible before typing.

**Pitfall**: LinkedIn sometimes shows a modal (e.g., "Choose audience") before the editor appears. Handle with a try/except or check for the editor with a timeout.

## Commenting on Feed Posts

```python
# Find posts in feed
posts = page.locator('.feed-shared-update-v2, [data-urn*="activity"]').all()

for post in posts[:5]:
    # Click comment button on THIS post (not a global one)
    post.locator('button:has-text("Comment"), [aria-label*="Comment"]').first.click()
    time.sleep(2)
    
    # Type in the post's comment input (scoped to this post)
    post.locator('[contenteditable="true"]').first.click()
    page.keyboard.type(comment_text, delay=random.randint(50, 100))
    page.keyboard.press("Enter")
    time.sleep(random.uniform(5, 15))  # big delay between comments
```

**Pitfall**: Each post has its own comment input. Always scope locators to the specific post element, not the page. Global locators will type into the wrong input.

## Rate-Limit State Machine

`linkedin-browser.py` tracks actions per day in `/home/sean/n8n-data/linkedin-rate-limit.json`:

```json
{
  "today": "2026-05-28",
  "counts": {
    "post": 2,
    "comment": 8,
    "connection": 1
  }
}
```

Reset date automatically when `today` changes. Bot checks `_check_rate_limit(action)` before every network action.

## Screenshot Debugging

Always take before/after screenshots for visual verification (Sean's preference):

```python
bot.screenshot("linkedin-profile-before-headline.png")
# ... make changes ...
bot.screenshot("linkedin-profile-after-headline.png")
```

Upload screenshots to Google Drive or show inline for verification before considering a task done.

## Integration with n8n

**Don't try to run Playwright inside n8n.** n8n is for:
- Receiving webhooks (content requests)
- Queueing posts (JSONL file)
- Scheduling triggers (cron workflows)

Playwright runs as a separate process on the host, reads the queue, publishes. Keep them decoupled.

```
n8n webhook → JSONL queue → Playwright bot → LinkedIn
```

The `linkedin-post-runner.py` script bridges them: picks the next queued item, runs the Playwright bot, marks as posted.
