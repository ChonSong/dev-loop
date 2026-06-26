---
name: skill-selector
description: Every-turn skill scorer. Scores all ~3,928 skills against the current task context, auto-loads the top 5 matches into every session.
category: software-development
tags: [skills, autonomy, auto-load, context-awareness]
source: local
is_imported: true
---

# skill-selector

Every-turn skill scorer. Scores all **~3,913** skills against the current task context, auto-loads the top 5 matches into every session.

**Category:** software-development  
**Source:** local (installed from 5 source repos: awesome-hermes-agent, awesome-agent-skills, mattpocock-skills, vercel-labs-skills, expo-skills)  
**Cache:** `~/.hermes/skill-selector-cache/` (3,913 skill metadata, 2,799 context scores)

---

## Architecture

```
SKILLS_GUIDANCE (prompt_builder.py:166-185)
  → every-turn: run skill-selector.py with current task
  → auto-loads top 5 scored skills into session

skill-selector.py          # Runtime scorer — runs each turn
skill-selector-prep.py     # Weekly cache refresh (cron job 65520f7d71f9)
skill-selector-cache/
  skill_metadata.json      # 3,928 skills (name, description, category, tags)
  skill_summaries.json     # removed (no longer generated)
  batches.json             # removed (no longer used)
  context_scores.json      # Per-task context scoring (2,799 skills)
  last_refresh.txt         # 2026-05-26T03:03Z
```

---

## Workflow

**Every turn:**
1. SKILLS_GUIDANCE fires — calls `skill-selector.py` with the current task description
2. Script scores all 2,726 local + 1,202 remote = **3,928 total** skills against task context using keyword + semantic signals
3. Top 5 skills auto-loaded into session

**Weekly (cron job `65520f7d71f9`, Sundays 06:00 UTC):**
1. `skill-selector-prep.py` runs on host at `/home/sean/.hermes/scripts/`
2. Pulls fresh skill listings from 5 source repos
3. Sanitizes names (replaces `/` with `-` to avoid path issues)
4. Generates summaries via LLM (Nixi-EN/OpenRouter-200k-context-with-thinking) or synthetic fallback
5. Updates `skill_metadata.json` and `skill_summaries.json`

---

## Key Behaviours

- **Lazy loading** — skills only loaded when matched. 2726 local + 1187 remote = ~3913 total skills in registry does not cost tokens unless selected.
- **Synthetic summaries** — when LLM APIs are unavailable, summaries are generated from skill description fields. 954/1,440 use synthetic summaries; 481 use real LLM.
- **Name sanitization** — skills with `/` in names installed as `-` equivalents. Original name preserved in SKILL.md frontmatter.
- **Every-turn scoring** — the SKILLS_GUIDANCE instruction in `prompt_builder.py` fires on every user message, not on slash commands. This is the correct integration point.

---

## Adding New Source Repos

Edit `skill-selector-prep.py` on the host at `/home/sean/.hermes/scripts/skill-selector-prep.py`. Add the repo to the `REPOS` list:

```python
REPOS = [
    ("owner/repo", "optional-category-name"),
    # ... existing repos
    ("new-owner/new-repo", "new-category"),
]
```

Then manually trigger a cache refresh:
```bash
python /home/sean/.hermes/scripts/skill-selector-prep.py
```

---

## Pitfalls

- **Blind dump is not routing.** Dumping all 612 skill names into the system prompt without ranking does NOT constitute intelligent skill selection. The LLM cannot meaningfully score 612 entries — it tends to grab a few obvious names and miss domain-relevant skills buried in the list.
- **skill_selector.py is the intended scorer but not integrated into prompt assembly.** The script in `~/.hermes/scripts/skill-selector.py` scores all skills by keyword + project tags + recency and returns a ranked shortlist. If its output is not being injected into `build_skills_system_prompt()` in `prompt_builder.py`, the routing loop is broken — file a bug to fix the integration.
- **Two colliding entries block loading.** Both `skill-selector` (root) and `software-development/skill-selector` exist. `skill_view` refuses a bare name — load via `skill_view(name='software-development/skill-selector')` or report to curator for deduplication.
- **Auto-loading top 5 is not happening.** The system prompt instructs scanning + loading matching skills, but without wiring skill_selector.py output into prompt assembly, no ranked shortlist is produced. Agents default to grabbing a few high-visibility names and missing domain-specific skills.
- **Skills with `/` in names** were sanitized to `-` at install time (e.g. `vendor/pkg-name` → `vendor-pkg-name`). The original name in SKILL.md frontmatter is preserved.
- **Synthetic summaries** are fallbacks — real LLM summaries require OpenRouter credits. Current state: 481 LLM + 954 synthetic.
- **`deliver: all` silently fails** if fewer than 2 channels are wired. Cron output delivery does not use this field — the job prompt must call `send_message` for Discord delivery.
