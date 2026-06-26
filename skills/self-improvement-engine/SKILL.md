---
name: self-improvement-engine
description: "Use when: (1) Roadmap engine finishes a run and has learnings to process, (2) a capability gap is identified that needs a new skill, (3) errors recur 3+ times in learnings files, (4) a feature request in roadmap.json learnings has enough context to prototype. Scans learnings, ranks candidates, researches solutions, authors SKILL.md files. Also runs Phases 0: proactive coverage blind-spot scan."
version: 1.3.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [self-improvement, autonomous-improvement, learnings, skill-authoring, continuous-improvement, rsi, meta-loop, coverage-audit]
    related_skills: [roadmap-engine, self-improvement, hermes-agent-skill-authoring, code-quality-audit, dashboard-development, coach-agent]
---

# Self-Improvement Engine

A persistent loop that closes the gap between "logged a learning" and "built the skill."
**Phase 0 (added 2026-06-22)** makes it proactive: it discovers coverage blind spots across all autonomous loops before processing reactive learnings.

## Overview

The self-improvement engine is the missing link in the self-improvement chain:

```
Without SIE:
  Error occurs -> Logged to .learnings/ERRORS.md -> Nobody reads it -> Same error repeats

With SIE (was):
  Error occurs -> Logged -> Scanner detects 3x repeat -> Skill author researches -> SKILL.md authored -> committed

With SIE (now):
  [Phase 0] Blind-spot scan discovers what audits DON'T check -> Seeds .learnings/ entries proactively
  [Phases 1-4] Process ALL .learnings/ entries (reactive + proactive) -> Skills authored
```

It is a pipeline with five phases:
0. **Proactive Coverage Scan** — discover what the system is NOT checking across all projects
1. **Scan** — find high-value candidates from roadmap learnings + hermes-sync learnings files
2. **Research** — investigate the problem space via web + code analysis
3. **Author** — write a SKILL.md using skill_manage, then commit it
4. **Push** — commit and push to origin

## When to Use

- Roadmap engine reports learnings after a run
- A capability gap is identified ("I cannot do X") that maps to a learnable skill
- ERR-* entries in .learnings/ have Status: pending and Reproducible: yes
- LRN-* entry has Recurrence-Count >= 3 and Pattern-Key set
- User says "you should learn to do X" or "save this as a skill"
- **A new project is added to the master checkpoint** — the coverage scan will discover if it has oversight
- **An audit has been running silently for weeks** — Phase 0 checks if it's checking what it should
- **Coach-agent reports FIX/REVERT verdict with cross-project pattern** — the Coach seeds a .learnings/ entry to LEARNINGS.md; SIE scans it in Phase 1 and promotes if Recurrence-Count >= 3

## When NOT to Use

- One-off errors already fixed — no skill needed
- Complex features requiring significant architecture — file as GitHub issue instead
- Platform-specific knowledge that belongs in memory (user preferences, environment quirks)

## Architecture

```
hermes-sync/
├── scripts/
│   ├── self_improvement.py     <- Entry point (Phases 1-4)
│   ├── learnings_scanner.py   <- Phase 1: Scan + rank
│   └── skill_author.py         <- Phase 2: Research + author
├── workspace/plans/
│   ├── skill_candidates.json   <- Scanner output
│   ├── skill-research/         <- Research briefs
│   └── roadmap.json (optional) <- Roadmap-engine learnings source
├── memory/.learnings/          <- Extended learnings (LEARNINGS.md, ERRORS.md, FEATURE_REQUESTS.md)
└── skills/                     <- Authored skills land here
```

Phase 0 runs **before** the Python pipeline — it's an LLM-driven scan using the file+terminal toolsets. It does not require code changes.

## Phase 0: Proactive Coverage Blind-Spot Scan (LLM-driven)

This is the RSI meta-problem fix. Added 2026-06-22 after LRN-010 revealed that the autonomous HWC Health Audit had been running for months without ever checking code quality — finding 11 bugs (2 P0) that deployment checks can't catch.

Phase 0 has two sub-phases that run sequentially:

### Phase 0a: Project Coverage Scan

Scans all projects in the master checkpoint for oversight gaps.

### Phase 0b: Skill Hygiene Audit 

Scans cron-loaded skill files for content bloat — prevents the monotonic growth that makes skills slow and expensive.

### Why This Phase Exists

The SIE was purely reactive — it only processed .learnings/ entries that a human or Coach manually seeded. The Coach now systematically seeds learnings entries as part of its review protocol (on FIX/REVERT verdicts with recurring patterns across projects — see coach-agent SKILL.md Learnings Feedback section). But Phase 0 addresses a deeper gap: blind spots that no single review would catch — projects with no audit, deployment-only checks missing code quality, stale oversight. Without Phase 0, those gaps never produce a learning entry at all.

### What It Checks

Reads /home/sc/.hermes/master-checkpoint.json to discover all projects, then for each project:

When the cron job's `enabled_toolsets` includes `"delegation"` (as configured since 2026-06-23), spawn one subagent per project to audit coverage in parallel. Each subagent reads the project's audit outputs independently — no shared state. Collate gaps from all subagents, deduplicate, then seed .learnings/ entries for each unique gap found. When delegation is unavailable, scan projects serially within the 48h budget (serial is fine — this is a generous cycle).

| Check | Reads | Flags If |
|-------|-------|----------|
| Health audit exists? | ~/.hermes/cron/output/ job outputs | No audit at all (uncovered) |
| Audit checks code quality? | Last 2 outputs + code-quality-audit skill | Deployment-only (LRN-010 pattern) |
| **E2E test infrastructure exists?** | **`apps/web/e2e/*.spec.ts` or `e2e/*.spec.ts` in project repo** | **No browser/E2E tests at all** |
| **E2E tests pass?** | **`cd apps/web && npm run test:e2e 2>&1` (if e2e dir exists)** | **Tests fail or broken selectors** |
| **POM selector freshness?** | **Compare catalog snapshot element count vs live DOM** | **>20% element drift since last catalog** |
| Last review freshness | Checkpoint last_review timestamp | >7d stale (active) or >30d (complete) |
| Dashboard manifest exists? | DASHBOARD.md in workspace root | No dashboard for a pipeline/project |
| Dashboard data sources covered? | DASHBOARD.md RSI Coverage table | Marked 🔴 items not yet wired |

### Phase 0b: Skill Hygiene Audit

Prevents skill file bloat by tracking size and structure of cron-loaded skills, flagging when they grow without corresponding pruning.

#### Which Skills Are Checked

All skills loaded by cron jobs. Discover by listing cron jobs and checking their `skills` field:
```bash
cronjob action=list | grep -E '"skills":\s*\[' | grep -oE '"[a-z_-]+"' | sort -u
```

Currently tracked: `player-agent`, `coach-agent`, and any skill referenced in a cron job's `skills[]` array.

#### Checks

| Check | Reads | Flags If |
|-------|-------|----------|
| Size delta | `workspace/plans/skill-hygiene-state.json` (previous audit) vs current file | Lines grew >15% OR bytes grew >20% since last audit |
| Rare-use section ratio | Content scan — identify sections >30 lines that are safety valves, recovery protocols, or fallback diagnostics | A section >30 lines exists that the skill itself describes as "rare" or "safety valve" or "only when" |
| Inline vs reference balance | Count lines of inline detailed procedures vs reference-linked content | A detailed procedure (>40 lines) has no corresponding reference file it could be moved to |
| Section age | git log for last modification date of the skill file | No structural review (section count change) in >30 days |
| **Compensation loop detection** | Compare rule-to-output ratio: count explicit behavioral rules (\"MANDATORY\", \"HARD RULE\", \"DO NOT\", \"ALWAYS\", \"NEVER\", explicit prohibitions) in the skill vs avg tool calls or output length in the last 3 cron sessions | Rule count / output length ratio >0.5 (more than 1 rule per ~2 tool calls) OR >15 rules added since last audit without corresponding pruning |

#### State File

Persisted at `workspace/plans/skill-hygiene-state.json`:

See `references/autonomous-ai-agents-self-improvement-engine-code_block-0.md` for the full code_block.

Update this file each run so subsequent audits can compute deltas.

#### Seeding Protocol

For each hygiene issue found, append to LEARNINGS.md:

| Condition | Priority | Pattern-Key | Example |
|-----------|----------|-------------|---------|
| Lines grew >15% | medium | `skill-content-bloat` | `player-agent grew 22% since last audit (192→234 lines)` |
| Rare-use section >30 lines inline | medium | `skill-section-not-in-reference` | `Task Exhaustion Recovery is 72 lines but a safety valve — no reference pointer` |
| No structural review >30d | low | `skill-review-stale` | `coach-agent hasn't been structurally reviewed in 45 days` |
| **Rule-to-output ratio >0.5** | **high** | **`compensation-loop-active`** | **`coach-agent: 22 behavioral rules for avg 14 tool calls/session — compensation loop active`** |
| **>15 rules added without pruning since last audit** | **medium** | **`compensation-loop-growth`** | **`player-agent: 18 rules added since last audit, 0 pruned — skill is accumulating, not refining`** |

Each entry uses Recurrence-Count: 1 (incremented by Phase 1 scanner if same pattern detected next run).

### Seeding Protocol

For each gap found, appends a new LRN-### entry to LEARNINGS.md with:
- Pattern-Key matching the gap type (so recurrence detection works)
- Priority based on severity (uncovered=high, deployment-only=high, stale=medium)
- Recurrence-Count: 1 (increments on subsequent detections via the scanner)

### Output

Reports: how many projects scanned, how many gaps found, each gap with project name and what was missing.

## Phase 1: Learnings Scanner

Scans four sources:

| Source | Priority Weight |
|--------|---------------|
| roadmap.json -> learnings[] | 1.0 |
| memory/.learnings/ERRORS.md | 0.9 |
| memory/.learnings/LEARNINGS.md | 0.7 |
| memory/.learnings/FEATURE_REQUESTS.md | 0.6 |

Also picks up any entries seeded by Phase 0 or the Coach-agent's learnings feedback (cross-project FIX/REVERT patterns) — they enter the same scoring pipeline.

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
cd /home/sc/repos/hermes-sync

# Full pipeline: Phase 0 -> scan -> research -> author -> commit -> push
# (Phase 0 runs as LLM-driven step before the Python pipeline)
python3 scripts/self_improvement.py

# Scan only (no authoring)
python3 scripts/self_improvement.py --scan-only

# Dry run (no commits)
python3 scripts/self_improvement.py --dry-run

# Target a specific candidate
python3 scripts/self_improvement.py --candidate LRN-001-web-search
```

## Cron Definition

```bash
# Created via cronjob tool (job_id: 83e9c3a48cff)
name: Self-Improvement Engine
schedule: "0 */48 * * *"      # Every 48 hours
workdir: /home/sc/repos/hermes-sync
deliver: local
enabled_toolsets: [terminal, file, delegation]

# Phase 0a: Project coverage blind-spot scan (parallelized via delegate_task — one subagent per project).
# Phase 0b: Skill hygiene audit — measure cron-loaded skills, detect bloat, seed learnings.
# Phases 1-4: Python pipeline runs after.
```

## Integration with Roadmap Engine

Runs inside Phase 1 of roadmap_engine.py, after _scan_github_issues() and before _llm_planner_revision().

## References

- `references/rsi-capability-bottlenecks.md` — Research on what limits autonomous self-improvement: academic papers, Anthropic RSI data, and cross-reference against Hermes architecture (capability bottlenecks, not just safety). Key for Phase 2 research when the topic involves RSI theory or scaling constraints.
- `references/pipeline-troubleshooting.md` — Bugs found and fixed during restoration from git (regex drift, timezone-naive datetime, syntax errors). Read this first if the pipeline produces 0 candidates or crashes.
- `references/rsi-research-capability-bottlenecks.md` — Detailed research on what actually limits RSI in practice, including cron reliability, web tool fallback chains, vision vs web independence, and feedback loop failure modes.
- `references/coach-player-loop-failure-detection.md` — Detection pattern for when the autonomous dev loop's feedback mechanisms stall (Coach/Player cron errors, vision tool failures, backlog exhaustion). Add learnings entries when this pattern is observed.

## Common Pitfalls

1. **Phase 0 may find no gaps on the first run if projects are well-covered** — that's a success, not a bug. It means the system has good coverage.
2. **Do NOT run Phase 0 if the master checkpoint is unavailable** — skip Phase 0 and fall back to Phases 1-4.
3. **Phase 0 creates learnings entries but does NOT auto-author skills** — that requires Recurrence-Count >= 3, which only happens if the same gap persists across multiple scans.
4. **Skill Hygiene Audit needs a baseline** — the first run after implementing Phase 0b won't have a state file to compare against. Create the initial state file manually at `workspace/plans/skill-hygiene-state.json` with current measurements. The audit seeds a "baseline created" entry rather than a bloat flag on first run.
5. **Phase 0b only checks cron-loaded skills** — skills loaded on-demand (like hermes-agent at 1,371 lines) aren't checked because they don't burn tokens every tick. If on-demand skills need pruning, run a separate manual audit.
6. **Authoring skills for solved problems** — only if Status: pending and Reproducible: yes
7. **Duplicating existing skills** — check skills/ directory first
8. **Over-engineering** — a simple 10-line skill beats a complex 200-line one
9. **Forgetting to commit** — skill only persists if committed to hermes-sync
10. **Research without sources** — web search minimum 3 relevant URLs before authoring
11. **Wrong category** — match existing categories, don't invent new ones

## Quality Gates

Before authoring a skill, verify:
- [ ] Problem is solvable as a skill (not a full project)
- [ ] Solution is generalizable (not one-off fix)
- [ ] No existing skill covers the same trigger
- [ ] Hermes tools can actually solve the problem
- [ ] Research brief has real references (not just guesses)
- [ ] Skill follows hermes-agent-skill-authoring format
- [ ] If adding to an existing skill, check if any existing section can be moved to reference to offset the growth (no net bloat)
