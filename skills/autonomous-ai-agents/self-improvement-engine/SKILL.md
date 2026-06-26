---
name: self-improvement-engine
description: "Use when: (1) Roadmap engine finishes a run and has learnings to process, (2) a capability gap is identified that needs a new skill, (3) errors recur 3+ times in learnings files, (4) a feature request in roadmap.json learnings has enough context to prototype. Scans learnings, ranks candidates, researches solutions, authors SKILL.md files."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [self-improvement, autonomous-improvement, learnings, skill-authoring, continuous-improvement]
    related_skills: [roadmap-engine, self-improvement, hermes-agent-skill-authoring]
---

# Self-Improvement Engine

A persistent loop that closes the gap between "logged a learning" and "built the skill."

## Overview

The self-improvement engine is the missing link in the self-improvement chain:

```
Error occurs -> Logged to .learnings/ERRORS.md

                    with self-improvement-engine

Error occurs -> Logged -> Scanner detects 3x repeat -> Skill author researches -> SKILL.md authored -> committed
```

It is a pipeline with three phases:
1. **Scan** — find high-value candidates from roadmap learnings + hermes-sync learnings files
2. **Research** — investigate the problem space via web + code analysis
3. **Author** — write a SKILL.md using skill_manage, then commit it

## When to Use

- Roadmap engine reports learnings after a run
- A capability gap is identified ("I cannot do X") that maps to a learnable skill
- ERR-* entries in .learnings/ have Status: pending and Reproducible: yes
- LRN-* entry has Recurrence-Count >= 3 and Pattern-Key set
- User says "you should learn to do X" or "save this as a skill"

## When NOT to Use

- One-off errors already fixed — no skill needed
- Complex features requiring significant architecture — file as GitHub issue instead
- Platform-specific knowledge that belongs in memory (user preferences, environment quirks)

## Architecture

```
hermes-sync/
├── scripts/
│   ├── self_improvement.py     <- Entry point
│   ├── learnings_scanner.py   <- Phase 1: Scan + rank
│   └── skill_author.py         <- Phase 2: Research + author
├── workspace/plans/
│   ├── skill_candidates.json   <- Scanner output
│   └── skill-research/         <- Research briefs
├── memory/.learnings/          <- Extended learnings
└── skills/autonomous-ai-agents/self-improvement-engine/SKILL.md
```

## Phase 1: Learnings Scanner

Scans four sources:

| Source | Priority Weight |
|--------|---------------|
| roadmap.json -> learnings[] | 1.0 |
| memory/.learnings/ERRORS.md | 0.9 |
| memory/.learnings/LEARNINGS.md | 0.7 |
| memory/.learnings/FEATURE_REQUESTS.md | 0.6 |

### Scoring Algorithm

```
skill_score = priority_weight * area_multiplier * recurrency_multiplier * recency_boost

priority_weight:   critical=40, high=30, medium=20, low=10
area_multiplier:   infra=1.3, tests=1.2, backend=1.1, frontend=1.0, docs=0.8, config=0.9
recurrency_multiplier: count>=5 -> 1.5, >=3 -> 1.2, >=2 -> 1.0, else 0.8
recency_boost:     <7 days -> 1.2, <30 days -> 1.0, else 0.8
```

### Promotion Rules

A candidate is **high_priority** when ANY:
- skill_score >= 50
- Recurrence-Count >= 3
- Priority critical/high AND area=infra

## Phase 2: Skill Author

For each high_priority candidate:

1. **Research** — web search + code analysis, writes research brief to `workspace/plans/skill-research/<id>.md`
2. **Author** — builds SKILL.md using skill_manage(action='create')
3. **Verify** — skill_view loads without error, no duplicate exists
4. **Commit** — git add + commit to hermes-sync with candidate ID in message

SKILL.md format follows hermes-agent-skill-authoring spec:
- YAML frontmatter: name, description <=1024 chars, version, author, license, metadata.hermes.{tags, related_skills}
- Body: # Title -> ## Overview -> ## When to Use -> body -> ## Common Pitfalls -> ## Verification Checklist

## Running

```bash
cd /opt/data/hermes-sync

# Full pipeline: scan -> research -> author -> commit -> push
python3 scripts/self_improvement.py

# Scan only (no authoring)
python3 scripts/self_improvement.py --scan-only

# Dry run (no commits)
python3 scripts/self_improvement.py --dry-run

# Target a specific candidate
python3 scripts/self_improvement.py ERR-20260429-001
```

## Cron Definition

```yaml
name: Self-Improvement Engine
schedule: "0 */48 * * *"    # Every 2 days at midnight Sydney
workdir: /opt/data/hermes-sync
repeat: forever
deliver: local
prompt: |
  Run the self-improvement engine.
  Execute: python3 scripts/self_improvement.py
  Report what skills were authored.
```

- **Script deleted 2026-05-08:** `scripts/self_improvement.py` was removed in an auto-sync cleanup. The `_run_self_improvement()` call in Phase 1 now prints `"Script not found, skipping"` and exits gracefully — improvement loop silently broken. **Restore from git commit `9e5982d`:**

  ```bash
  cd /opt/data/hermes-sync
  git checkout 9e5982d -- scripts/self_improvement.py
  ```

  After restore, verify with: `python3 scripts/self_improvement.py --scan-only`

## Integration with Roadmap Engine

Runs inside Phase 1 of roadmap_engine.py, after _scan_github_issues() and before _llm_planner_revision().

## Common Pitfalls

1. **Authoring skills for solved problems** — only if Status: pending and Reproducible: yes
2. **Duplicating existing skills** — check skills/ directory first
3. **Over-engineering** — a simple 10-line skill beats a complex 200-line one
4. **Forgetting to commit** — skill only persists if committed to hermes-sync
5. **Research without sources** — web search minimum 3 relevant URLs before authoring
6. **Wrong category** — match existing categories, don't invent new ones

## Quality Gates

Before authoring a skill, verify:
- [ ] Problem is solvable as a skill (not a full project)
- [ ] Solution is generalizable (not one-off fix)
- [ ] No existing skill covers the same trigger
- [ ] Hermes tools can actually solve the problem
- [ ] Research brief has real references (not just guesses)
- [ ] Skill follows hermes-agent-skill-authoring format
