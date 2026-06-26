---
name: website-investigation
category: research
description: Investigate websites thoroughly using Hermes' built-in browser API tools (browser_navigate, browser_click, browser_snapshot, browser_vision, browser_console). Covers navigation flows, content extraction, SPA click workarounds, sign-up flow navigation, and synthesizing findings into actionable briefs.
triggers:
  - "investigate website"
  - "explore site"
  - "research company"
  - "look at website"
  - "what does X do"
  - "check out site"
  - "navigate site"
  - "sign up flow"
  - "find course"
  - "proceed with enrollment"
  - "complete course"
  - "get certificate"
  - "finish the course"
  - "course completion"
---

# Website Investigation

Investigate websites using Hermes' built-in browser API tools. This skill covers the full workflow: load → explore → extract → handle SPAs → synthesize findings.

## Tools Reference

| Tool | When to use |
|------|-------------|
| `browser_navigate(url)` | Load a page. **Already returns a compact snapshot** with ref IDs — no need for immediate `browser_snapshot`. |
| `browser_snapshot()` | Refresh after clicks/scrolling. `full=true` for complete content, omit for compact interactive view. |
| `browser_click(ref)` | Click elements by their `@eN` ref ID from the snapshot. |
| `browser_scroll(direction)` | Scroll down/up — many sites lazy-load content below the fold. |
| `browser_vision(question)` | Take a screenshot with visual description. Use to **show the user** what the page looks like, or when text snapshot misses visual info (layouts, images, CAPTCHAs). |
| `browser_console(expression)` | Execute JS in page context. **Key for extracting hidden URLs**, reading page state, DOM inspection, debugging JS errors. |
| `browser_type(ref, text)` | Type into form fields. |
| `browser_press(key)` | Keyboard actions (Enter, Tab, Escape). |
| `browser_back()` | Navigate back in history. |
| `browser_get_images()` | List all images + alt text on current page. |

## Investigation Workflow

### Phase 1: Initial Recon
1. `browser_navigate(url)` — loads and returns compact snapshot
2. Read the snapshot for:
   - Navigation structure (menus, categories, links)
   - Hero content (headline + subheading — what the org does)
   - CTAs and entry points (sign-up, enroll, get started)
   - Social proof (alumni logos, testimonials, stats)
3. `browser_scroll("down")` to reveal below-fold content
4. Call `browser_snapshot()` to refresh after scroll

### Phase 2: Deep Exploration
- Click nav links via their ref IDs to explore pages
- Toggle dropdown menus (`browser_click` on menu buttons) for full navigation
- Scroll through long content sections and re-snapshot
- For known URL patterns, navigate directly instead of chaining clicks

### Phase 3: SPA Handling
**Detection**: snapshot stays the same after a click, or URL bar doesn't change.

**Fix** — use `browser_console` to extract the actual href:
```javascript
// By partial href match
document.querySelector('a[href*="keyword"]')?.href

// By text content of the link
Array.from(document.querySelectorAll('a'))
  .find(a => a.textContent.includes('Target Text'))?.href

// Get all links on the page
Array.from(document.querySelectorAll('a[href]'))
  .map(a => ({text: a.textContent.trim(), href: a.href}))
  .filter(l => l.href.startsWith('http'))
```
Then `browser_navigate(url)` directly.

### Phase 4: Course Flow — Sign-up, Completion, and Certification
1. Navigate to the course/product/landing page
2. Find and click the primary CTA via ref ID
3. **Open-access courses** (no sign-up): clicking the CTA drops straight into lesson content. Verify by checking snapshot for course outline (units, lessons, navigation sidebar).
4. **Gated courses** (sign-up required): fill fields with `browser_type` and submit, then proceed to course content.
5. **Navigating lesson content**: use the snapshot's lesson navigation (sidebar, "Next →" buttons, disclosure triangles) to understand the structure. Report the number of units, estimated duration, and format (videos, text, interactive demos).
6. **Course completion**: after the user finishes the course, look for a certificate link or verification URL they share. Navigate to the certificate page to confirm it's valid and publicly verifiable.
7. **Certificate sharing**: certificate verification pages are typically public URLs that can be shared as links. Use `browser_vision` to confirm the certificate looks right, then share the URL with the user.
8. Use `browser_vision` on the final state so the user can see what's loaded.
9. Report back: what the user gets, how long it takes, what's needed, and the certificate URL if applicable.

### Phase 5: Synthesis
Deliver a structured brief:
- **What the organization does** (one-line)
- **Their offerings** (courses, products, services with key details)
- **Key stats** (alumni count, funding, hiring stats, notable partners)
- **Relevance** — specific to the user's situation, not generic
- **Recommendation** — specific next step (take the course, skip, apply, etc.)

## Best Practices

1. **`browser_navigate` already returns a snapshot** — don't call `browser_snapshot` immediately after unless the page renders dynamically.
2. **`browser_click` may "succeed" without navigating** — always verify the snapshot changed. This is common on landing pages with scroll-to-section links.
3. **`browser_vision` is for the user** — use it to share what you're seeing (especially the final result), not for every intermediate step.
4. **Scroll before snapshot** — many sites lazy-load content; the snapshot only shows what's rendered.
5. **Prefer direct URL navigation** over click chains for SPAs. Extract URLs early via `browser_console`.
6. **Extract numbers and stats** from page content into a readable format.
7. **Check the `stealth_warning` field** in navigation results — bot detection may be active.

## Pitfalls

1. **JS-heavy SPA clicks silently fail**: The click tool sends a mouse event but the SPA router may not process it. Always verify. Fallback: extract hrefs via `browser_console` and navigate directly.
2. **Cookie consent popups obscure content**: Snapshot may show the popup instead of the page beneath. Click "Reject all" or "Accept all" via ref ID to dismiss.
3. **Empty snapshot on reload**: Some pages require JS execution to render. Try re-navigating or adding a brief wait.
4. **Bot detection / CAPTCHAs**: The headless browser may trigger these. Note the `stealth_warning` to the user. In this environment, residential proxy support may not be available.
5. **Clicking a nav dropdown button**: The expanded menu region may already be in the snapshot even if `expanded=false`. The links inside it are still accessible via their ref IDs without clicking the dropdown first.

6. **`browser_click` returning success but no navigation — idempotent_no_progress_warning**: When the system emits `idempotent_no_progress_warning` (you see the same snapshot N times after clicks), **stop clicking that element immediately**. The click fires but navigation is not happening (scroll-to-section anchors, SPA intercepts, or dead links). Switch to `browser_console` to extract the actual href, then `browser_navigate(url)` directly. This warning appears at count=2, then count=3 — by the third warning you've wasted three turns on a dead end.
