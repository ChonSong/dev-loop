# SPA Click Workaround

When `browser_click` on a link doesn't cause navigation (common with React/Next.js/Vue SPAs that use client-side routing), use `browser_console` to extract the actual URL and navigate directly.

## Detection

Signs a click didn't navigate:
- `browser_snapshot()` returns the same content
- Page title / URL doesn't change
- The click was on a `<a>` element with an `href` but no actual navigation occurred

## Recovery via browser_console

### Extract a specific link by text content
```javascript
Array.from(document.querySelectorAll('a'))
  .find(a => a.textContent.includes('Future of AI'))?.href
```

### Extract a specific link by URL pattern
```javascript
document.querySelector('a[href*="future-of-ai"]')?.href
```

### Dump all links on the page
```javascript
Array.from(document.querySelectorAll('a[href]'))
  .map(a => ({text: a.textContent.trim(), href: a.href}))
  .filter(l => l.href.startsWith('http'))
```

### Get the current page URL
```javascript
window.location.href
```

### Check if the page is a single-page app
```javascript
// React
!!document.querySelector('[data-reactroot]')

// Next.js
!!document.querySelector('script[src*="_next"]')

// Vue
!!(document.__vue_app__ || document.querySelector('[data-v-app]'))

// History API router (most SPAs)
!!(window.__NEXT_DATA__ || window.__NUXT__ || window.history.pushState.toString() !== '[object History]')
```

## After extracting: navigate directly

```javascript
// Get the href
const url = document.querySelector('a[href*="course"]')?.href;
```

Then `browser_navigate(url)` with the extracted URL.

## Why this works

Most SPAs intercept clicks via `event.preventDefault()` on `<a>` elements and handle routing in JavaScript. The Hermes `browser_click` tool dispatches a mouse click event which the SPA may or may not handle — but the `href` attribute on the DOM element still holds the real URL. `browser_console` evaluates JavaScript directly in the page context, bypassing the SPA routing layer entirely.

## Example from session

On bluedot.org, the "Future of AI" course card appeared as a styled `<a>` element in the snapshot. `browser_click` on ref `@e18` returned success but the page didn't navigate (same homepage displayed). `browser_console` with `document.querySelector('a[href*="future-of-ai"]')?.href` revealed the actual URL `https://bluedot.org/courses/future-of-ai`, which loaded correctly via direct `browser_navigate`.
