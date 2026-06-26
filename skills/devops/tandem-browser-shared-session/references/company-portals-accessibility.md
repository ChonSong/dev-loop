# Company Portal Accessibility via Tandem Browser

Findings from session 2026-06-16 job application campaign.

## Method

All tests performed via Tandem Electron browser (`start-tandem.sh`) controlled through `electron-viewer.js` on `localhost:3099`. The Tandem browser uses a full Chromium engine via Electron, which bypasses Cloudflare/anti-bot on many (but not all) sites that block the container's Playwright browser.

## Portal-by-Portal Results

### Amazon.jobs ✅ (with caveat)

- **URL**: `https://www.amazon.jobs/en/jobs/{JOB_ID}`
- **AWS Apprentice role**: `amazon.jobs/10379834` (Cloud Support Associate Apprentice, Sydney)
- **Status**: Loaded fully, all content visible
- **Apply flow**: "Apply now" → redirects to `passport.amazon.jobs`
- **Auth options**: 
  - ✅ Login with Google (no Amazon account needed)
  - ✅ Login with Apple
  - ✅ Login with LinkedIn
  - ✅ Create Amazon.jobs account
- **Google OAuth flow**: Redirects to accounts.google.com → account chooser → OAuth consent → back to Amazon.jobs
- **CAPTCHA blocker**: Image CAPTCHA at the final registration step (select matching images). **Cannot be automated** — user must complete this manually in the Tandem window.
- **Verdict**: Best path is Google sign-in, then have user complete the CAPTCHA, then AI can fill the application form.

### Datadog Careers ✅

- **URL**: `https://careers.datadoghq.com/`
- **Status**: Loaded fully
- **Job search**: `careers.datadoghq.com/all-jobs/` — 384 jobs listed with filters (Teams, Locations, Job Types)
- **Early Careers**: `careers.datadoghq.com/early-careers/` — internships and entry-level information
- **APAC jobs**: Search parameter `?location=Asia%20Pacific` or filter by country
- **No Sydney roles found**: At time of checking, no entry-level Sydney positions were listed. Most engineering roles in US/Europe.
- **Verdict**: Worth monitoring but no current openings for Sean's profile.

### Canva Careers ✅

- **URL**: `https://www.lifeatcanva.com/en/jobs/`
- **Status**: Loaded fully (JS-rendered SPA, takes 5+ seconds to hydrate)
- **Job count**: 210 live results
- **Filters**: Country, Team, Sub-speciality, Location Type, Work Type
- **Australia jobs**: 2 relevant at time of check (both senior)
- **Verdict**: Heavy SPA that needs patience. Entry-level roles in Australia are rare on the platform.

### Atlassian Careers ✅

- **URL**: `https://www.atlassian.com/company/careers/all-jobs`
- **Status**: Loaded fully
- **Filter UI**: Function-based (Engineering, Sales, etc.) + Country-based
- **Australia jobs**: 6 total (1 intern, 1 support, rest senior/sales)
- **Entry-level**: 1 Product Marketing Intern (Sydney), 0 Engineering graduate roles
- **Verdict**: Minimal entry-level engineering opportunities currently.

### Datacom Careers ❌

- **URL**: `https://www.datacom.com/nz/en/careers`
- **Status**: Cloudflare blocked
- **Verdict**: Cannot access via Tandem either — alternative approach needed.

### LinkedIn ❌

- **URL**: `https://www.linkedin.com/jobs/`
- **Status**: Sign-in wall
- **Verdict**: Requires user to be logged into LinkedIn in Tandem browser.

## Summary Table

| Portal | Cloudflare | Auth Required | Entry-Level Available | Apply via AI |
|--------|-----------|--------------|----------------------|-------------|
| Amazon.jobs | ✅ Bypassed | Google OAuth works | ✅ Apprentice program | Partial (CAPTCHA blocks) |
| SEEK | ✅ Bypassed | Already logged in | ✅ Many roles | ✅ Full Quick Apply |
| Datadog | ✅ Bypassed | None | ❌ None in Sydney | N/A |
| Canva | ✅ Bypassed | None | ❌ Senior only | N/A |
| Atlassian | ✅ Bypassed | None | ⚠️ 1 intern role | N/A |
| Datacom | ❌ Blocked | — | — | — |
| LinkedIn | ✅ Bypassed | ❌ Sign-in wall | — | — |
