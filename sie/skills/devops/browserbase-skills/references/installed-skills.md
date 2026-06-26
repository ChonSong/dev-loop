# Installed Browserbase Skills — Quick Reference

Location: `~/.hermes/skills/browserbase-*/`

## company-research
- **Trigger:** "find companies to sell to", "ICP research", "prospect list"
- **Output:** Scored CSV + per-company markdown files on Desktop
- **Scripts:** `scripts/extract_page.mjs`, `scripts/compile_report.mjs`, `scripts/list_urls.mjs`
- **References:** `references/example-research.md`

## browser-to-api
- **Trigger:** "what APIs does this site use", "build OpenAPI spec from browser trace"
- **Output:** `openapi.yaml`, `openapi.json`, `index.html` report, `client.mjs`
- **Composes with:** browser-trace (capture first, then generate spec)
- **Scripts:** `scripts/discover.mjs`

## autobrowse
- **Trigger:** "build a browser automation skill for X", "improve browsing skill"
- **Output:** `./autobrowse/` workspace with task definitions, strategy iterations
- **References:** `references/example-task.md`

## event-prospecting
- **Trigger:** "find leads at {event}", "research conference speakers", "prospect this conference"
- **Output:** HTML report (people grouped by company) + CSV for cold-outbound
- **Scripts:** `scripts/extract_page.mjs`, `scripts/compile_report.mjs`
- **References:** `references/example-research.md`, `references/workflow.md`

## fetch
- **Trigger:** "fetch this URL", "get page content without browser"
- **Output:** JSON with statusCode, headers, content, contentType

## cookie-sync
- **Trigger:** "browse as myself", "sync cookies", "log into site via Browserbase"
- **Prerequisites:** Chrome with `--remote-debugging-port=9222`
- **Output:** Browserbase context ID for authenticated browsing
- **Scripts:** `scripts/cookie-sync.mjs`

## search
- **Trigger:** "search the web", "find URLs for X"
- **Output:** Structured JSON with title, URL, author, date per result

## ui-test
- **Trigger:** "test UI changes", "QA this PR", "audit accessibility"
- **Workflow:** Plan (3 rounds) → execute in parallel sub-agents → merge report
- **Supports:** Diff-driven, exploratory, parallel testing

## browser-trace
- **Trigger:** "debug browser automation", "capture CDP trace", "audit network activity"
- **Output:** `.o11y/<run>/` with bisected CDP events, screenshots, DOM dumps
- **Scripts:** `scripts/start-capture.mjs`, `scripts/stop-capture.mjs`, `scripts/bisect-cdp.mjs`
