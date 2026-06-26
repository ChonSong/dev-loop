---
name: browser-agent
description: Browser Agent — web automation agent. Handles browser-based automation, web scraping, and UI interaction.
version: 1.0.0
author: migrated-from-openclaw
category: agents
metadata:
  openclaw_id: browser-agent
  openclaw_name: "Browser Agent – Web Automation"
  model:
    primary: minimax/MiniMax-M2.7
    fallbacks:
      - minimax/MiniMax-M2.5
      - litellm/minimax-m2.7-highspeed
      - litellm/minimax-m2.7
---

# Browser Agent – Web Automation

Browser Agent automates browser-based tasks including web scraping, form filling, and UI interaction.

## Browser Tool Usage (Critical — Subagent Delegation Fails)

The `browser` tool is a CDP-based automation tool. When you need browser interaction for a task:
- **Use the `browser` tool directly in the agent's own context** — do NOT delegate browser tasks to a subagent via `delegate_task`
- Subagent delegation to browser-agent has been observed to fail silently (subagent returns after 1 tool call without executing browser commands)
- If a subagent must be used for a browser task, provide explicit step-by-step browser commands in the `context` field, not assume the subagent will figure out the tool usage

### Direct Browser Workflow
When using `browser` directly in the agent's own context:

```javascript
// Navigate
{ tool: "browse", args: { action: "goto", url: "https://example.com" } }

// Find elements (returns element references for follow-up actions)
{ tool: "browse", args: { action: "find", selector: "textarea", role: "textbox" } }
{ tool: "browse", args: { action: "find", selector: "button[type=submit]" } }

// Interact
{ tool: "browse", args: { action: "fill", selector: "textarea", text: "..." } }
{ tool: "browse", args: { action: "click", selector: "button[type=submit]" } }

// Read page
{ tool: "browse", args: { action: "read" } }
```

### Key Pitfalls
- aidetector.com is Cloudflare-protected — API endpoints return 404 or Cloudflare challenge pages. Browser automation against such sites may be blocked at the network layer.
- Always verify the browser can reach the target before attempting interaction.
- For JS-heavy SPAs (Vue/Nuxt/RCT), wait for `networkidle` before attempting interactions.

## Tools
- browser, read, write, exec, web_search, subagents, sessions_spawn, sessions_list

## Use case
Automating web interactions, web scraping, form filling, and UI interaction.