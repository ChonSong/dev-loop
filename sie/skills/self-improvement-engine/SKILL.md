---
name: self-improvement-engine
description: "Use when: (1) Roadmap engine finishes a run and has learnings to process, (2) a capability gap is identified that needs a new skill, (3) errors recur 3+ times in learnings files, (4) a feature request in roadmap.json learnings has enough context to prototype. Scans learnings, ranks candidates, researches solutions, authors SKILL.md files."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [self-improvement, autonomous-improvement, learnings, skill-authoring, continuous-improvement]
    related_skills: [roadmap-engine, hermes-agent-skill-authoring]
---

# Self-Improvement Engine

A persistent loop that closes the gap between "logged a learning" and "built the skill."

## Overview

```
Error occurs → Logged → Scanner detects 3x repeat → Skill author researches → SKILL.md authored
```

Pipeline phases:
1. **Scan** — find high-value candidates from 4 sources (roadmap.json, ERRORS.md, LEARNINGS.md, FEATURE_REQUESTS.md)
2. **Research** — investigate the problem, write brief
3. **Author** — write a SKILL.md (dry-run to workspace/plans/authored/)

## When to Use

- Roadmap engine reports learnings after a run
- A capability gap is identified that maps to a learnable skill
- ERR-* entries have Status: pending and Reproducible: yes
- LRN-* entry has Recurrence-Count >= 3 and Pattern-Key set
- User says 'save this as a skill'

## When NOT to Use

- One-off errors already fixed — no skill needed
- Complex features requiring significant architecture — file as GitHub issue instead
- Platform-specific knowledge that belongs in memory (user preferences, environment quirks)

## Scripts

All at `/tmp/hermes-sync/scripts/`:

| Script | Lines | Role |
|--------|-------|------|
| self_improvement.py | ~120 | Orchestrator: runs scanner → author pipeline |
| learnings_scanner.py | ~380 | Scans 4 sources, scores candidates, writes skill_candidates.json |
| skill_author.py | ~325 | Reads high-priority candidates, authors SKILL.md (dry-run) |

Supporting files:
- `/tmp/hermes-sync/workspace/plans/skill_candidates.json` — scanner output
- `/tmp/hermes-sync/workspace/plans/skill-research/` — research briefs
- `/tmp/hermes-sync/workspace/plans/authored/` — dry-run skill output

## Scoring Algorithm

```
skill_score = priority_weight × area_multiplier × recurrency_multiplier × recency_boost
```

| Signal | Effect |
|--------|--------|
| priority=critical → 40 | high=30 | medium=20 | low=10 |
| area=infra → ×1.3 | tests→×1.2 | backend→×1.1 | frontend→×1.0 | docs→×0.8 |
| recurrence ≥5 → ×1.5 | ≥3 → ×1.2 | ≥2 → ×1.0 | else → ×0.8 |
| age <7 days → ×1.2 | <30 days → ×1.0 | else → ×0.8 |

**High-priority** (triggers authoring): score ≥ 50 OR recurrence ≥ 3 OR (critical/high priority + infra area)

## Usage

```bash
cd /tmp/hermes-sync

# Full pipeline: scan → research → author (dry-run)
python3 scripts/self_improvement.py

# Scan only (no authoring)
python3 scripts/self_improvement.py --scan-only

# Dry run (save to workspace/plans/authored/ for review)
python3 scripts/self_improvement.py --dry-run

# Target a specific candidate
python3 scripts/self_improvement.py --dry-run lrn-001
```

## Recovery Notes

The original scripts were deleted when /opt/data/hermes-sync was lost. Rebuilt from this skill's architecture docs June 2026. If lost again, re-create from the scoring algorithm and pipeline spec above. Git-init /tmp/hermes-sync/ and push to backup to prevent re-loss.

## Integration with Roadmap Engine

Roadmap engine Phase 1 calls self_improvement.py via subprocess. The `_run_self_improvement()` hook in roadmap_engine.py runs the scanner and reports results.

## Cron Definition

```yaml
name: Self-Improvement Engine
schedule: "0 */48 * * *"    # Every 2 days
workdir: /tmp/hermes-sync
repeat: forever
deliver: local
prompt: |
  Run the self-improvement engine.
  Execute: python3 scripts/self_improvement.py
  Report what skills were authored.
```

## Common Pitfalls

1. Authoring skills for solved problems — only if Reproducible: yes
2. Duplicating existing skills — check skills/ directory first
3. Over-engineering — a simple 10-line skill beats a complex 200-line one
4. Scripts on /tmp are ephemeral — lost on container restart. Git-init + push to backup.
5. skill_author.py is dry-run only — saves to workspace/plans/authored/ for review
6. Wrong category — match existing categories, don't invent new ones

## Quality Gates

Before finalizing an authored skill, verify:
- [ ] Problem is solvable as a skill (not a full project)
- [ ] Solution is generalizable (not one-off fix)
- [ ] No existing skill covers the same trigger
- [ ] Skill follows hermes-agent-skill-authoring format
