---
name: job-application-assistance
description: End-to-end job application assistance — extract job postings from JS-rendered career pages, analyze track/pathway fit, generate cover letters, tailor resumes, and plan application strategy. Covers graduate programs, professional roles, and technical positions.
tags: [career, job-search, cover-letter, resume, application-strategy, ats]
source: hermes-webui
---

# job-application-assistance

End-to-end job application assistance — extract job postings, analyze fit, draft cover letters, tailor resumes, and plan strategy.

## Triggers

- User asks to "apply for [job URL]", "help me apply", "review my application", "write a cover letter for [job]", "tailor my resume for [job]", "which tracks/roles should I target"
- User shares a job posting URL (any major ATS: Greenhouse, Lever, Workday, Taleo, SmartRecruiters, dxc.com,Seek, LinkedIn, etc.)

## Workflow

### Step 1 — Extract the Job Posting

**Always extract structured data first.** Do NOT try to scrape JS-rendered pages with curl alone — you will get New Relic/Waterfall agent JavaScript stubs instead of content.

Techniques (try in order):

1. **JSON-LD structured data** (preferred for modern career pages):
   ```bash
   curl -sL "JOB_URL" | grep -oP '<script type="application/ld\+json">.*?</script>' | python3 -c "
   import sys, json, re
   data = json.loads(re.search(r'\{.*\}', sys.stdin.read(), re.DOTALL).group())
   print(json.dumps(data, indent=2))
   " 2>/dev/null | python3 -m json.tool
   ```

2. **WDAPI endpoint** (for Workday-run sites like dxc.com):
   ```
   curl -sL "SITE_URL/wdapi/job/JOB_ID"
   # or
   curl -sL "SITE_URL/wdapi/apply/jobs/JOB_ID/professional"
   ```
   Extract the numeric ID from the URL path.

3. **Page title fallback** (if structured data is unavailable):
   ```bash
   curl -sL "JOB_URL" | grep -oP '(?<=<title>).*?(?=</title>)'
   ```

### Step 2 — Parse Key Fields

Extract and confirm:
- **Job title**, company, location
- **Department/team**
- **Work model** (in-person, hybrid, remote)
- **Job description / responsibilities**
- **Requirements / qualifications** (technical skills, soft skills, education, certifications)
- **Track/pathway/specialisation** options (graduate programs often have multiple)
- **Eligibility** (citizenship, degree window, clearance)
- **Diversity statement** and contact for accommodations
- **Application deadline** (if stated)
- **Internal job ID** (for reference)

### Step 3 — Application Strategy

Generate a ranked track/pathway recommendation table. For each track include:
- Rationale (why it matches a technical degree holder)
- ATS keyword alignment score
- Competitive positioning note

**Strategy rules:**
- Recommend **2–3 tracks max** to avoid looking unfocused in ATS
- For graduate programs: highlight tracks aligned to degree major
- For experienced roles: match years of experience to seniority
- Note diversity statements if present (neurodiverse, Indigenous, etc.) — these are genuine application advantages
- Flag location requirements; note willingness to commute/relocate

### Step 4 — Cover Letter

Generate a **300–400 word** professional cover letter:
- Address to "Dear [Company] Recruitment Team," (DXC uses this format)
- Express genuine interest in the company's work — digital transformation, managed services, consulting, specific industry
- Name **2 specific tracks** being applied for (don't just list; explain why each matches)
- Include a concrete example (project, internship, thesis) with technical specificity — what you did, what tools, what outcome
- Echo the company's language (digital transformation, cloud modernization, client outcomes, etc.)
- Close with invitation to discuss
- Use placeholders `[TRACK]`, `[SPECIFIC CLIENT/INDUSTRY]`, `[PROJECT EXAMPLE]` for personalization
- **Do not** use generic corporate boilerplate ("I am a highly motivated individual...").
- **Identify the user's engineering/philosophy principles** from their projects and USER.md. Common ones:
  - "Simplest model that accurately explains the phenomenon" — frame projects as deliberately simple
  - "Investigate first, then build" — show systematic debugging
  - "Ship and iterate" — show tagged releases and deployed projects
  - Weave these principles into the cover letter and resume naturally, not as buzzwords

### Step 5 — Resume Generation

Generate a complete, formatted resume — not just tailoring notes. Default output: **docx** (not HTML→PDF). **When the user explicitly asks for HTML** (e.g., "use the html resumes as a template"), generate an HTML resume using the user's existing HTML templates as the design foundation.

**Why docx over HTML (default):**
- ATS systems parse docx natively; HTML→PDF can introduce parsing artifacts
- Hiring managers expect docx or PDF; docx lets them annotate and copy-paste
- python-docx gives pixel-perfect control; no browser rendering variability

**When to use HTML:**
- User explicitly requests HTML output
- User has existing HTML resume templates to use as a base
- The role is at a company where visual presentation matters (startups, design-forward teams)
- User wants to print-to-PDF from browser for precise control

**HTML Resume Workflow:**
1. Find existing HTML templates in `/workspace/resumes/*.html`
2. Read the template to extract the design system (colors, fonts, layout, Tailwind classes)
3. Reuse the same: accent bar color, sidebar width, heading styles, tag/badge patterns, date pills
4. Replace content with the new role's information
5. Save to `/workspace/resumes/[COMPANY]_[ROLE]_Resume.html`
6. Also generate a matching cover letter in HTML using the same design language
7. User can print to PDF from browser (Ctrl+P → Save as PDF, margins: none, background graphics: on)
8. See `templates/html-resume-design-system.md` for the full design system reference
9. **For server-side PDF generation** (automatic, no browser needed): use Chrome headless on the host:
   ```bash
   google-chrome-stable --headless --disable-gpu \
     --print-to-pdf=/path/to/output.pdf \
     --print-to-pdf-no-header \
     file:///path/to/input.html
   ```
   The `--print-to-pdf-no-header` flag suppresses the URL/date footer Chrome adds by default.
   The `vaInitialize failed` error is harmless in headless mode — ignore it.

10. **Multi-page strategy** — Two-column layouts (sidebar + main) break poorly across pages with CSS `page-break-before`. The sidebar is shorter than the main column, leaving whitespace on the new page. Instead, use **separate `.page` divs**:
    - **Page 1**: Full original layout — header + sidebar + main (first half of content)
    - **Page 2**: Slim header (name + title only) + **full-width** content (no sidebar)
    - This avoids wasted horizontal space on page 2 where the sidebar would be empty
    - See `templates/html-resume-multipage-example.md` for the exact HTML pattern

11. **Mandatory verification step** — Before sending or uploading any PDF, inspect the output:
    ```python
    import fitz
    doc = fitz.open('/path/to/output.pdf')
    print(f'Pages: {len(doc)}')
    for i in range(len(doc)):
        text = doc[i].get_text()
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        print(f'Page {i+1}: {len(lines)} lines — first: {lines[0]}, last: {lines[-1]}')
    ```
    Check:
    - Correct page count
    - Content balance across pages (page 1 should not have large whitespace gaps, page 2 should not be cramped)
    - Sidebar doesn't leave empty space on continuation pages
    - No orphaned section headings
    - If the layout is unbalanced, adjust the content split point and regenerate. **Never present or send a PDF you have not verified.**

**HTML Design System (from established templates):**
- Accent bar: `linear-gradient(135deg, #1e3a5f 0%, #2d5a8a 100%)` — navy gradient
- Sidebar: `w-[30%]` with `bg-slate-50`, border-right `border-slate-200`
- Main: `w-[70%]` with padding
- Section headings: UPPERCASE, `font-weight: 700`, `letter-spacing: 0.08em`, navy `#1e3a5f`, with 2px bottom border
- Tags/badges: `background: #e8f0fe`, `color: #1e3a5f`, small padding, `border-radius: 4px`
- Date pills: `background: #1e3a5f`, white text, `border-radius: 999px`
- Accent color: `#2d7d6f` (teal) for issuer/company names
- Font: Inter (body), JetBrains Mono (tech labels)
- Page: A4 (210mm × 297mm), flex column layout
- Two-column: sidebar (tech stack, education, soft skills) + main (summary, projects, employment)

**Resume content selection approach (user-specific preference):**
When selecting which projects and experience to include in a resume, do not silently decide. Use an interactive "grill me" approach:
1. Research the company and target role first
2. Present a ranked table of candidate projects from the user's repo catalog, with a column explaining WHY each project matches the target role
3. Let the user decide what stays and what goes — this respects their domain knowledge about which work is most relevant
4. If the user says "look more into source code," actually read the source files (not just READMEs) — extract specific libraries, algorithms, architecture patterns, and metrics (test counts, build times, data sizes)
5. Include "engineer's philosophy" elements when relevant (e.g., Principle of Parsimony, eval-driven development) as a differentiating sidebar or heading
6. After content selection, ask the user "1 page or 2 pages?" based on content volume
0. **Investigate the user's actual projects deeply before writing.** This is the most important step. Do NOT write generic project descriptions.
   - **Use the repo catalog if one exists** — Check for `seans-reporepo` or similar catalog repos at `/home/sc/repos/seans-reporepo/owned/`. These contain structured markdown files per project with descriptions, tags, languages, and status. Read these first to build a complete inventory before diving into source code.
   - Present a ranked selection of projects to the user for inclusion, explaining WHY each matches the target role. Let them decide what stays and what goes. Do not silently decide yourself.
   - Search the workspace for project directories: `ls /workspace/` — look for repos with real code
   - For each project, read the README, SPEC, and key source files to understand what was actually built
   - Check GitHub for the user's public repos: `curl "https://api.github.com/users/USERNAME/repos?per_page=100&sort=updated"`
   - Look for: algorithms implemented, architecture decisions, tech stack specifics, testing strategy, CI/CD, deployment
   - Read actual source code files — don't guess at what the project does from the directory name
   - Identify the user's **modeling/engineering philosophy** (e.g., "simplest model that works") and weave it into the resume
   - Extract specific technical details: algorithm names, library names, service architectures, data models
   - For each project, aim for 3-5 specific bullet points with real technical depth, not generic "built a full-stack app"
   - **If the user corrects you for being too shallow** ("you haven't spoken enough about project details"), go back and investigate more repos
   - **ALWAYS investigate repos BEFORE writing project descriptions.** Never write "built a full-stack application using React and Python" — that is a generic placeholder, not a resume bullet. The correct workflow is: (1) `ls /workspace/` to find project dirs, (2) read README/SPEC files, (3) read actual source code (especially algorithm implementations, architecture decisions, testing strategy), (4) check GitHub API for public repos, (5) THEN write descriptions with specific technical depth. If you haven't read the code, you haven't investigated.

1. Search workspace for existing resumes:
   ```bash
   find /workspace -iname '*resume*' -o -iname '*cv*' | grep -v venv | grep -v __pycache__ | grep -v node_modules
   ```
2. If NOT found locally, search Google Drive:
   ```bash
   GAPI="python ${HERMES_HOME:-$HOME/.hermes}/skills/productivity/google-workspace/scripts/google_api.py"
   # Search for resume files (--raw-query avoids shell quoting issues with single quotes)
   $GAPI drive search --raw-query "fullText contains 'resume' and mimeType != 'application/vnd.google-apps.folder'" --max 20
   # Download the most recent relevant file (file_id is positional, NOT --file-id)
   mkdir -p /workspace/resumes && cd /workspace/resumes
   $GAPI drive download FILE_ID --output resume_latest.pdf
   # For Google-native Docs files, export to pdf explicitly:
   $GAPI drive download DOC_ID --output resume.pdf
   # For docx files:
   $GAPI drive download DOC_ID --output resume.docx
   ```
   **Critical CLI syntax:** `drive download FILE_ID` — file_id is a positional argument. Use `--output` for local path. Do NOT use `--file-id FILE_ID` (that flag doesn't exist and will error).
3. If Drive auth fails (token expired), re-auth before proceeding:
   ```bash
   GSETUP="python ${HERMES_HOME:-$HOME/.hermes}/skills/productivity/google-workspace/scripts/setup.py"
   $GSETUP --auth-url
   # User opens URL in browser, copies redirected URL with code= parameter
   $GSETUP --auth-code "PASTE_CODE_OR_FULL_URL_HERE"
   ```
4. Read previous resume to extract formatting style (font, colors, section order, tone). Use `python-docx` to parse docx files:
   ```python
   from docx import Document
   doc = Document("/workspace/resumes/resume_latest.docx")
   for p in doc.paragraphs[:60]:
       if p.text.strip():
           print(f"[{p.style.name}] {p.text}")
   ```
   For PDF files, use `pymupdf` (not `pdftotext` which is not installed):
   ```python
   import fitz
   doc = fitz.open("/workspace/resumes/resume_latest.pdf")
   text = "".join(page.get_text() for page in doc)
   ```
5. Map user's background to job requirements (skill-by-skill table)
6. Write resume with: Header → Professional Summary → Core Skills → Qualifications → Employment History → Additional
7. Save to `/workspace/resumes/[COMPANY]_[ROLE]_Resume.docx`
8. Upload to Google Drive for user access:
   ```bash
   $GAPI drive upload /workspace/resumes/[COMPANY]_[ROLE]_Resume.docx --name "Sean Cheong Resume — [ROLE].docx"
   ```

**Formatting standard** (from established portfolio style):
- Font: Times New Roman or Calibri, 11pt body / 10pt skills / 18pt name
- Margins: 0.75"–1" all sides
- Header color: `1F4E79` (dark navy) for name; section headings use same color with bottom-border
- Section headings: UPPERCASE, 11pt, bold, with bottom border line
- Job titles: 10pt, bold, with company/location on same line separated by ` │ `
- Role subtitles: 10pt, italic (e.g., "In-person and over-the-phone personalised support for clients")
- Body/bullets: 10pt, space_after 2–3pt
- Tight paragraph spacing throughout
- Use `python-docx` — NOT Node.js docx package
- ATS compatibility: single-column, no tables (except optional contact line), no text boxes, no images

**Tone:** Conversational first-person. "A smooth sea never made a skilled sailor" — personality is welcome. Avoid corporate boilerplate ("I am a highly motivated individual...").

### Step 6 — Resume Tailoring Notes

Group keywords into:
1. **Technical keywords** — languages, frameworks, cloud platforms, tools (must appear verbatim)
2. **Soft/transferable skills** — stakeholder management, requirements gathering, etc.
3. **Company-specific language** — mirror the phrasing the employer uses ("digital transformation", "managed services", etc.)
4. **Certifications** — relevant certs that carry weight for the role

### Step 7 — Fit Assessment (if asked)

Evaluate the user's stated background against the job requirements:
- Which requirements does the user clearly meet?
- Which are stretch or missing?
- What is the overall strength as a candidate?
- What 1–2 things could strengthen the application most?

## Company Research Workflow

When researching a company for an application, use this multi-source fallback approach:

1. **Wikipedia** — `curl -sL "https://en.wikipedia.org/wiki/COMPANY"` — often has the best structured overview, history, financials, and key people. Works without JS.
2. **Google News** — `curl -sL "https://news.google.com/search?q=COMPANY&hl=en-AU&gl=AU&ceid=AU:en"` — extract article titles from the raw HTML (look for `>` delimited text containing the company name). Heavily JS-rendered but article titles are often in the initial HTML.
3. **ASX announcements** (for ASX-listed companies) — `curl -sL "https://www.asx.com.au/asx/v2/statistics/announcements.do?by=asxCode&asxCode=CODE&timeframe=D&period=M"` — returns a clean table of recent announcements with dates and headlines.
4. **Bing** — `curl -sL "https://www.bing.com/search?q=COMPANY"` — sometimes returns usable snippets when Google doesn't.
5. **Direct site scraping** — Try the company's investor centre, about page, and news sections. WordPress-based sites return usable HTML (strip scripts/styles). JS-rendered sites (React/Next.js) often return empty shells — skip these.
6. **LinkedIn** — Company page may show employee count and basic info in the initial HTML.

**Key principle:** Never rely on a single source. If one approach returns nothing useful, move to the next. Most company research requires 3-4 sources to build a complete picture.

**What to extract:**
- Company history, size, revenue, key executives
- Recent news (acquisitions, product launches, financial results)
- Culture signals (diversity accreditations, awards, Glassdoor reviews)
- Red flags (layoffs, controversies, culture issues)
- Competitors and market position

## Pitfalls

- **JS-rendered pages** — never trust raw curl HTML on modern career sites. Use JSON-LD or API endpoints. The curl output will look like New Relic agent code — that is not the job content.
- **Generic cover letters** — the single fastest way to get filtered. Name specific tracks, specific company work, specific projects.
- **Applying to too many tracks** — 2–3 is the max before ATS flags you as unfocused.
- **Fabricated requirements** — never invent requirements, preferred qualifications, or "must-haves" not in the posting. Stick to what is actually stated.
- **Missing eligibility checks** — note citizenship/residency requirements before generating application materials. Australian graduate programs often require citizen/PR.
- **Google Drive CLI syntax** — `drive download FILE_ID` takes file_id as a positional argument, NOT `--file-id`. Using `--file-id` causes `unrecognized arguments` error. Always use `--output` to specify the local download path.
- **Google Drive auth expiry** — OAuth tokens can expire or be revoked. If `drive search` or `drive download` fails with auth errors, re-run the auth flow (`setup.py --auth-url` → user authorizes → `setup.py --auth-code`). The `--auth-code` accepts either the full redirected URL or just the bare code string.
- **docx style parsing** — When reading previous resumes, some paragraphs may have `None` as style name (especially in Google Docs-exported docx). Guard with `p.style.name if p.style else "None"` to avoid `AttributeError`.
- **Resume reframe for career changers** — When the user's existing resume is tailored for a different role type (e.g., admin → software engineering), don't just tweak the existing resume. Create a new version that: (1) leads with relevant technical skills and projects, (2) reframes transferable skills from the old role (documentation → technical writing, CRM → database experience, problem-solving → debugging), (3) includes a projects section with GitHub links, (4) maps work history to the target role's language. Save as a separate file to avoid overwriting the original.
- **HTML resume print-to-PDF** — When generating HTML resumes, always remind the user to enable "Background graphics" in print settings and set margins to "None" — otherwise the accent bar and sidebar colors won't render in the PDF.
- **Shallow project descriptions** — The #1 quality failure in generated resumes. "Built a full-stack web application using React and Python" tells the employer nothing. Instead: name the specific algorithm (MCCFR, not "solver"), the specific libraries (PokerHandEvaluator, not "poker library"), the specific architecture (monorepo with shared types, not "well-structured"). Always read the actual source code before writing project descriptions. If the user says "you haven't spoken enough about project details," go back and investigate more repos.

## Sending CV via Email (Gmail API with Attachment)

The `gmail send` CLI subcommand (`google_api.py gmail send`) does NOT support file attachments. For sending a CV PDF with a cover email, use the Gmail API directly with a MIME multipart message.

### Python Pattern

```python
import base64, json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

creds = Credentials.from_authorized_user_file('/home/sc/.hermes/google_token.json')
if creds.expired:
    creds.refresh(Request())
    json.dump(json.loads(creds.to_json()), open('/home/sc/.hermes/google_token.json','w'), indent=2)

msg = MIMEMultipart('mixed')
msg['To'] = 'recipient@example.com'
msg['Subject'] = 'Application — Role Name'
msg['From'] = 'Sean Cheong <seanos1a@gmail.com>'

body = MIMEMultipart('alternative')
body.attach(MIMEText('''Cover email body here.''', 'plain'))
msg.attach(body)

with open('/path/to/cv.pdf', 'rb') as f:
    att = MIMEBase('application', 'pdf')
    att.set_payload(f.read())
    encoders.encode_base64(att)
    att.add_header('Content-Disposition', 'attachment', filename='CV - Role.pdf')
    msg.attach(att)

raw = base64.urlsafe_b64encode(msg.as_bytes()).decode('ascii')
service = build('gmail', 'v1', credentials=creds)
result = service.users().messages().send(userId='me', body={'raw': raw}).execute()
print('SENT:', result['id'])
```

### Pitfalls
- File path must exist when script runs — re-generate PDF if /tmp was cleaned
- From address must match the authenticated Gmail account
- The `gmail send` CLI cannot send attachments — always use the direct API for this
- **Resume project selection** — When choosing which projects to feature in resumes and cover letters, **diversify across the user's portfolio**. Do NOT default to GTO Wizard Clone as the only or primary example. The user's portfolio includes:
  - **OneTag** — open-source browser extension (Manifest V3, Chrome/Firefox/Safari, published to all 3 stores, 100+ users, real-time WebSocket sync, Supabase backend)
  - **Forrest** — AI-powered task management app (React, Node.js, OpenAI integration, real-time collaboration)
  - **LLM Benchmark** — benchmarking framework for evaluating LLM performance across providers
  - **GTO Wizard Clone** — poker training platform (MCCFR solver, hand history analysis, spaced repetition)
  - **Hermes Agent ecosystem** — multi-agent orchestration, Docker infrastructure, Cloudflare tunnels
  - **CasaOS / Open Lovable** — self-hosted dashboard and AI-powered site builder
  - **anihermes** — local anime server with natural language interface
  - **hermes-web-computer** — browser automation and web scraping framework
  - For **software engineering roles**: lead with OneTag (published extension, real users), Forrest (full-stack AI app), or LLM Benchmark (technical depth)
  - For **AI/ML roles**: lead with LLM Benchmark, Forrest (AI integration), or GTO Wizard (game theory + ML)
  - For **startup/generalist roles**: lead with OneTag (shipped product, multi-platform) or the Hermes ecosystem (infrastructure + tooling)
  - **Always match the project to the role** — the most relevant project should be the most detailed, not the most recent
  - In cover letters, name 2-3 projects maximum with specific technical details, not a laundry list

## Multi-CV Job Search System (High-Volume Campaign)

For users who want to run a systematic, high-volume job search across multiple role types rather than one-off applications.

### When to Use

- User asks to "streamline the process", "increase volume", "vary the roles", or "build a system"
- User has a broad skillset that maps to 3+ distinct role categories
- The goal is 20+ applications per week across varied targets, not 3-5 tailored ones

### The Approach

1. **Analyze the user's profile** for distinct role families. A Data Science graduate with full-stack delivery, database depth, and ML/RL work might fit: Python Backend, Data Engineer, Full-Stack, Solutions Engineer, ML/AI, DevOps, Data Analyst, Database Admin, Graduate.

2. **Create one CV variation per role category** — each reorders skills, experience highlights, and summary to lead with the most relevant material for that target. CVs should share a consistent visual identity (header, contact, styling) but differ in emphasis:
   - Role title changes per CV (Junior Software Engineer, Data Engineer, Solutions Engineer, etc.)
   - Skill section: reorder and filter tags to show category-relevant skills first
   - Summary: rewrite to lead with the role-appropriate angle
   - Experience: reorder bullet points, pick the most relevant ones
   - Projects: reorder and select those most relevant to the role

3. **Build a tracking spreadsheet** — CSV with columns: Date, Company, Role Title, Category, Platform, Salary, Link, Status, Notes, Follow-Up. Share via Google Drive.

4. **Define search queries per category** — 3-5 SEEK queries per role type that the user can paste directly.

5. **Create a daily rotation schedule** — e.g., Mon: Python-Backend + Full-Stack + Data; Tue: Solutions + DevOps + Analyst; etc. Each day = 30 min, 5 applications.

6. **Use Google Drive as the central hub** — create a Drive folder containing:
   - System playbook (.md)
   - Tracking spreadsheet (.csv)
   - All CV PDFs (one per category)
   - Market research (if applicable)
   The user can open this folder and run the system from there.

### Before Generating Media (CVs, Cover Letters, PDFs)

**Ask the user first. Do not charge ahead.**

1. Ask what format they want (PDF, docx, HTML, markdown)
2. Ask what QA criteria matter to them (page count, visual fidelity, ATS compatibility, specific template)
3. Ask if they want to review a sample before you batch-generate everything
4. Search for existing templates before creating new ones

This applies to ALL generated media — CV PDFs, cover letter documents, application materials.

### PDF Generation for CVs/Resumes — Host Chrome Only

When generating CV PDFs from styled HTML (two-column layouts, custom colors, tags, gradient headers):

**DO use the host Chrome pipeline** (produces faithful Tailwind/CSS rendering):
```python
SSH = ["ssh", "-i", "/home/hermeswebui/.ssh/id_ed25519", "-o", "StrictHostKeyChecking=no", "sean@172.19.0.1"]
SCP = ["scp", "-i", "/home/hermeswebui/.ssh/id_ed25519", "-o", "StrictHostKeyChecking=no"]

# Copy HTML to host
subprocess.run(SCP + [f"/workspace/cv.html", "sean@172.19.0.1:/tmp/cv.html"])

# Convert with Chrome
cmd = "google-chrome-stable --headless --no-sandbox --disable-gpu --print-to-pdf=/tmp/cv.pdf --no-margins file:///tmp/cv.html"
subprocess.run(SSH + [cmd], timeout=30)

# Retrieve
subprocess.run(SCP + [f"sean@172.19.0.1:/tmp/cv.pdf", "/workspace/cv.pdf"])
```

**DO NOT use fpdf2** for styled documents — the user rejected it as "awful" and it cannot replicate CSS layouts.

**Piataforms/Providers.**

### Common Pitfalls

- **Bot-blocking from container IPs** — Job sites (SEEK, Jora, Adzuna, LinkedIn) and search engines (Google, DuckDuckGo) block requests from container IPs. You cannot scrape live listings from inside a container. Either: (a) ask the user to search and share URLs, or (b) provide ready-to-paste search queries they can run themselves.
- **Tandem Browser workaround for bot-blocked sites** — When sites block container IPs (Cloudflare, anti-bot), use the Tandem Browser shared session (`~/.hermes/scripts/electron-viewer.js` on localhost:3099, also accessible via `browse.codeovertcp.com`). The user logs into the site in their Tandem Electron window (which has better browser fingerprinting through Electron's Chrome), and you control the same session via CDP. See the `tandem-browser-shared-session` skill for full setup. Workflow: (1) User navigates to site in Tandem and logs in, (2) You navigate/search via `curl -X POST http://localhost:3099/navigate`, (3) You screenshot via `http://localhost:3099/screenshot.png`, (4) You click elements via `/click` at coordinates from vision analysis.
- **Too many categories dilutes focus** — 9 is the upper limit. Beyond that, the CVs become indistinguishable and you're just spamming.
- **Page breaks in two-column PDFs** — When generating programmatically, page 1 has sidebar + main; page 2 should be full-width with a slim header only. The sidebar doesn't carry to page 2.
- **Cover letter for high-volume campaigns** — Use a single template with 3 placeholders (role category, 1-2 relevant projects, company-specific sentence). Don't write unique cover letters for 5+ daily applications — the ROI doesn't justify it.

## Output Format

Produce all sections in a single document:
1. Application Strategy (ranked table + strategic notes)
2. Cover Letter Template (with placeholders)
3. Resume Tailoring Notes (4 keyword groups)

Deliver as a file at `/workspace/[COMPANY]_[PROGRAM/ROLE]_Career_Coaching.md` and display the key content inline.

## References

- `references/dxc-jsonld-extraction.md` — DXC careers page JSON-LD extraction example and Workday API patterns
- `references/cover-letter-template.md` — reusable cover letter structure for graduate programs
- `references/docx-resume-style.md` — python-docx formatting standard (fonts, colors, spacing, table patterns) for resume generation
- `references/short-answer-responses.md` — short answer response format for tech job applications (bug stories, code changes, tech checklists)
- `references/multi-cv-search-system.md` — Google Drive folder structure, rotation schedule, daily workflow, search query template, and CV variation strategy for high-volume multi-role campaigns