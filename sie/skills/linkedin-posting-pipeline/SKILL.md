---
name: linkedin-posting-pipeline
description: "LinkedIn daily post pipeline — draft generation, queueing, and publishing automation. Covers content pillars, hook formulas, draft storage, and infrastructure status. Use when running the daily LinkedIn cron, creating post drafts, or troubleshooting the posting pipeline."
---

# LinkedIn Posting Pipeline

## Overview

Automated weekday LinkedIn posting pipeline for an AI/self-hosting focused personal brand. Generates drafts using hook formulas and content pillars, stores them locally, and queues for publishing.

## Correct Infrastructure Paths

**CRITICAL — The cron job references wrong paths. Use these instead:**

| What | Wrong Path (in cron) | Correct Path |
|------|---------------------|--------------|
| Draft directory | `/workspace/linkedin-drafts/` | `/opt/data/linkedin-drafts/` |
| Queue script | `/workspace/linkedin-queue-post.py` | **Does not exist** |
| Skill file | `/home/hermeswebui/.hermes/skills/linkedin-hooks/SKILL.md` | **Does not exist** |
| Audit reports | — | `/opt/data/linkedin-audit/` |

## Content Pillar Rotation (Mon-Fri)

| Day | Pillar | Description |
|-----|--------|-------------|
| Monday | Build Log | What shipped this week |
| Tuesday | Teach | Explain a concept from your work |
| Wednesday | Hot Take | Opinion on AI infra / self-hosting |
| Thursday | Community | Shoutout or collab |
| Friday | Build Log | Weekly roundup |

## Topics to Draw From

- Hermes WebUI dashboard
- agent-os (multi-agent orchestration)
- HWC tiling desktop (window management)
- TrueNAS self-hosting
- Playwright browser automation
- n8n workflow automation
- Go backend + Svelte5 frontend development

## Hook Formulas

### Build Log Hook
> "I spent [time] building [thing]. Here's what I learned."

### Teach Hook
> "Most people get [concept] wrong. Here's the right way to think about it."

### Hot Take (Contrarian) Hook
> "Unpopular opinion: [contrarian statement]."

### Community Hook
> "Shoutout to [person/project] for [specific thing]. Here's why it matters."

### Weekly Roundup Hook
> "This week in [project/area]: [highlight 1], [highlight 2], and [highlight 3]."

## Draft Format

Save each draft as `/opt/data/linkedin-drafts/YYYY-MM-DD.md`:

```markdown
# LinkedIn Post Draft — YYYY-MM-DD (Day)

**Pillar:** [Pillar Type]

**Hook used:** "[Hook formula used]"

---

## Post Text

[150-250 words, conversational tone, end with question or CTA]

#hashtag1 #hashtag2 #hashtag3

---

**Status:** draft
```

## Posting Infrastructure Status

**As of 2026-06-03: DOWN**

| Component | Status |
|-----------|--------|
| Chrome CDP (port 9222) | 🔴 Not running |
| n8n (port 5678) | 🔴 Not running |
| Host SSH (172.19.0.1) | 🔴 Key mismatch |
| linkedin-queue-post.py | 🔴 Does not exist |
| linkedin-browser.py | 🔴 Does not exist |
| Draft storage | 🟢 Working at `/opt/data/linkedin-drafts/` |

## Publishing Workflow (When Infrastructure Is Up)

1. Generate draft using hook formula and pillar rotation
2. Save to `/opt/data/linkedin-drafts/YYYY-MM-DD.md`
3. Queue for publishing (script TBD — none exists yet)
4. Update draft status to `queued` → `published`

## Hashtags Pool

Rotate 5-8 from: `#AI` `#SelfHosting` `#Agents` `#Hermes` `#TrueNAS` `#Svelte5` `#Go` `#Automation` `#n8n` `#Playwright` `#DevOps` `#AgentOps` `#OpenSource` `#WebDevelopment`

## Pitfalls

- **Wrong paths**: The original cron job references `/workspace/` which is not accessible from the hermes container. Always use `/opt/data/linkedin-drafts/`.
- **No queue script**: `linkedin-queue-post.py` does not exist. Drafts are saved locally but cannot be auto-published until the infrastructure is rebuilt.
- **Infrastructure dependency**: Publishing requires Chrome CDP + n8n + host SSH. All three have been down since at least 2026-06-01.
- **Skill file missing**: There is no `linkedin-hooks` skill file. This skill replaces it.
