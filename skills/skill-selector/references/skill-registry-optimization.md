# Skill Registry Optimization — Full Analysis

**Date:** 2026-05-28
**Status:** Analysis complete, implementation pending approval

## Problem Statement

The Hermes Agent system prompt injects **~3,900 skill entries** (name + description) into every conversation turn. This consumes an estimated **100,000-200,000 tokens per turn**, leaving 0-92K of usable context for actual work in a typical 128K-200K context window.

## Token Budget Analysis

| Component | Est. Tokens |
|-----------|-------------|
| Core system prompt (SOUL.md, rules, guidelines) | ~3,000 |
| **Available skills list (~3,900 entries)** | **~100,000-200,000** |
| AGENTS.md | ~1,500 |
| MEMORY.md + memory files | ~1,500 |
| Tool definitions (MCP, built-in, etc.) | ~2,000 |
| **Total system overhead** | **~108,000-208,000** |
| Typical context window | 128,000-200,000 |
| **Remaining for conversation** | **0-92,000** |

The skill registry is **50-100x larger** than all other context combined.

## Root Causes

1. **Flat injection:** Every skill name and description is injected equally, regardless of relevance to the current task.
2. **No tiering:** Local/installed skills (25) and remote/marketplace skills (3,875) are treated identically.
3. **Stale cache:** skill-selector cache has 1,441 entries vs. ~3,900 live entries. ~2,500 skills are invisible to the scorer.
4. **Redundancy:** Multiple overlapping skills (4 debugging, 5 planning, 3 code review, 5 memory, 2 skill-selector).
5. **No auto-firing:** skill-selector script runs manually, not as a per-turn hook.

## Recommended Solution: Tiered Injection

### Tier Architecture

| Tier | Content | Entries | Est. Tokens | Injection Method |
|------|---------|---------|-------------|-----------------|
| Tier 1 | Installed & verified local skills | ~25 | ~2,000 | Full descriptions in system prompt |
| Tier 2 | Relevant skill categories (summaries) | ~50-80 | ~3,000 | Category name + one-line summary |
| Tier 3 | Full catalog | ~3,800 | 0 (not injected) | On-demand via `skill_list` / `skill_view` tools |

**Projected savings:** ~95-195K tokens/turn (60-75% reduction of total system overhead).

### Why this works

- The LLM already has `skill_list()` and `skill_view()` tools for on-demand loading.
- In practice, only 2-5 skills are loaded per turn anyway (MAX_LOAD = 5).
- Tier 1 gives the agent full metadata for skills it actually has access to.
- Tier 2 provides awareness of available categories without the token cost.
- Tier 3 is already available via tools — no information loss.

### Implementation Path

**Phase A (immediate, low effort):**
- Edit `agent/prompt_builder.py` on the host to change skill injection from flat name+description list to category-only summary.
- Change `available_skills` block from `{"skill-name": "full description"}` to `{"category": "count + one-line summary"}`.
- Keep `skill_list` and `skill_view` tool access for on-demand loading.
- Estimated effort: 1-2 hours, single file change.

**Phase B (medium effort):**
- Rebuild skill-selector cache from full 3,900-entry catalog.
- Wire skill-selector as per-turn pre-hook (not manual invocation).
- Only auto-load top-5 relevant skills per turn.
- estimated effort: 4-8 hours.

**Phase C (longer term):**
- Enforce SKILL_SCHEMA frontmatter quality metadata on all skills.
- Deduplicate redundant skills (add `supersedes` field for conflict resolution).
- Add `deprecated: true` flag for outdated skills.
- Estimated effort: ongoing.

## Redundancy Analysis

Skills with significant overlap (candidates for deduplication via `supersedes`):

| Class | Overlapping Skills | Action |
|-------|-------------------|--------|
| Debugging | systematic-debugging, debug-mantra, debugging-hermes-tui-commands, diagnose | Merge into systematic-debugging |
| Planning | writing-plans, plan, blueprint, autonomous-development | Merge into writing-plans |
| Code review | structured-code-review, scrutinize, requesting-code-review | Merge into structured-code-review |
| Memory | hindsight, mnemo-hermes, hanfang-claude-memory-skill, flowstate-qmd | Keep hindsight + mnemo-hermes |
| Skill selection | skill-selector (root), skill-selector (software-development) | Keep software-development version |
| Reproducibility | repo-init, scaffold-exercises, write-a-skill | Distinct enough to keep |

## Additional Findings

1. **AGENTS.md references OpenClaw agents** (zoul, codi, etc.) instead of Hermes-native `delegate_task`. Should be updated for the current system.
2. **Heartbeat protocol (~80 lines)** in AGENTS.md should be extracted to HEARTBEAT.md to reduce system prompt size.
3. **System prompt has duplicate guidance** across AGENTS.md, SOUL.md, and skill-selector — overlapping "load skills before acting" instructions.

## Next Steps

1. Get approval for Phase A implementation.
2. Edit `prompt_builder.py` to inject category summaries instead of full descriptions.
3. Test token savings with a real session.
4. Rebuild skill-selector cache against full catalog.
5. Wire skill-selector as automatic pre-turn hook.