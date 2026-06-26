---
name: linkedin-post-pipeline
description: "Daily LinkedIn post pipeline — drafts, hooks, content pillar rotation, and queue management. Trigger when running the daily LinkedIn cron, drafting LinkedIn posts, or managing the post queue."
---

# LinkedIn Daily Post Pipeline

Automated daily LinkedIn post generation with structured hook formulas, content pillar rotation, and file-based queue.

## Content Pillar Rotation (by day)

| Day       | Pillar     | Focus |
|-----------|------------|-------|
| Monday    | Build Log  | What shipped this week |
| Tuesday   | Teach      | Explain a concept from your work |
| Wednesday | Hot Take   | Opinion on AI infra / self-hosting |
| Thursday  | Community  | Shoutout or collab |
| Friday    | Build Log  | Weekly roundup |

**Content domains to draw from:** Hermes WebUI, agent-os, HWC tiling desktop, TrueNAS self-hosting, Playwright automation, n8n workflows, Go/Svelte5 development.

## Hook Formulas

Rotate through these proven hook types:

1. **Pattern Interrupt + Vulnerability** — "Most weeks I ship 3 things and forget about them. This week I actually wrote them down."
2. **Contrarian** — "Everyone says X. They're wrong. Here's why."
3. **List/Number** — "5 things I learned building X this week:"
4. **Question** — "What if the bottleneck isn't where you think it is?"
5. **Behind the Scenes** — "Here's what actually happens when you deploy X:"
6. **Myth-Busting** — "Self-hosting is dead. Except it isn't. Here's the data."
7. **Story Opener** — "Last Tuesday at 2am, a smoke test caught something I'd ignored for weeks."

## Post Structure

1. **Hook** (1-2 lines, pattern interrupt or curiosity gap)
2. **Body** (150-250 words total post) — 3-5 bullet items with specific metrics, tools, or outcomes
3. **CTA** — End with a question or invitation to engage
4. **Hashtags** — 6-8 relevant tags at the end

## Draft File Format

Save to `/opt/data/linkedin-drafts/YYYY-MM-DD.md`:

```markdown
# LinkedIn Post Draft — YYYY-MM-DD

## Pillar
[Build Log | Teach | Hot Take | Community]

## Hook Formula
"[Hook text]"

## Post Text

[Full post body]

## Hashtags
#tag1 #tag2 #tag3

## Status
draft
```

## Queue System

Queue script: `/opt/data/linkedin-queue-post.py`

```bash
cd /opt/data && python3 linkedin-queue-post.py "POST_TEXT"
```

Writes JSON queue entries to `/opt/data/linkedin-queue/post-TIMESTAMP.json` with fields: `id`, `text`, `status`, `created_at`, `platform`.

The queue is consumed by the n8n webhook or Playwright bot — do NOT invoke those directly from the cron job.

## Execution Steps (cron)

1. Determine day of week → select pillar
2. Select a hook formula (rotate, don't repeat)
3. Draft post (150-250 words) drawing from recent work
4. Save draft to `/opt/data/linkedin-drafts/YYYY-MM-DD.md`
5. Run queue script with post text
6. Report: post drafted, hook used, queue status

## Support Files

- `references/hooks.md` — Hook formula quick reference with 7 hook types, examples per pillar day, and selection rules.
- `scripts/linkedin-queue-post.py` — Queue script that writes JSON entries to `/opt/data/linkedin-queue/`. Copy to `/opt/data/` if missing.

## Pitfalls

- **Skill file not found at expected path:** The `linkedin-hooks` skill may not exist. Don't fail — use the hook formulas documented here instead.
- **/workspace not writable:** Use `/opt/data/` as the base directory for drafts and queue.
- **Queue script missing:** Copy `scripts/linkedin-queue-post.py` to `/opt/data/linkedin-queue-post.py`.
- **Don't run Playwright bot directly:** The cron job only drafts and queues. The bot picks up from the queue separately.
- **Post too long:** Keep under 250 words. LinkedIn truncates at ~1,400 chars but engagement drops after ~150-200 words.
- **Missing CTA:** Every post should end with a question or engagement prompt.
