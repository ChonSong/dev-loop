---
name: technical-resume-builder
description: Build targeted 1-page technical resumes/CVs from repo catalog audit, source code deep-dive, and company research. Generates formatted PDF via Playwright and uploads to Google Drive.
version: 1.0.0
author: Hermes
tags: [resume, cv, job-search, career, pdf, document]
trigger:
  - User asks to build or update a CV/resume for a specific role
  - User shares a job ad and asks whether/how to apply
  - User asks to tailor an existing CV to a specific company or role
prerequisites:
  commands: [node, npx]
  files:
    - path: ~/.hermes/google_token.json
      description: Google OAuth token for Drive upload and Gmail send
    - path: ~/repos/seans-reporepo/owned/
      description: Repo catalog for project selection
---

# Technical Resume Builder

Build targeted 1-page CVs for engineering roles by combining company research, repo catalog audit, and source code deep-dive into a formatted PDF delivered to Google Drive.

## Workflow

### Phase 1: Research the Target Company

Research the company behind the job ad:
- Company size, sector, funding, culture (from website, LinkedIn, Glassdoor, SEEK reviews)
- **Who is the job poster?** A recruitment agency (like Harvey Robinson, FinXL, TRS) vs the direct employer. If it's an agency, the CV must impress the recruiter first — they scan for keywords and placeability before forwarding to their client. Agency roles may close faster as they fill on a rolling basis.
- Tech stack from their job ads and engineering blog
- What they value (check job ad keywords: "home lab", "automation", "production", "curiosity", "potential over perfection")

### Phase 2: Audit Repo Catalog for Relevant Projects

From `/home/sc/repos/seans-reporepo/owned/`, select repos that match the role's requirements:

**Tier 1 — Direct match:** Infrastructure/automation projects (agent-os, energy-aware-task-router, webhook emitter, linux-web-serving-infrastructure, sean-dotfiles, hermes-telemetry)
**Tier 2 — Breadth signal:** Full-stack with engineering rigour (gto-wizard-clone, hermes-web-computer, circuit-breaker-framework)
**Tier 3 — Skip:** Data science, ML, or frontend-only projects unless directly relevant

### Phase 3: Source Code Deep-Dive

For each selected repo, extract specific technical details by reading:
- `README.md`, `docker-compose.yml`, `Dockerfile`, `package.json`, `go.mod`, `pyproject.toml`
- Key source files (`main.go`, `api.py`, `router.py`, `config.go`)
- CI/CD config (`.github/workflows/*.yml`)
- Systemd unit files
- Test files and test counts

Capture concrete details:
- Specific libraries and versions (e.g., `nhooyr.io/websocket`, `gorilla/mux`, `fastapi>=0.110.0`)
- Architecture patterns (semaphore-based concurrency, health cascades, dead-letter queues)
- Security configurations (`NoNewPrivileges`, `ProtectSystem=strict`, HMAC signing)
- Numbers and metrics (9 containers, 17 ingress rules, 269 MB → 94 MB compression, 589 tests)
- Build tooling (Nx + Turbo + uv, matrix builds, cross-compile)

### Phase 4: Draft CV Content

Structure for Sean (1 page targeted):

```
SUMMARY — 2-3 lines framing the candidate as a systems engineer
ENGINEERING PHILOSOPHY — Parsimony principle (optional box/sidebar)
SKILLS — Two-column dense list with categories
EXPERIENCE — 3-4 entries, lead with strongest match:
  1. Self-hosted Agent Infrastructure (personal platform)
  2. Relevant Go/Python automation project
  3. Client contract work
  4. Autonomous development pipeline
EDUCATION — One line
```

**Content rules:**
- Every bullet must be evidence-based from source code (library names, numbers, patterns)
- Map project details to the job ad's requirements explicitly
- Cut data science/ML projects unless directly relevant to the role
- Include the Parsimony philosophy as a differentiator
- Skip projects the user has explicitly excluded (e.g., casaos-agent, hermes-sync)

### Phase 5: Build HTML → PDF

Generate HTML with precise formatting:

```html
@page { size: A4; margin: 0; }
.page { width: 210mm; min-height: 297mm; padding: 16mm 14mm 10mm 14mm;
        display: flex; flex-direction: column; }
.main { flex: 1; }
.footer { margin-top: auto; }
```

**Styling rules (Sean's preferences):**
- Body text: 8.5pt minimum, line-height 1.5-1.55
- Job titles: 9pt bold
- Bullets: 8pt, line-height 1.5
- Skills: 8.5pt, two-column layout
- Philosophy box: light grey background (#f8fafc), green left border (#2d7d6f)
- Blank space target: <5% (tight fill)
- Footer pinned to bottom with `margin-top: auto` on `.main`

**PDF generation with Playwright:**
```javascript
const { chromium } = require('playwright');
const b = await chromium.launch({
  executablePath: '/home/sc/.cache/ms-playwright/chromium-1223/chrome-linux64/chrome'
});
const p = await b.newPage({ viewport: { width: 1240, height: 1754 } });
await p.goto('file:///tmp/cv.html', { waitUntil: 'networkidle', timeout: 30000 });
await p.pdf({ path: '/tmp/cv.pdf', format: 'A4', printBackground: true,
              margin: { top: '0', bottom: '0', left: '0', right: '0' } });
await b.close();
```

**Verify measurements:**
```javascript
const m = await p.evaluate(() => {
  const page = document.querySelector('.page');
  const footer = document.querySelector('.footer');
  const r = page.getBoundingClientRect();
  const fr = footer.getBoundingClientRect();
  return {
    pageHeight: r.height, footerBottom: fr.bottom,
    blankPercent: ((r.height - fr.bottom) / r.height * 100).toFixed(1),
    overflow: r.height > 1123 ? 'YES' : 'NO'
  };
});
// Target: <5% blank, NO overflow
```

### Phase 6: Upload & Send

**Upload to Google Drive:**
```bash
GAPI="python ${HERMES_HOME}/skills/productivity/google-workspace/scripts/google_api.py"
$GAPI drive upload "/tmp/cv.pdf" --name "CV - Role Name.pdf" --parent FOLDER_ID
```

**Send via Gmail with attachment** — use the Gmail API via Python with MIME multipart:
- Build `MIMEMultipart('mixed')` with `MIMEBase('application', 'pdf')` attachment
- Use `googleapiclient.discovery.build('gmail', 'v1', credentials=creds)`
- Call `service.users().messages().send(userId='me', body={'raw': raw_base64}).execute()`
- **Confirm with the user before sending** — show them the recipient, subject, and email body. Do NOT send without approval, even if you already drafted it earlier in the conversation.

## References

- `references/harvey-robinson-research.md` — Harvey Robinson company research and application
- `references/harvey-robinson-systems-engineer.md` — Systems Engineer CV for Harvey Robinson
- `references/ngs-super-sre-role.md` — NGS Super SRE role research and profile mapping
- `references/sean-cv-preferences.md` — Document formatting preferences and excluded projects
- `references/source-code-interview-points.md` — Concrete technical details from Sean's repos (libraries, architectures, metrics)
- `templates/cv-template.html` — Base HTML template with correct styling
- `scripts/generate-pdf.cjs` — Playwright PDF generation script

## Pitfalls

- **Don't include data science/ML projects** for infrastructure roles — cuts the wrong direction
- **Don't trust vision model blank-space estimates** — always measure with `page.evaluate()` pixel measurements
- **Don't stop at the README** — the richest CV content is in source code: configs, CI files, systemd units, test files
- **Don't use markdown → PDF converters** (they lose control over spacing) — use HTML + Playwright
- **Don't forget to check the user's excluded projects** — preferences stored in memory
- **The /tmp directory is ephemeral** — save scripts and outputs to a non-tmp path if they need to survive
- **npm install playwright can be slow** — batch commands to avoid timeout; check cached Chromium path first
- **Gmail send via CLI script** — the attachment file path must be passed correctly; use a Python script rather than trying to handle MIME in bash
- **SEEK uses Cloudflare + Google GSI (iframes) for login** — The "Sign in with Google" button is rendered inside an iframe from `accounts.google.com/gsi/button`. Standard `Runtime.evaluate` JavaScript clicks won't work because the button is in a cross-origin iframe. Use CDP `Input.dispatchMouseEvent` with page coordinates (click at the iframe's bounding rect center) instead. To find coordinates, query the iframe element position from the parent page. The electron-viewer.js at `~/.hermes/scripts/electron-viewer.js` needs both `require('ws')` installed and a `/click` endpoint added for coordinate-based interaction.
- **Recruitment agencies post on SEEK on behalf of clients** — The job ad may not name the actual employer. Harvey Robinson, FinXL, and TRS are all agencies. Apply via the agency's portal/email; they forward to the client. Agency roles often close quickly and fill on a rolling basis.

## Verification

- PDF is exactly 1 page (A4) with <5% blank space
- Footer pinned to bottom edge
- No overflow to page 2
- Source code claims are accurate (verify the file or metric exists in the repo)
