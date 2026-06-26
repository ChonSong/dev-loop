# Skills-First Investigation — Methodology

From session 2026-06-16. When asked to solve a dev-loop problem, the
correct first step is to investigate existing skills for reusable
patterns, not to propose a solution from scratch.

## Trigger

User asks: "how should we fix X" or "design Y for the dev loop" or
"what skills should we use for Z". Any architectural/process question
about the autonomous development system.

## Investigation Workflow

### Phase 1: Identify Candidate Skills

Run `skills_list()` on the categories most likely to contain relevant
patterns. For dev-loop questions, these are usually:

- `autonomous-ai-agents` — self-improvement-engine, roadmap-engine,
    parallel-investigation
- `planning` — blueprint, product-lens
- `software-development` — writing-plans, spec-audit, development-
    communication, scrutinize
- `devops` — phased-project-runner, doc-driven-dev-loop
- `quality` — adversarial-commitment-audit

Target 6-10 skills for investigation.

### Phase 2: Extract Patterns from Each

For each skill, `skill_view()` the full content. Extract:

| Skill Name | Key Pattern | What to Borrow | Trigger for Using |
|------------|-------------|----------------|-------------------|
| `self-improvement-engine` | Scoring algorithm (weight × frequency) | Adapt to backlog gap prioritisation | Ranking competing candidate tasks |
| `planning/blueprint` | Design tree walk | One decision per exchange, foundation first | Ambiguous task requirements |
| `writing-plans` | 2-5 min task granularity | Each task = one atomic action | Task is too large for one tick |
| `parallel-investigation` | Spawn subagents per dimension | Probe API, DB, browser simultaneously | >3 endpoints to check |

### Phase 3: Assess Coverage

For each pattern, ask:

1. Does an existing skill already cover this? → Use it directly
2. Does an existing skill cover most of it but needs a minor extension? → Patch it
3. Does NO existing skill cover it? → Create new class-level skill

### Phase 4: Propose

Present findings as a table (what exists, what needs extending, what's
missing). Then propose the solution — it should compose existing skills
with minimal new surface.

## Example

From the backlog curation design (2026-06-16):

| Skill | Pattern Used | How Adapted |
|-------|-------------|-------------|
| `self-improvement-engine` | Scoring formula | `blocking_weight × confidence` for gap prioritisation |
| `planning/blueprint` | Brainstorm before investigating | Name 2-3 candidates before running probes |
| `writing-plans` | 2-5 min granularity | Task size pre-check before starting implementation |
| `parallel-investigation` | Multi-probe parallelism | Spawn subagents for >3 endpoints |
| `product-lens` | ICE scoring | Simplified to blocking×confidence |
| `coach-agent` (evidence gates) | Fresh context (#8) | Coach is right owner because it runs with no shared history |
| `adversarial-commitment-audit` | Verify don't trust | Coach probes live system, doesn't trust checkpoint health field |

Solution: Extended coach-agent with backlog health check. Minimal change
— no new cron job, no new skill.
