# Coach-Agent Reference

The Coach validates player commits and generates backlog tasks. See `~/.hermes/skills/coach-agent/SKILL.md` for the full skill definition.

## Core Responsibilities

1. **Review**: Validate player commits against AGENTS.md task criteria
2. **Decide**: APPROVE, FIX, or REVERT with evidence
3. **Generate**: When tasks run low, investigate what's broken and add new tasks

## Key Principles

- **Fresh context**: Runs as a completely separate agent from the Player — no shared history
- **Evidence gates**: 8 mechanisms prevent rubber-stamping (requirements checklist, compile gate, test gate, edge case gate, security gate, approval sentinel, turn limit, fresh context)
- **Approval sentinel**: Verdict must start with `DECISION: APPROVE | FIX | REVERT`
- **Requirements anchoring**: Evaluate against AGENTS.md criteria, NOT the player's commit message

## Decision Framework

| Decision | Condition | Action |
|----------|-----------|--------|
| APPROVE | All criteria met, all checks pass | Update checkpoint, report |
| FIX | >90% met, minor issues only (≤20 lines) | Create corrective commit, approve |
| REVERT | Tests fail, structural issues, misrepresentation | `git revert`, restore checkpoint |

## Backlog Generation

When 0 tasks remain in AGENTS.md:

1. **Brainstorm**: Name 2-3 candidate gaps from review context
2. **Investigate**: Probe API health, proxy, endpoints, DB, deploy log, browser
3. **Score**: Use `blocking_weight × confidence` formula
4. **Generate**: 3-5 tasks with success criteria and coach checks
5. **Commit**: Append to AGENTS.md, update checkpoint, push

## Scoring Model

| Factor | Weight |
|--------|--------|
| Blocking | 3.0× |
| User-facing | 2.0× |
| Infra gap | 1.5× |
| Polish | 1.0× |

See `docs/scoring-model.md` for details and worked examples.

## Composing with Other Skills

| Skill | When |
|-------|------|
| `parallel-investigation` | Probing 3+ endpoints simultaneously |
| `software-development/writing-plans` | Task granularity (2-5 min each) |
| `self-improvement-engine` | Scoring/ranking gaps |
| `planning/blueprint` | Decomposing large gaps into substeps |
| `planning/product-lens` | Validating "why" for product gaps |
