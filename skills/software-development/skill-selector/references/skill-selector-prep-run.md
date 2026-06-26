# skill-selector-prep reference — what the script does and why

**What it is:** A Python script (`skill-selector-prep.py`) that syncs 5 source repos, computes metadata for all skills, pre-scores them against workspace contexts, and writes cache files consumed by `skill-selector` every turn.

**Source repos (all on GitHub, cloned to host at `/tmp/skill-selector-prep/`):**
- `VoltAgent/awesome-agent-skills` → ~800 skills, README bullet format
- `mattpocock/skills` → 28 skills, per-skill SKILL.md files in `.claude/` dirs
- `0xNyk/awesome-hermes-agent` → ~300 skills, mixed README formats
- `vercel-labs/skills` → ~4 skills, README
- `expo/skills` → ~4 skills, README

**Cache files written:**
- `skill_metadata.json` — 1,441 skills with name/category/description/tags/size/source
- `context_scores.json` — per-skill pre-computed relevance scores per workspace (hermes-web-computer, agent-os, seans-reporepo, repo-transmute-v2)
- `batches.json` — 50 batches of ~30 skills each (for LLM summary generation)
- `skill_summaries.json` — LLM-generated summaries for 481/1441 skills (batches 0-16 were processed, 17-50 pending)

**Key scripts:**
- `/home/hermeswebui/.hermes/scripts/skill-selector-prep.py` — main prep script
- `/home/hermeswebui/.hermes/scripts/skill-selector.py` — every-turn scorer
- `/home/hermeswebui/.hermes/scripts/process_batches.py` — LLM batch summarizer (called by prep or run standalone)

**Two-layer architecture:**
1. Local skills (~167): registered in `~/.hermes/skills/`, visible to `skills_list`
2. Imported skills (1,274): in `skill_metadata.json`, NOT registered in local skills dir

**To finish batch summarization (960 skills remaining):**
Run `process_batches.py` in background — it reads `batches.json` and processes from the next undone batch.