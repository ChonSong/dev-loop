---
name: job-scout-agent
description: Run a structured, high-volume job search with tracking, targeted role categories, and CV variations per role type.
category: productivity
tags: [job-search, career, applications, sydney, employment]
source: 0xNyk
is_imported: true
---

# Job Scout Agent

Run a structured, high-volume job search campaign. Covers researching the market, targeting multiple role categories in parallel, swapping CV variations per category, tracking applications, and managing the weekly cycle.

## When to Use

- User says "help me find a job" or "I need employment"
- User asks about the job market in a specific city/region
- User wants a system to manage their application pipeline
- User shares their resume/CV and wants to know which roles fit

## Workflow

### Phase 1 — Profile Assessment
1. Read the user's resume/CV carefully. Extract:
   - Skills stack (languages, frameworks, databases, tools)
   - Experience level and type (junior, mid, senior; full-time, freelance, contract)
   - Notable projects or depth areas (ML algorithms, database work, etc.)
   - Education
2. Map their skills to 3-5 role categories. Examples:
   - Python-Backend
   - Full-Stack (React + backend)
   - Data-Engineer / Database Developer
   - ML / AI Engineer
   - Graduate / General
3. Identify which aspects to lead with per category and which to de-emphasise.

### Phase 2 — Market Research
1. Search for the city's current labour market conditions (unemployment rate, hiring trends, sectors growing/contracting).
2. Identify which sectors and role types have genuine vacancy pressure vs oversupply.
3. Map AI disruption risk to the user's target roles (roles with routine data/doc work are shrinking; roles requiring judgment, relationships, cross-functional coordination are growing).
4. Compile salary benchmarks for target roles in the user's city.
5. List recruitment agencies relevant to the user's sector and city.

**LIVE LISTINGS LIMITATION:** The container environment triggers bot-blockers on all major job boards (SEEK, Indeed, LinkedIn, Adzuna) and search engines. You cannot scrape live job listings from inside the container. Options:
- Give the user exact search queries they can paste into SEEK/LinkedIn from their browser
- Point them to specific company careers pages
- Build the system so they can self-serve the scraping from their own machine
- Use a B2B data API (e.g. Explorium AgentSource) as a **supplement** — see `references/b2b-data-apis-for-job-hunting.md` for company discovery, hiring signals, tech stack filtering, and prospect outreach. These APIs work from the container since they're authenticated REST calls, not web scrapes.
- **Use the Tandem shared browser** (see `references/applying-via-portal-browser.md`) to bypass Cloudflare and interact with job portals that require auth, using the Electron CDP viewer at `localhost:3099`.

### Phase 3 — Build the System
1. **Define 3-5 role categories** the user should cycle through. Each gets:
   - A tailored CV variation (lead with relevant skills)
   - 3-5 SEEK search queries
   - LinkedIn quick links
2. **Create the tracker** — simple CSV with columns: Date, Company, Role Title, Role Category, Platform, Salary, Link, Status, Notes, Follow-Up
3. **Generate CV variations** — one per category. Copy their base resume, reorder bullets in Summary + Skills so the relevant depth comes first. Save as separate files.
4. **Write a cover letter template** — 4 lines, 30-second customisation per application.
5. **Define daily workflow** — 30 min, 5 applications:
   - 5 min: open SEEK, paste 3 queries (rotate categories)
   - 5 min: scan, pick 5 matching roles
   - 15 min: paste the right CV variation, tweak 1-2 lines, submit
   - 5 min: log in tracker
6. **Define weekly review** — Sunday, 15 min: count apps (target 25+), check category balance, follow up on old apps, update statuses.

### Phase 4 — Give Specific Next Steps
- Tell the user exactly what to do TONIGHT (open SEEK, paste these 3 queries, apply to 5, log them)
- Tell them what to do TOMORROW MORNING
- Set a Week 1 target

## Pitfalls

- **Show the CV screenshot before submitting** — the user needs to verify the correct CV is attached before you hit Submit. After uploading and reaching the review page, take a screenshot and present it via `MEDIA:` before clicking the final Submit button. SEEK may silently revert to a stored profile resume instead of the uploaded one — visual verification catches this.
- **Don't only target one role type** — user wants variety. Enforce cycling through categories.
- **Don't just dump information** — user wants a system they can oversee. Build the tracker and workflow.
- **Don't keep researching once the user says "proceed"** — shift to execution mode. Build the system.
- **Live listings are un-scrapeable from this container** — don't waste time trying. Use the Tandem shared browser (see `references/applying-via-portal-browser.md`) to navigate SEEK and company portals instead.
- **SEEK Quick Apply uses React, not Angular** — SEEK updates its model on standard DOM events, so `element.value` + `dispatchEvent` works. But the flow has its own quirks: the Continue button may need 2 clicks, roll-requirements selects have dynamic random names, and uploaded CVs can silently revert to a stored profile resume. See `references/applying-via-portal-browser.md#seek-quick-apply-automation` for the full step-by-step.
- **Portal forms with Angular validation** — setting DOM values is not enough for AngularJS forms. Use the CDP `Runtime.evaluate` to call `scope.$apply()` to set model values, or click radio/checkbox elements by `name` and `value` attributes rather than by label text (see reference file for the full technique).
- **OAuth popup buttons (Google, LinkedIn, Apple) fail in Tandem/Electron** — career portals that use OAuth single sign-on via popup windows (e.g. Amazon.jobs "Login with Google") will blank out to `about:blank` because the Electron browser context can't spawn popups properly. These buttons typically have empty `href` attributes and rely on JS event handlers. Workaround: prefer email/password registration on the portal's own account system instead of social login. See `references/applying-via-portal-browser.md#amazonjobs-portal` for the Amazon.jobs-specific registration flow.
- **Verify the page actually rendered in the Tandem viewer** before telling the user to look — after navigating, check the viewer URL and snapshot. OAuth redirects, popup failures, and session expiry can leave the page at `about:blank` or an error page without the agent noticing. If the snapshot is empty, the page didn't render. Navigate back to the origin URL and retry from the previous step before asking the user to solve a CAPTCHA or interact.
- **CV variation matters** — a generic CV shows less than half your relevant depth. Always tailor per category.
- **Volume beats perfection at entry level** — 3-5 applications/day minimum. The numbers game is real.
- **B2B data APIs are supplements, not replacements** — Explorium, Clearbit, etc. won't list job postings. They're for company discovery, tech stack intel, and finding people for outreach. Free tiers (100-500 credits) burn fast on complex stats queries — check credits first before expensive calls. See `references/b2b-data-apis-for-job-hunting.md` for endpoint patterns, credit management, and known 422/404 traps.
- **Don't over-customise** — 2 lines changed per application is enough. More is diminishing returns.

## Reference Files

See `references/job-search-system.md` for the full playbook with SEEK queries, daily workflow, weekly review, and role category definitions.
See `references/job-search-tracker.csv` for the application tracking spreadsheet template.
See `references/research-sydney-2026.md` for a full Sydney labour market research compilation.
See `references/b2b-data-apis-for-job-hunting.md` for using B2B company intelligence APIs (Explorium AgentSource, etc.) as supplementary tools for company discovery, hiring signals, and prospect outreach.
See `references/applying-via-portal-browser.md` for using the Tandem shared browser (Electron CDP) to navigate job portals that block the container IP, and for automated AngularJS form filling via CDP.
See `templates/` for CV variation templates per role category.
