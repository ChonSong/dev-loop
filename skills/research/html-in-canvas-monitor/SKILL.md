---
name: html-in-canvas-monitor
description: Monitor Layout Subtree API (HTML-in-Canvas) experimental browser feature for stability and browser support changes.
trigger: Weekly check (Monday 9am UTC)
---

# Layout Subtree API Monitor

## What It Monitors

- **WICG/html-in-canvas** spec repository — commits, issues, spec changes
- **Chrome** — flag requirement, API stability, version support
- **Remotion** — HtmlInCanvas component updates
- **Browser support** — Firefox/Safari any new support

## Status Levels

| Status | Meaning |
|--------|---------|
| `STABLE` | API unchanged, no new browser support |
| `UPDATED` | API changed, new browser support, or flag requirement removed |
| `ACTION NEEDED` | API removed/deprecated or major breaking change |

## When to Escalate

- API reaches W3C Candidate Recommendation → evaluate integration into HWC
- Firefox/Safari implement → broaden monitoring scope
- Chrome removes flag requirement → API approaching stability

## Job ID

`5b47d796f26f` (hermes cron, every Monday 09:00 UTC)

## Pitfalls

- **caniuse.com does NOT track this API.** Searching "html-in-canvas" returns unrelated "CSS Canvas Drawings" results. Do not use caniuse for browser support checks — rely on chromestatus, bug trackers, and direct testing instead.
- **Google search may be blocked** (residential proxy required). Use alternative search via `bing.com` or `duckduckgo.com` if Google returns a CAPTCHA page.
- **Remotion docs main content** may be truncated in browser snapshot (sidebar loads fine). Navigate directly to the URL and scroll to get the article body, or use the sidebar link to confirm the page title loaded correctly.
- **chromestatus.com** may not render feature details without JS. Use the GitHub WICG repo and Chrome release notes as primary sources.

## Related

- Spec: https://github.com/WICG/html-in-canvas
- Remotion docs: https://www.remotion.dev/docs/remotion/html-in-canvas
- Chrome flag: `chrome://flags/#canvas-draw-element`
- Chrome releases: https://developer.chrome.com/release-notes