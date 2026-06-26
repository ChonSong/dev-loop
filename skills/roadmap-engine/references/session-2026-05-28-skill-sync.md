# Skill Sync Architecture — May 2026

## The Skill Count Gap

**System prompt claim:** ~1,440 skills  
**Actual count (May 2026):** ~89 skills across 25 categories on disk

**Root cause:** The `skill-selector-prep` weekly cron job stopped syncing 5 remote repos because OpenRouter credits exhausted, and the synthetic summary fallback wasn't generating descriptions for already-cloned skill repos.

## Skill Sync Pipeline

```
skill-selector-prep.sh (weekly cron, Sunday 06:00 UTC)
  └─> sync_skills.sh --generate-summaries
        ├─ (1) Clone 5 remote repos into ~/.hermes/skills/remote/
        ├─ (2) For each cloned skill: generate SKILL.md description via OpenRouter
        └─ (3) Install skills to ~/.hermes/skills/<category>/
```

**Step (1) is independent of OpenRouter credits.** The `git clone` operations complete regardless.

**Step (2) requires OpenRouter credits.** Without credits, step (2) silently skips → skills lack descriptions but files are present.

**Step (3) installs skills using the repo structure** — doesn't require descriptions.

## The 5 Remote Repos

| Repo | Path in `~/.hermes/skills/remote/` |
|------|--------------------------------------|
| `coding-at-scale/skills` | `remote/ai-agents/` |
| `coding-at-scale/design-patterns` | `remote/design-patterns/` |
| `coding-at-scale/enterprise-patterns` | `remote/enterprise-patterns/` |
| `coding-at-scale/ai-agents` | `remote/ai-agents/` |
| `coding-at-scale/devops-advanced` | `remote/devops-advanced/` |

## Manual Recovery (No Credits Required)

```bash
# Run sync with fallback (no summarization)
SKILL_SUMMARIES_SOURCE=none bash ~/.hermes/scripts/sync_skills.sh

# Verify repos cloned
ls ~/.hermes/skills/remote/coding-at-scale/

# Verify skill files present
find ~/.hermes/skills/remote/coding-at-scale -name "SKILL.md" | wc -l
```

Exit code 0 = success. Repos are cloned to `~/.hermes/skills/remote/coding-at-scale/`.

## Credit Exhaustion Pattern

```json
{"error":{"code":0,"message":"You have run out of credits. Please add moreCredits."}}
```

When credits are exhausted, the `skill-selector-prep.sh` script detects the error and sets `SKILL_SUMMARIES_SOURCE=none` as fallback. **But this only works if the script has already been run at least once before** — the first run fails silently with the above JSON before the fallback logic can trigger.

## The `roadmap-engine` Skill Anomaly

`skill_manage` (patch/write_file) cannot find `roadmap-engine` even though:
- `skill_view(name="roadmap-engine")` → ✅ resolves
- `skill_view(name="autonomous-ai-agents/roadmap-engine")` → ✅ resolves
- `skills_list()` shows it under category `autonomous-ai-agents` → ✅ resolves
- `skill_manage(action="patch", name="roadmap-engine")` → ❌ "not found"
- `skill_manage(action="patch", name="autonomous-ai-agents/roadmap-engine")` → ❌ "not found"

The skill has `source: local` and `is_imported: true` in its frontmatter. The `skill_manage` tool appears to fail on skills imported from `remote/` directories even when they are displayed as local skills. Workaround: use `skill_view` + `skill_manage` with a direct file write via `write_file`.

**Discovered:** 2026-05-28, during manual skill sync investigation.

## Skills That Needed Updates This Session

| Skill | Action | Reason |
|-------|--------|--------|
| `writing-plans` | Check for update fit | Key workflow skill for this task type |
| `subagent-driven-development` | Check for update fit | Delegation pattern used |
| `roadmap-engine` | Reference doc added | Learned skill sync architecture + anomaly |
