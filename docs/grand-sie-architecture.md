# Grand SIE — Strategic Intelligence Engine

Extends the Self-Improvement Engine from *retrospective fix tracking* to *prospective strategic intelligence*. Three subsystems sit above the existing Coach/Player loop:

```
┌─────────────────────────────────────────────────────────────────────┐
│                       GRAND SIE (Strategic Layer)                    │
│                                                                       │
│  ┌────────────────┐  ┌────────────────────┐  ┌──────────────────────┐│
│  │ Opportunity    │  │ Requirements       │  │ Self-Audit           ││
│  │ Radar          │  │ Engine             │  │ Engine               ││
│  │ (Phase 1)      │  │ (Phase 2)          │  │ (Phase 1.5)          ││
│  │ weekly         │  │ on-demand          │  │ biweekly             ││
│  │                │  │                    │  │                       ││
│  │ outward: scan  │  │ how to build it    │  │ inward: scan our      ││
│  │ external world │  │ → spec → tasks     │  │ own system           ││
│  │ → what to build│  │ → Coach/Player     │  │ → what to automate   ││
│  └───────┬────────┘  └─────────┬──────────┘  └────────┬─────────────┘│
│          │                     │                        │             │
│          └──────────┬──────────┴────────────────────────┘             │
│                     │                                                 │
│            ┌────────▼────────┐                                       │
│            │ Strategic Brief │                                       │
│            │ (weekly output) │                                       │
│            └────────┬────────┘                                       │
└─────────────────────┼────────────────────────────────────────────────┘
                         │ feeds into
┌────────────────────────▼─────────────────────────────────────┐
│              Coach / Player Loop (unchanged)                   │
│  Executes specs from Requirements Engine, outputs verified    │
│  work, feeds learnings back to SIE Knowledge Store            │
└───────────────────────────────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│              SIE Knowledge Store (unchanged)                   │
│  ChromaDB, trajectories, DevKnowledge — indexed learnings     │
│  that Grand SIE queries during research synthesis             │
└───────────────────────────────────────────────────────────────┘
```

## Design Principles

1. **Read-world, not read-repo** — scan external signals, not internal TODOs
2. **Synthesis, not aggregation** — don't just list links; say what they *mean* for our work
3. **Bias toward action** — every signal gets a recommendation (build/watch/skip)
4. **Self-improving** — the Radar learns from past recommendations (was I right? was it worth it?)
5. **Token-efficient** — a brief is 3-5 paragraphs, not 30 pages. Enough to decide, not enough to drown.

---

## Phase 1: Opportunity Radar

### Schedule

- **Weekly** — Sundays 02:00 UTC (12:00 Sydney Sunday)
- Delivered to morning briefing or a dedicated channel

### Sources

| Source | Tooling | What It Catches |
|--------|---------|-----------------|
| **GitHub Trending** | `web_search` or `gh search repos --sort=stars --limit 10` per domain | New repos in poker/GTO, 3DCP, AI agents, game dev |
| **arXiv** | `arxiv` skill → specific categories + keyword filters | Academic papers relevant to our stack |
| **Competitor Activity** | `gh repo list <org>` or `web_search` for release notes | Major updates to Luyten, ICON, other poker tools |
| **HN / Product Hunt** | `web_search site:news.ycombinator.com OR site:producthunt.com poker GTO` | Product launches and community discussion |
| **NPM / PyPI** | `web_search` or curl for recent downloads | Relevant package ecosystem changes |

### Scan Strategy (per tick)

Each source scan follows the same pattern:

1. **Query** — run the search with time-bounded filters (last 7 days)
2. **Extract** — pull titles, descriptions, URLs
3. **Score** — relevance 1-5, novelty 1-5, actionability 1-5
4. **Filter** — discard anything < 7 combined score
5. **Synthesise** — write 1-2 sentences on what it means for our work

### Output: Strategic Brief

A Markdown document with sections:

```markdown
# Strategic Brief — 2026-07-05

## Signals This Week

### 🟢 Worth Building
- [Repo/tool name] — Relevance: 5/5, Novelty: 4/5
  One-line assessment. Why we should care. Suggested action.

### 🟡 Worth Watching
- [Paper/article] — Relevance: 3/5
  Why it might matter later. What trigger would elevate it.

### 🔴 Skip / Out of Scope
- [Competitor feature] — Not relevant because...

## Recommendation

Based on this week's signals, the highest-impact move is:
> **Build X** — here's why, and here's the minimum next step.

## Project Health
- gto-wizard-clone: [on track / stalled / needs attention]
- polytopia-clone: [on track / stalled / needs attention]
- New opportunity: [brief description, effort estimate]
```

### Implementation: `scripts/opportunity-radar.py`

Single Python script, no persistent state beyond what it reads:

```
/tmp/hermes-sync/scripts/
└── opportunity-radar.py      # Main script (~400 lines)
```

Structure:

```python
class OpportunityRadar:
    def __init__(self, keywords: dict[str, list[str]]):
        # keywords = {"poker": ["GTO", "solver", "poker"], ...}
        pass

    def scan_github_trending(self) -> list[Signal]: ...
    def scan_arxiv(self) -> list[Signal]: ...
    def scan_competitors(self) -> list[Signal]: ...
    def scan_hacker_news(self) -> list[Signal]: ...

    def score_and_filter(self, signals: list[Signal]) -> list[Signal]: ...
    def synthesize(self, signals: list[Signal]) -> StrategicBrief: ...
    def deliver(self, brief: StrategicBrief): ...
```

### Cron Job

```yaml
# Runs weekly
name: opportunity-radar
schedule: "0 2 * * 0"        # Sunday 02:00 UTC
script: scripts/opportunity-radar.py
no_agent: true                # Script output IS the message
deliver: morning-briefing     # or a dedicated channel
```

---

## Phase 1.5: Self-Audit Engine

The inward-facing complement to the Opportunity Radar. Where the Radar scans the external world for **what to build**, the Self-Audit scans our own operation for **what to automate, improve, or kill**.

### Schedule

- **Biweekly** — every 2nd Saturday 02:00 UTC

### Audits

| Audit | Data Source | What It Catches |
|-------|------------|-----------------|
| **Manual Patterns** | `state.db` → messages where role=user | Repeated Sean requests worth automating (47× "summarise state of wiz", 18× "not happy with changes") |
| **Coach Trends** | Project `.checkpoint.json` files | Sysmic rejection reasons recurring across projects |
| **Dead Skills** | `~/.hermes/skills/*/SKILL.md` mtime | Skills never loaded in 60+ days (candidates for deletion) |
| **Zombie Crons** | `~/.hermes/cron/output/*` mtime | Cron jobs with no useful output in 30+ days (candidates for pausing) |
| **System Health** | Aggregated from above + session DB | Session volume, cost trends, token usage, project health |

### Automation Fitness Scoring

Every repeated pattern gets scored against three rules (from automation best practices):

| Rule | How Measured |
|------|-------------|
| **Repetitive?** | Occurrence count in 60 days. ≥3 = candidate, ≥10 = strong candidate |
| **Stable inputs/outputs?** | Heuristic: does the output follow a pattern? Is it deterministic? |
| **Not messy/rare/personal?** | Heuristic: if human judgment involved >50% of the time, skip |

### Right-Size Recommendation

Not everything needs Coach/Player. The audit recommends the right tier:

| Tier | Hermes Equivalent | When |
|------|-------------------|------|
| Reusable prompt | Saved in AGENTS.md or a skill | < 3×/month, stable I/O |
| Template | checkpoint.json, verdict-schema.json | Structured output needed |
| Workflow automation | Cron job (no_agent: true) | Connects tools, no reasoning |
| AI Agent | Cron job (LLM-driven) | Needs light reasoning |
| Script | Python script on schedule | Deterministic processing |
| Full Coach/Player | Coach + Player loop | Code implementation only |

### Output: System Health & What to Automate

A Markdown brief with sections:
- **Automation Candidates** — ranked by frequency, with recommended tier
- **Sysmic Coach Trends** — recurring rejection reasons with project context
- **Dead Automation** — skills/crons ready for deletion or pausing
- **System Health** — session counts, cost, project status

### Implementation: `scripts/self-audit.py`

Single Python script, queries `state.db` directly (SQLite), no LLM needed.

```bash
python3 scripts/self-audit.py            # Full audit → deliver to Discord
python3 scripts/self-audit.py --dry-run  # Print to stdout
python3 scripts/self-audit.py --section patterns  # Single section
```

### Cron Job

```yaml
name: self-audit
schedule: "0 2 * * SAT/2"     # Every 2nd Saturday 02:00 UTC
script: scripts/self-audit.py
no_agent: true                 # Deterministic — no LLM needed
deliver: all                   # Discord + local
```

### Connection to DELEGATE-52 + CFS

The Self-Audit, DELEGATE-52, and Code Fidelity Score form a unified quality framework:

```
Self-Audit → identify what to automate
Right-size → prompt / template / workflow / agent / script
Coach/Player → execute
Code Fidelity Score → is the automation degrading?
Prune → kill what's no longer useful → back to Self-Audit
```

When CFS trends down and the Self-Audit flags the project as having sysmic Coach rejections, Grand SIE recommends a structural review — not a code fix, but a systematic redesign.

---

## Phase 2: Requirements Engine

### Trigger

- An Opportunity Radar signal scores ≥ 20 combined (5×5×5 cube)
- Manual: "we should build this, write a spec"

### Output

A structured requirement spec:

```json
{
  "project": "new-project-name",
  "strategic_rationale": "...",
  "reference_url": "...",
  "effort_estimate": "3-5 ticks",
  "priority": "high|medium|low",
  "tasks": [
    {"id": "task-001", "description": "...", "success_criteria": "..."}
  ],
  "decision": "BUILD|WATCH|SKIP"
}
```

### Implementation Path

1. Start as a Hermes agent call with the `delegate_task` toolset
2. If successful, harden into a script
3. If successful, integrate into the Roadmap Engine's Phase 1

---

## Integration Points

| Existing System | How Grand SIE Connects |
|----------------|------------------------|
| **Roadmap Engine** | Grand SIE's Strategic Brief becomes input to Phase 1 research |
| **Coach/Player Loop** | Requirements Engine feeds task specs directly into `.checkpoint.json` |
| **SIE Knowledge Store** | Grand SIE queries ChromaDB during synthesis (e.g., "have we seen this pattern before?") |
| **Morning Briefing** | Strategic Brief is a morning briefing section |
| **Skills** | When Grand SIE identifies a recurring research pattern, it authors a skill for it |

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| **Signal fatigue** (too many irrelevant signals) | Aggressive scoring filters; start with 3 sources, add more only if value proven |
| **Analysis paralysis** (never building because always researching) | Fixed time budget per scan (10 min max); "recommendation or nothing" hard gate |
| **Stale recommendations** (brief says something that's no longer true) | Brief has TTL of 7 days; if not acted on, it expires |
| **Token cost of research** | Use cheap models (big-pickle or owl-alpha) for the scan; only use smart models for synthesis |
