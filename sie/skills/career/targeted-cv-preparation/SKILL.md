---
name: targeted-cv-preparation
description: |
  Build a targeted CV for a specific job application by researching the
  company, extracting role requirements, auditing the repo catalog for
  relevant projects, and iterating content with the user in a
  consultative "grill me" style — not a one-shot deliverable.
category: career
trigger:
  - User says "tailor my CV for this role" or "help me apply to X"
  - User shares a job ad and asks what to include in their CV
  - Before writing any CV content for a specific role
  - User says "grill me about what to include"
related_skills: [seans-reporepo-query, visual-qa]
---

# Targeted CV Preparation

A consultative workflow for building role-specific CVs by cross-referencing company research, job requirements, and the personal repo catalog. **Every line in the CV is justified by a role requirement.** Nothing goes in because "it's a good project" — everything goes in because it demonstrates a specific skill the employer asked for.

## The Workflow

### Phase 1 — Company & Role Research

Before touching the CV, understand who you're selling to:

1. **Extract structured requirements** from the job ad into a table:

   | Requirement Category | What They Asked For | Evidence We Have |
   |---------------------|--------------------|-------------------|
   | Hard skills | e.g. Docker, automation | e.g. agent-os, CasaOS webhook emitter |
   | Soft/cultural signals | e.g. "home lab", "builds things" | e.g. self-hosted infra, dotfiles |
   | Experience level | e.g. early-career, second-role | e.g. degree timeline, project history |
   | Bonus/plus items | e.g. "cloud a plus (training provided)" | e.g. Cloudflare tunnel experience |

2. **Research the company** — who are they, what do they do, size, culture, who's the recruiter/agency. For agency-placed roles (like Harvey Robinson), the CV has to impress the recruiter first before it reaches the client.

### Phase 2 — Portfolio Audit via Repo Catalog

Use `seans-reporepo` to find matching projects:

1. **Scan the owned repos** (`/home/sc/repos/seans-reporepo/owned/`) for projects relevant to each requirement extracted in Phase 1.

2. **Read the actual repo descriptors** — the frontmatter `description` field tells you what the project ACTUALLY does and which tags apply, not just what the name suggests.

3. **Rank by relevance** to the specific role:
   - **Tier 1** — Direct hits: repos that demonstrate the exact skills in the job ad (infrastructure, automation, Docker, Go, etc.)
   - **Tier 2** — Breadth signals: repos that show engineering rigour, production habits, testing discipline
   - **Skip** — Repos that are irrelevant to this role (ML/data science for a SysEng role; frontend-heavy for a backend role)

4. **Present the options to the user** — do NOT pick the final content yourself. List what fits and why, then let the user push back, add, or remove.

### Phase 3 — Collaborative Content Building ("Grill Me")

**This is the critical step.** Do not write a full CV and present it as done. Instead:

1. **Suggest specific content items** — "I think your self-hosted infra story belongs in Experience because it directly demonstrates the home-lab culture they want. Your GTO Wizard project is impressive but less relevant for this role — I'd drop it."

2. **Justify every suggestion** — "The CasaOS webhook emitter shows Go automation with event-driven architecture, systemd integration, and retry logic — all three match requirements in the ad."

3. **Let the user push back** — they'll know which projects they want to lead with, which clients they want to feature, and what narrative they're comfortable with. Respect their judgment.

4. **Iterate** — propose a section → user adjusts → propose the next section. Don't try to get it perfect in one shot.

### Phase 4 — Format & Page Decision

Once content is agreed:

1. **Decide page count** based on content density:
   - **1 page** — early-career/grad, or when content is tight enough (aim for 25-35 lines of body)
   - **2 pages** — mid-career with substantial experience

2. **Structure the CV**:
   - **Header**: Name, email, phone, location (Sydney/NSW), GitHub link
   - **Summary**: 2 lines max. Frames the candidate for THIS role, not a generic bio.
   - **Skills**: 1 dense line covering the key stack elements
   - **Experience**: 2-3 entries. Each with a clear project/client name, date/context tag, and 3-5 bullet points. Every bullet should tie back to a requirement from the job ad.
   - **Education**: 1 line. Degree, university, year.

3. **Style defaults** (from this user's preferences):
   - Body text: 9-10.5pt minimum. Never below 9pt.
   - Line spacing: 1.6-1.8 for all running text. Below 1.5 = too cramped.
   - Blank space target: below 25%. When content is sparse, increase font/spacing to fill.
   - Footer: "Additional projects and references available at github.com/ChonSong"

## Pitfalls

### Don't One-Shot Deliver
The user explicitly wants "grill me" style — suggest, justify, iterate. Writing a complete CV and presenting it as finished skips the most important part (getting buy-in on what to include). You'll waste time reformatting content they'd have rejected earlier.

### Don't Skip the Repo Catalog
The user corrected this explicitly: "i meant i wanted seans reporepo to be reviewed for resume inclusions." The catalog is the authoritative source of what projects exist. Skipping it means you'll suggest projects from memory and miss relevant ones.

### Don't Skip the "Grill Me" Step
The user wants to be consulted on what goes into the CV — suggest options with justifications, let them push back, iterate. Writing a complete CV in one shot skips the validation step and wastes time on content they'd reject.

### Don't Include Irrelevant Projects for Padding
Every project on the CV should tie directly to a role requirement. "This is a good project" is not sufficient grounds for inclusion. If a project doesn't demonstrate something the employer asked for, it dilutes the signal.

### Don't Lead with Education
For Sean, the production portfolio is the stronger signal. Education goes at the bottom. The summary should lead with what they've actually built, not where they studied.

### Don't Use the Wrong CV Variant
Sean has 9 CV variants. For any specific role, pick the one whose angle matches the role, then tailor further. Don't start from scratch — use the closest variant as a base.

## References

- `references/harvey-robinson-systems-engineer.md` — worked example from the session that produced this skill: research output, role requirements table, repo-to-requirement mapping, and the final 1-page CV structure.
- `references/job-ad-analysis-template.md` — template for extracting structured requirements from any job ad.
