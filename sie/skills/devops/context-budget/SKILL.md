---
name: context-budget
description: Audit context window consumption across loaded skills, agents, and tools. Identifies bloat, redundant components, and produces token-savings recommendations.
origin: ECC (adapted for Hermes)
---

# Context Budget

Analyze token overhead across loaded components and surface actionable optimizations to reclaim context space.

## When to Activate

- Session performance feels sluggish or output quality degrades
- Recently added many skills
- Planning to add more skills and need to know if there's room
- Running a token audit on the skill system

## How It Works

### Phase 1: Inventory

For each loaded skill:
- Count lines and estimate tokens (words × 1.3)
- Flag files > 400 lines (heavy)
- Check for duplicate content between skills

### Phase 2: Classify

| Bucket | Criteria | Action |
|--------|----------|--------|
| **Always needed** | Referenced in memory, backs active workflow | Keep |
| **Sometimes needed** | Domain-specific, not always relevant | Load on-demand |
| **Rarely needed** | No usage, overlapping content | Remove or merge |

### Phase 3: Detect Issues

- **Bloated skills** — files > 400 lines inflate every session
- **Redundant skills** — duplicate content across skills
- **Over-subscription** — too many skills loaded at once
- **Context chain bloat** — verbose memory entries that should be concise

### Phase 4: Report

Produce a context budget report:
```
Total estimated overhead: ~XX,XXX tokens
Context model: [current model] ([window] window)
Effective available context: ~XXX,XXX tokens (XX%)

Top optimizations:
1. Remove/merge [skill] — saves ~X,XXX tokens
2. Condense [memory entry] — saves ~X,XXX tokens
3. Load [skill] on-demand instead of always — saves ~X,XXX tokens
```

## Hermes Adaptation

- Run the audit script: `python3 /opt/data/skills/devops/context-budget/scripts/audit.py`
- Reference baseline metrics in `references/baseline-2026-05-11.md` for trend comparison
- Use `skills_list` to see all loaded skills
- For skill consolidation: use `skill_manage(action='delete', absorbed_into='...')`
