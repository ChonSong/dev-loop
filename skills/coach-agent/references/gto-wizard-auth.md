# GTO Wizard API Access (for Coach Reference)

## Authentication
- Domain: `app.gtowizard.com` (SPA) / `gtowizard.com` (landing page)
- Login: Google/Facebook/Apple OAuth only — no email/password form supported
- Cookies set after auth: `GTO_LOGGED_IN=yes`, `GTO_USERID=acc_q6xorvbjq1`, `GTO_APP_UID=<uuid>`
- Cookies set on `.gtowizard.com` domain, not `app.` subdomain
- GraphQL endpoint: `https://gtowizard.com/graphql` (POST, returns 405 for unauthenticated requests)
- All routes on `app.gtowizard.com` return the SPA shell (index.html) — the real API is proxied through Cloudflare

## Auth Session Storage
The SPA stores auth tokens in **localStorage** (not just cookies). Cookie-only auth may not work because:
- `GTO_LOGGED_IN` is set to `no` by default on page load
- The SPA sets it to `yes` after a successful OAuth flow stores tokens in localStorage
- Simply setting the cookie via JS after page load doesn't work — the SPA already booted

## API Discovery (Partial)
The SPA uses an API at `getApiBaseUrl()/v1/...` where base URL is dynamically set.
Known endpoints that return anything useful (not just HTML shell) need further discovery.

## Accessing Range Data
The real GTO Wizard's preflop ranges and strategy data are behind the OAuth-authenticated SPA.
No programmatic API access was confirmed working in this session.
