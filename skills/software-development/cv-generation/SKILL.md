---
name: cv-generation
description: End-to-end targeted CV generation — research a role, scan seans-reporepo for relevant projects, draft content, produce HTML, convert to PDF, upload to Google Drive. Covers the full workflow from job ad to deliverable.
version: 1.0.0
trigger:
  - User shares a job ad and asks to "build a CV for this" / "tailor my CV" / "make a resume for this role"
  - User asks to update an existing CV variant
  - User asks to generate a new CV targeting a specific role category
  - After researching a company, user wants a CV drafted for that specific role
metadata:
  related_skills:
    - software-development/seans-reporepo-query — repo discovery for CV content
    - software-development/playwright-pdf — Node.js/Playwright HTML→PDF pipeline
    - devops/html-to-pdf — host-Chrome HTML→PDF via SSH (container setup)
    - productivity/google-workspace — Drive upload
    - software-development/visual-qa — PDF QA with vision models
---

# CV Generation Workflow

## Overview

Produce a targeted 1-page CV for a specific job role. The workflow is: research company → audit seans-reporepo for relevant projects → draft content (with user input) → produce HTML → convert to PDF → QA → upload to Drive.

**Key principle:** The user wants to be "grilled" — you suggest content based on recent conversation and GitHub projects, then let them decide. Do NOT charge ahead and generate without discussion.

## Step 1 — Research the Role

When the user shares a job ad or company name:

1. **Research the employer** — who they are, what they do, size, culture, tech stack. Is this a direct employer or an agency? (Harvey Robinson turned out to be a recruitment agency, not the actual employer.)
2. **Map the job requirements** to Sean's existing projects. The job ad's keywords determine which projects go on the CV.
3. **Determine salary band** — $105-115k for early-career is excellent; $50-70k is low but a stepping stone.

## Step 2 — Scan seans-reporepo for Relevant Projects

This is the content discovery phase. The catalog is at `/home/sc/repos/seans-reporepo/owned/` with ~45 repos.

**Rank by relevance to the specific role:**
- **Tier 1 (directly relevant):** agent-os, hermes-agent, energy-aware-task-router, casaos-webhook-emitter, linux-web-serving-infrastructure, hermes-telemetry, sean-dotfiles
- **Tier 2 (breadth signals):** gto-wizard-clone, hermes-web-computer, hermes-bootstrap, homepage-dashboard-sync, clonezilla-backup, circuit-breaker-framework
- **Tier 3 (skip):** repo-transmute, minsky-circuit, forrest-plan-and-track, rasta-assistant, g3kilocode, Codeovertcp, everything-dashboard, hermes-knowledge-graph, hermes-webui, seans, ecosystem, features-list, sean-s-landing-page

**User-specific project exclusions (do not include unless explicitly asked):**
- `casaos-agent` — user has said not to include
- `hermes-sync` — user has said not to include

**Present the ranked options to the user before drafting.** Say: "Here's what I'd include for this role. Here's what I'd cut. Does this feel right?"

## Step 3 — Draft the CV Content

### Page Count Decision

- **1 page** for early-career / grad / first-role applications (standard in Australia). Fits ~28-32 lines of body text at 10pt with 1.8 line spacing.
- **2 pages** for mid-level (3+ years experience) or roles requiring extensive project descriptions.
- Default for Sean: 1 page. Ask if uncertain.

### Content Rules

- **Lead with infrastructure/automation** for systems-engineer-type roles. The self-hosted agent infrastructure (agent-os + hermes + Cloudflare + systemd) is the strongest signal.
- **Lead with backend/data engineering** for developer-type roles. GTO Wizard clone, energy-aware-task-router, OneTag.
- **Cut the Data Science / ML angle** unless the role explicitly asks for it. For infrastructure/DevOps roles, ML projects dilute the signal.
- **Lead with client work (OneTag HMAS Sydney)** for credibility — real contracts beat personal projects.
- **Skills section:** One dense line grouped by category. Use `·` as separator.
- **Summary:** 2-3 lines. Frame the "home lab" as production infrastructure. Avoid generic statements.

### Source Code Deep-Dive for Technical Depth

Generic project descriptions don't impress systems engineers. Read the actual source code of selected repos and extract specific technical details:

| Detail to Extract | Example |
|------------------|---------|
| Config structures, defaults | `retry_backoff: [1s, 5s, 30s]`, `MaxConcurrent: 10` |
| Security hardening | `NoNewPrivileges`, `ProtectSystem=strict`, `PrivateTmp` in systemd unit |
| Architecture decisions | Health cascades (`depends_on: service_healthy`), read-only + tmpfs on sidecars |
| Protocol specifics | `nhooyr.io/websocket`, HMAC-SHA256 signing, Prometheus metrics without deps |
| CI/CD matrix | Matrix across 2 Python versions, 3 Go arch targets |
| Concurrency patterns | Semaphore-based (buffered chan), hand-rolled rate limiter |
| Storage patterns | SQLite audit trail, Redis sorted-set queue, JSONL dead-letter queue |

Deep-dive via `delegate_task` to read repo source files (Dockerfile, docker-compose.yml, main.go, systemd unit files, CI configs). Then incorporate the specifics as bullet points.

### Philosophy / Parsimony Section

For roles where intellectual framing is a differentiator (systems engineering, platform, research), add a brief inline philosophy block:

```html
<div class="phil-box">
  <strong>Engineering Philosophy — Principle of Parsimony:</strong>
  Given multiple models with equivalent accuracy, the simplest is favoured.
  PAC learning theory, VC dimension — applies to system architecture as much as ML.
</div>
```

This turns the academic background into a hiring signal.

### Promptfoo / Autonomous Dev Pipeline (When Relevant)

For roles asking about automation, testing, or CI/CD, include promptfoo eval-driven development and the Coach/Player autonomous dev loop as bullet points under the self-hosted infra section:

```
• Eval-driven development pipeline: promptfoo for adversarial LLM-as-judge testing
  across OWASP LLM categories, 5 evasion strategies, cost/latency thresholds
• Tick-based autonomous dev: Player agent (deepseek-v4-flash, 2-hourly) implements
  features; Coach agent (owl-alpha, 4-hourly) reviews commits against success criteria
```

### The "Evidence of Curiosity" Angle

For roles asking about home labs, build-things mentality, or self-directed learning, frame the self-hosted infrastructure as:

> *Built and maintains a production-grade multi-container platform — Docker Compose (9 containers), Cloudflare Tunnel (17 ingress rules), systemd services, GitHub Actions CI/CD, PostgreSQL-backed web platform, automated backup pipeline.*

---

## Linked Files

- `templates/cover-email.py` — reusable script that sends a cover email with CV PDF attached via Gmail API. Use instead of `$GAPI gmail send` when attachments are needed (the CLI wrapper doesn't support attachments).
- `references/seek-tandem-browser.md` — how to use Tandem Browser's shared Electron session to research SEEK jobs (login via GSI, bypassing Cloudflare, navigating results).
- `references/seek-tandem-login.md` — detailed SEEK Google Sign-In flow via Tandem Browser (GSI iframe coordinate-based clicks, search URL formats, anti-bot coverage).

---

## Step 4 — Produce HTML

### Styling Reference (Validated for A4 1-page)

| Element | Value |
|---------|-------|
| Name | 18pt, bold, #0f172a |
| Contact | 9pt, #475569 |
| Section heading | 11pt, bold, #1e293b |
| Body text | 9.5pt, #334155, line-height 1.7 |
| Job title | 10pt, semibold, #0f172a |
| Job subtitle | 8.5pt, #2d7d6f, semibold |
| Bullet point | 9pt, #334155, line-height 1.65, text-indent -12px |
| Skills line | 9pt, line-height 1.75 |
| Footer | 8pt, #94a3b8 |
| Horizontal rule | 1px #cbd5e1 |
| Page margins | 18mm top/bottom, 16mm left/right |

### Layout Rules

- `.page`: 210mm wide, 297mm min-height, flexbox column
- `.main`: flex: 1 (pushes footer to bottom)
- `.footer`: margin-top: auto (pins to page bottom)
- No hard page breaks needed for 1-pagers

## Step 5 — Convert to PDF

### Option A: Local Playwright (Recommended for Hermes WebUI)

The container has Node.js v22 and Chromium 1223 cached at `~/.cache/ms-playwright/chromium-1223/chrome-linux64/chrome`.

```bash
cd /tmp && npm init -y && npm install playwright
```

Script at `/tmp/html2pdf.cjs`:

```javascript
const { chromium } = require('playwright');
const browser = await chromium.launch({
  executablePath: '/home/sc/.cache/ms-playwright/chromium-1223/chrome-linux64/chrome'
});
const page = await browser.newPage({ viewport: { width: 1240, height: 1754 } });
await page.goto('file:///tmp/cv.html', { waitUntil: 'networkidle', timeout: 30000 });
await page.pdf({
  path: '/tmp/output.pdf',
  format: 'A4',
  printBackground: true,
  margin: { top: '0', bottom: '0', left: '0', right: '0' }
});
await browser.close();
```

### Option B: Host Chrome (for container without Node.js)

See `devops/html-to-pdf` skill for the SSH-based host-Chrome pipeline.

## Step 6 — User Verification Before Submission

Before submitting the CV as a job application:

1. **Generate a preview** — Create a PNG screenshot of the PDF via Playwright: `await page.screenshot({ path: '/tmp/cv-preview.png', fullPage: true })`
2. **Present to the user** — Include `MEDIA:/tmp/cv-preview.png` in your response so they see the exact layout, spacing, and content.
3. **Wait for explicit approval** — Do not assume the CV is correct. The user may spot formatting issues, missing sections, or content errors.
4. **If submitting via SEEK Quick Apply** — Navigate to the review step and verify which resume filename appears in the page text. SEEK may silently swap the uploaded CV for an older one from the user's profile. Read `document.body.innerText` and search for `.pdf` to confirm the correct file is attached before clicking Submit.

This step is non-negotiable. Submit without verification is the most common application error.

## Step 7 — QA

1. **Measure blank space** via Playwright evaluate (target: <5% blank)
2. **Check page count** — 1 page for early-career
3. **Verify content** — all sections present, no text cut off
4. **No vision_analyze step required** — use programmatic measurements instead (faster, more reliable)

```javascript
const metrics = await page.evaluate(() => {
  const page = document.querySelector('.page');
  const footer = document.querySelector('.footer');
  const r = page.getBoundingClientRect();
  const fr = footer ? footer.getBoundingClientRect() : null;
  const blankPx = r.height - (fr ? fr.bottom : 0);
  const blankPercent = (blankPx / r.height * 100).toFixed(1);
  return { pageHeight: r.height, blankPercent, footerBottom: fr?.bottom };
});
```

Target: blank < 5%. If > 5%, the flexbox isn't pushing the footer properly — check `.main { flex: 1 }` and `.footer { margin-top: auto }`.

## Step 8 — Upload to Drive

Drive folder ID: `1adQ9t8qTU0Z6oHcga2rjAEP5MML0Crb3` (Sean Cheong — Job Search 2026)

```bash
GAPI="python ${HERMES_HOME:-$HOME/.hermes}/skills/productivity/google-workspace/scripts/google_api.py"
$GAPI drive upload "/tmp/CV - Role Name.pdf" --name "CV - Role Name.pdf" --parent 1adQ9t8qTU0Z6oHcga2rjAEP5MML0Crb3
$GAPI drive upload "/tmp/cv-role-name.md" --name "CV - Role Name.md" --parent 1adQ9t8qTU0Z6oHcga2rjAEP5MML0Crb3
```

Upload both PDF and markdown versions.

## Pitfalls

- **Do not generate without user input.** The user wants to be "grilled" — suggest content based on conversation history and GitHub, present options, let them decide. A CV generated without discussion will miss the mark.
- **seans-reporepo is a repo catalog, not a company catalog.** When asked to "review seans-reporepo" for CV content, scan the `owned/` directory for relevant projects — NOT for company mentions or recruiter names. The `owned/` dir has ~45 repos indexed as markdown files.
- **1 page is NOT negotiable for early-career** unless the user explicitly asks for 2. More pages signals padding for entry-level candidates.
- **Do NOT force Data Science projects** into an infrastructure-focused CV. They dilute the signal. ML/DS projects only belong when the role explicitly asks for them.
- **The self-hosted agent infrastructure is Sean's strongest differentiator** for systems-engineer roles. Most candidates have never deployed anything to production. Lead with it.
- **Cover email matters.** Draft a 3-4 paragraph email that directly maps the job requirements to Sean's specific projects. Attach both the email body and the PDF.
- **The google_api.py gmail send command does NOT support attachments.** To send a CV via email with PDF attached, use the Gmail API directly via Python with MIME multipart encoding. See the templates/cover-email.py pattern.
- **"/tmp/ files get cleaned up between sessions.** Rebuild the HTML and PDF each time. Do not assume prior builds persist.
