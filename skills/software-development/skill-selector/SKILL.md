---
name: skill-selector
description: Every-turn skill scorer. Scores all 1,441 remote + local skills against the current task context and loads matching ones silently (or asks if >100MB). Powered by cached metadata from skill-selector-prep. Run this on EVERY turn — it is lightweight.
category: software-development
tags: [skills, autonomy, auto-load, context-awareness]
required_environment_variables: []
required_commands: ["python3"]
---

## Overview

Every turn, score and load skills relevant to the current task — without asking, unless the skill is large (>100MB). This is the per-turn selector; the `skill-selector-prep` cron keeps its cache fresh.

## ⚠️ Cache Status — 2026-05-26

Cache is LIVE — populated from May 25 run:
- `skill_metadata.json`: **1,441 skills** (1441 imported from 5 repos + local)
- `skill_summaries.json`: **481/1441 skills** have LLM summaries (remaining ~960 not summarized — batch processing was interrupted at batch 16/50)
- `batches.json`: 50 batches exist; first 16 were processed, batches 17-50 are pending
- Cron `65520f7d71f9` (Sunday 06:00 UTC) has never fired — manual trigger needed to finish

Two-layer architecture:
1. **Local skills** (~167): registered in `~/.hermes/skills/`, visible to `skills_list`, full content loadable
2. **Imported skills** (1,274): parsed from VoltAgent/awesome-agent-skills (800+), mattpocock (28), 0xNyk (300+), vercel-labs (1), expo-skills (15) — stored in `skill_metadata.json` and `skill_summaries.json`, NOT visible to `skills_list` unless registered

Registration required to bridge layers — see `skill-selector-prep` script.

## Scoring Pipeline

```
task_text
  → classify_task() → task_types (14 categories) + stages (7 workflow stages)
  → score_by_summary() for each skill → base score
  → + context_scores (pre-cached per workspace, from prep)
  → sort, take top 10 local skills
  → LLM tiebreaker (only if borderline AND API key available)
  → decide() → "load" / "ask" / "skip"
  → format output
```

### Task Type Classification (rule-based, no LLM)

14 categories with keyword patterns:

| Type | Keywords |
|------|----------|
| deployment | deploy, ship, release, production, staging, kubernetes, helm, rollback, docker push, publish |
| git_operation | git, commit, branch, merge, pr, pull request, push, clone, fork, rebase |
| coding | implement, write code, function, component, fix bug, refactor, add feature, typescript, python, golang, rust, react, svelte, node |
| debugging | bug, crash, error, break, not working, issue, failed, exception, traceback, fix the |
| research | research, arxiv, paper, find, search for, look up, investigate, explore |
| creative | generate image, create video, make art, ascii, svg, animation, music, song, design |
| writing | write, essay, document, report, summary, article, blog post, draft |
| planning | plan, roadmap, architecture, design for, how to build, blueprint, spec out |
| devops | ci/cd, pipeline, terraform, ansible, nginx, apache, config, setup server, cron, backup |
| data_analysis | analyze, jupyter, pandas, notebook, visualize, chart, graph, data |
| autonomous | autonomous, roadmap, self-improve, learn and, iterate on |
| configuration | configure, setup, install, enable, disable, settings, config |
| monitoring | monitor, watch, alert, metrics, dashboard, health, uptime |
| smart_home | hue, light, sonos, smart home, home assistant, philips |
| media | spotify, youtube, gif, play audio, video |

### Workflow Stages

understand, plan, implement, test, review, deploy, monitor

Default stage: implement (if none detected).

### Score Weights

- Task type match: **+3.0**
- Workflow stage match: **+2.0** per stage
- Summary keyword match: **+0.3** per keyword (from task text)
- Category match: **+1.5**
- Pre-cached workspace score: added directly (cap 2.0 per skill)

### Decision Thresholds

| Score | Action |
|-------|--------|
| ≥3.0 | Load silently |
| ≥1.5 | Load |
| <1.5 | Skip |
| >100MB | Always ask |

MAX_LOAD = 5 per turn.

### LLM Tiebreaker

**Only fires when:** top score < 5.0 (borderline) AND API key available.

One call max per turn. Feeds top 8 candidates with one-line summaries → LLM returns `{skill_name: bool}`. Selected skills get +2.0 boost.

**OpenRouter via `poolside/laguna-xs.2:free`** — `openrouter/auto` routes to a paid model that returns 402. `poolside/laguna-xs.2:free` works but truncates JSON responses mid-way. LLM tiebreaker is functional but coverage is limited. If API key unavailable, scoring falls back entirely to keyword/description matching — still works, just less precise.

## Pitfalls

- **Hardcoded paths required** — `Path.home()` resolves to `/home/hermeswebui/.hermes/home` inside the container (not `/home/hermeswebui`). Always use absolute paths `/home/hermeswebui/.hermes/...` or the cache lands in the wrong directory. This applies to ALL scripts running in this environment, not just skill-selector.
- **Context scores capped at 2.0 per skill** — prevents high-base-score skills (e.g., agent-os at 16.2) from dominating. Workspace keyword matching can still out-rank capped skills.
- **Threshold calibration** — `>= 3.0` = silent load, `>= 1.5` = load. Produces 2–3 skills on typical tasks. If too noisy, raise silent threshold to 4.0.
- **Script exits 0 silently if no keywords extracted** — correct behavior, not an error.
- **Skill catalog: 1,320+ skills** (1,167 remote + 153 local as of 2026-05-25). Remote skills score on description text only — no SKILL.md content. Local skills have richer metadata from their own SKILL.md frontmatter.
- **OpenRouter free tier WORKING 2026-05-25** — `openrouter/free` routes to free models (nvidia/nemotron-3-nano, poolside/laguna-xs.2). Container must use host SSH tunnel: `ssh sean@172.19.0.1` then `curl -d @-` piping JSON payload through stdin. Previously returned 402 (credits exhausted) — now resolved. If 402 returns again, scoring falls back to keyword/description matching.
- **OpenRouter 402 on summary generation** — `google/gemini-2.5-flash-lite` free tier has daily request caps. When 402 fires during batch summary generation, skills fall back to description-only scoring. Not fatal — just means remote skills score slightly lower until quota resets.
- **MAX_LOAD = 5** — prevents context bloat. If relevant skills consistently exceed 5, raise to 8 or narrow STOPWORDS.
- **`.env` must be loaded before API key access** — Python module-level assignments run before `_load_env()` is called. In `generate-skill-summaries.py`, `_load_env()` is called at the TOP of the module (before any `API_KEY=` lines) to ensure keys are available for the batch LLM calls. This was the root cause of 0 summaries on the first run.
- **Triple backtick in Python strings** — `"\`\`\`"` in Python source is an invalid escape sequence (treated as literal backslash + backticks). Use `chr(96)*3` or raw string `r"```"` when constructing triple-backtick code block strings programmatically.

## Script Locations

All scripts live in `/home/hermeswebui/.hermes/scripts/`:
- `skill-selector.py` — every-turn scorer (11,579 bytes, lint OK)
- `skill-selector-prep.py` — daily cache builder (10,733 bytes, lint OK)
- `generate-skill-summaries.py` — LLM batch summarizer (6,167 bytes, lint OK)

Cache lives in `/home/hermeswebui/.hermes/skill-selector-cache/`:
- `skill_metadata.json` — 153 skills with size/category/tags
- `context_scores.json` — per-workspace pre-computed scores
- `skill_summaries.json` — **151 LLM-generated summaries** + 11 group descriptions (generated via OpenRouter `openrouter/auto` → `google/gemini-2.5-flash-lite`) — game-changer for scoring accuracy

## System Prompt Injection

**Status as of 2026-05-26: Uncertain.** The skill documents that injection was done via `SKILLS_GUIDANCE` in `agent/prompt_builder.py` on the host, but this session shows no evidence of auto-firing. The script at `/home/hermeswebui/.hermes/scripts/skill-selector.py` must be called manually per turn — either by you (this session) or by a cron-driven agent loop in other contexts.

Do NOT assume it fires automatically. **Always call it explicitly** when you remember: run `python3 /home/hermeswebui/.hermes/scripts/skill-selector.py "<user message>" "<workspace>"` at the start of any turn where skills might be relevant.

```python
SKILLS_GUIDANCE = (
    "After completing a complex task..."
    + "\n\n## Auto-loaded skills\n"
    "On every turn, BEFORE searching for or loading any skill, call the "
    "skill-selector to score and auto-load the most relevant skills:\n"
    "python3 /home/hermeswebui/.hermes/scripts/skill-selector.py "
    "\"<user message>\" \"<workspace>\"\n"
    ...
)
```

The agent sees this in its system prompt on every turn. It runs the scorer with the
user's actual message + `TERMINAL_CWD` workspace. Output like `Auto-loaded:
react-agent, go, zoul` — agent suppresses the raw script output and loads the
named skills via `skill_view(name)`.

## Related

- `skill-selector-prep`: weekly cron (Sunday 06:00 UTC) that builds the cache — updated from daily to weekly on 2026-05-25