---
name: seans-reporepo-query
description: Structured 4-phase discovery-to-build methodology using the 201-repo catalog. Not a search tool — a decision framework for finding, evaluating, and combining repos into real projects.
category: software-development
---

# Repo Discovery & Combinatorial Design

A structured methodology for turning the seans-reporepo catalog (201 repos, 67 tags) into buildable project ideas. This is NOT a search tool — it's a decision framework.

## The Four Phases

```
Frame Problem → Deep Discovery → Pattern Match → Feasibility → Decision
  (Phase 0)      (Phase 1)       (Phase 2)       (Phase 3)     (Phase 4)
```

---

## Phase 0: Frame the Problem

Before opening the catalog, answer:

1. **What capability do I lack?** (not "what repo should I use" — what can't I do today?)
2. **What data/event/service would unlock that?**
3. **What's the minimum version of success?** (one working integration vs a platform)
4. **What are my constraints?** (8GB RAM, no sudo, single-user, Python/Go/TS stack, Docker available)

**Output:** A one-paragraph problem statement. Example:
> "I want Discord push alerts when any systemd service on the host fails, without adding another database or paying for a SaaS."

---

## Phase 1: Deep Discovery

Not tag grep. Read the actual repo descriptions and code.

### Step 1: Identify Capability Candidates

For each problem domain, search the catalog for repos whose DESCRIPTIONS mention related capabilities:

```
search_files(path='/home/sc/repos/seans-reporepo', pattern='monitoring|alert|notification|health', target='content', file_glob='*.md')
```

Read each match's full markdown file — the frontmatter description tells you what it ACTUALLY does, not just its tags.

### Step 2: Map Capabilities to Owned Repos

For each candidate, ask:
- **Do we already own something like this?** Check the owned/ directory for overlap.
- **Is this a complement or a replacement?** (Complement = integrates with existing. Replacement = would require migration.)
- **What's the integration surface?** (API? Library import? CLI pipeline? Docker compose? MCP tool?)

### Step 3: Read the Actual Source (not just the readme)

When a candidate looks promising, validate:

```
# What language is it? Does it fit our stack?
grep "language:" /home/sc/repos/seans-reporepo/starred/<name>.md

# How many stars? Is it maintained?
grep "stars:" /home/sc/repos/seans-reporepo/starred/<name>.md

# What does the description actually promise?
grep "description:" /home/sc/repos/seans-reporepo/starred/<name>.md
```

For top candidates, visit the actual GitHub repo to check:
- Recent commits (active in last 6 months?)
- Issue tracker (responsive maintainer?)
- Dependencies (what does it pull in?)

### Step 4: Build a Capability Map

Organize findings into a map:

| Need | Candidate(s) | Owned Alternative | Integration Surface | Fit |
|---|---|---|---|---|
| System alerting | netdata (79K⭐) | circuit-breaker-framework | Docker compose + webhook | High |
| LLM tracing | langfuse (29K⭐) | hermes-telemetry | OpenTelemetry + HTTP | Low (too heavy) |
| ... | ... | ... | ... | ... |

---

## Phase 2: Pattern Matching

This is where combinations emerge. Look for four patterns:

### Pattern A: Complementarity

**Repo A's output is Repo B's input.**

Example: `netdata` emits alerts → `Discord` (already connected) displays them.
Status: ✅ Built (Netdata → Discord webhook, working)

Another: `promptfoo` → outputs JSON results → `llm-benchmark-platform` could ingest and display over time.
Status: 🔲 Not built — 30min integration.

### Pattern B: Gap Filling

**A starred repo provides a capability none of the owned repos have.**

Example: `context7` (57K⭐) provides live code documentation. No owned repo does this.
Status: ✅ Connected as MCP tool, usage skill created.

Another: `temporalio/temporal` (21K⭐) provides durable workflow execution. The current checkpoint-based system is a poor substitute.
Status: 🔲 Not built — overkill for 8GB VM, but worth watching.

### Pattern C: Platform Play

**One integration unlocks many downstream uses.**

Example: `yt-dlp` (169K⭐) can extract audio from any URL. Once integrated:
- Voice command → yt-dlp → transcribe → summarize → Discord
- Scheduled podcast ripper → LLM digest
- Video search index for research

Status: 🔲 Not built — all components exist but integration glue needed.

### Pattern D: Consolidation

**Two owned repos do similar things — merge or delete one.**

Example: `seans-reporepo` + old `seans` repo. `seans-reporepo` won. Delete `seans`.
Status: ✅ Done (during June 14 cleanup).

Another: `hermes-telemetry` (owned, 198-line server) overlaps with Netdata's capabilities. `hermes-telemetry` is narrower but lighter.
Status: 🟡 Keep both — Netdata for system, hermes-telemetry for agent-specific metrics if needed later.

---

## Phase 3: Feasibility Assessment

For each candidate combination, evaluate:

### Effort
| Level | Definition | Examples |
|---|---|---|
| Quick (<30min) | Docker compose addition, config change, existing tool | Netdata deploy, logrotate config |
| Small (<2h) | New config, CI pipeline, basic integration | promptfoo CI, Discord webhook |
| Medium (<1d) | New service, moderate glue code | Context7 MCP setup |
| Large (<1w) | New application, significant integration | Voice research pipeline |
| X-Large | Platform rebuild, architecture change | Temporal migration, dev-loop-v2 |

### Dependencies
- Does it need a new Docker container? (RAM budget: 8GB total, ~3GB used)
- Does it need a new API key? (Do we have one?)
- Does it need a database? (Postgres running, Redis running)
- Does it need sudo? (Not available — user-level installs or Docker only)

### Risk
- Maintenance burden (will this need updates?)
- Single point of failure (does everything break if this goes down?)
- Data loss risk (does it handle state?)
- Security surface (does it open ports? need auth?)

### Scoring Matrix

Score each candidate 1-5 on each axis:

| Criteria | Weight | netdata | context7 | dev-loop-v2 | voice pipeline |
|---|---|---|---|---|---|
| Effort (1=hard, 5=easy) | 1x | 5 | 4 | 2 | 1 |
| Value (1=low, 5=high) | 3x | 4 | 4 | 5 | 3 |
| Risk (1=high, 5=low) | 2x | 5 | 5 | 4 | 3 |
| Dependencies (1=many, 5=none) | 1x | 4 | 5 | 5 | 3 |
| **Weighted Score** | | **31** | **31** | **31** | **23** |

> `weighted = (5-effort)×1 + value×3 + risk×2 + (5-deps)×1`

---

## Phase 4: Decision

Based on the feasibility assessment, classify each candidate. **Then route to execution.**

### Routing Rules: Direct vs Queue

After Phase 4 classification, decide HOW to execute:

| If task is | Route | Action |
|------------|-------|--------|
| A script, one-shot command, or config change (<1 file, <5 min) | **Direct** | Execute with terminal()/write_file now. Report result. |
| A multi-step build, new feature, or anything needing commits | **Queue for player-agent** | Create project at /home/sc/repos/<project-name>/ with AGENTS.md + .checkpoint.json. Register in master checkpoint. |
| A cron job (recurring task) | **Cron job** | Use cronjob(action='create') with appropriate schedule and skill loading. |
| User says "do it autonomously" / "queue this" / "have x done" | **Queue** | Do NOT execute directly. Set up the dev loop infrastructure. |

**Key distinction**: When the user says "do it autonomously" or "place in queue", they mean set up the autonomous system to handle it — not execute it yourself. The autonomous executors are the player-agent (for builds), coach-agent (for reviews), and cron jobs (for recurring tasks). Your job is to create the project structure, checkpoint, and tasks — then let the loop run.

**How to queue for player-agent:**
1. Create /home/sc/repos/<project-name>/AGENTS.md with task descriptions (each task = one 2-5 min player tick)
2. Create /home/sc/repos/<project-name>/.checkpoint.json with current_task set to the first task
3. Register in /home/sc/.hermes/master-checkpoint.json with priority > 1 (lower = higher priority)
4. Optionally git init && git add -A && git commit -m "chore: init queue project"
5. Done — the player-agent cron picks it up on its next 30-min tick

### Build Now (Direct or Queued)
Quick wins already delivered from this process:
- ✅ Netdata + Discord alerts (Phase 1→2→3 in 20min)
- ✅ promptfoo CI eval (Phase 1→2→3 in 2h)
- ✅ seans-reporepo-query methodology (this skill)
- ✅ dev-loop-v2 Player + Coach (Phase 2→3→4 in 4h)
- ✅ Context7 MCP usage skill (Phase 1→2→3 in 15min)

### Build Later
- Voice research pipeline (all components exist, needs integration glue — 3-5d)
- Temporal evaluation (watch until dev-loop-v2 outgrows checkpoint pattern)
- Eval dashboard (promptfoo results → llm-benchmark-platform frontend — 30min integration)

### Don't Build
- langfuse/opik self-hosted (too heavy for 8GB VM — 6-8 containers, 3GB RAM)
- Prometheus+Grafana stack (Netdata does it in 1 container)
- Another agent framework (Hermes IS the framework)

### Watch
- google/adk-python (20K⭐ — if Hermes ever needs a multi-agent upgrade path)
- Temporal (21K⭐ — durable execution when cron + checkpoint isn't enough)
- karpathy/autoresearch (86K⭐ — time-budget pattern already borrowed for dev-loop-v2)

---

## Workflow: Full Discovery Cycle

When asked "find something useful from the catalog", DO NOT jump to tag search. Run the full cycle:

```
1. PHASE 0: What capability are we looking for? (or just "surprise me")
2. PHASE 1: Scan the README tag index and combinatorial potential sections for promising clusters
3. PHASE 1: Read 3-5 repo files from promising clusters — real descriptions, not just tags
4. PHASE 2: Look for complementarity, gaps, platform plays, consolidation opportunities
5. PHASE 3: Score each candidate (effort, value, risk, dependencies)
6. PHASE 4: Classify (build now / later / never / watch)
7. Output a structured recommendation with the scoring matrix
```

> If the user says "surprise me" or "what should I build next", run Phase 1 on a random under-explored tag cluster (research, voice, monitoring, testing all still have untapped potential).

## Pitfalls

### The Tooling Trap

The most common failure mode of this methodology: **identifying useful integrations but never building applications.** Every pattern match (complementarity, gap filling, platform play) should produce an answer to the question: "What APPLICATION does this enable? Who uses it?"

Signs you're in the tooling trap:
- You install and configure tools but have no user-facing UI
- The output is "I can now do X" rather than "User Y can now accomplish Z"
- Every discovery produces more cron jobs, more config files, more infrastructure
- You can describe the architecture but can't show it to anyone

**Correction:** After Phase 4 Decision ("build now"), immediately define:
- The application name (e.g. "Hermes System Console" not "health metrics API")
- The primary user (e.g. "Sean on Discord")
- The frontend interface (e.g. "Svelte 5 dashboard at :3030")

Then add it to the Player backlog as a phased build. The methodology is complete only when a user can interact with the result.

### Scope Creep Through Phase 4

**Building "now" does not mean building everything.** Pass through Phase 4 twice: once to identify (five builds in the backlog), once for YOUR NEXT TICK. Pick ONE. The Player does one task per 2h tick. If your Phase 4 list has 5 items, you need to pick which one actually gets built next.

### The Direct Execution Trap

**Most common failure mode when the user says "do it autonomously" or "go ahead":** you start building immediately — writing scripts, creating files, executing code — when the user actually wanted you to queue it for the player-agent dev loop.

Signs you're in the trap:
- You're writing implementation code (scripts, configs, project scaffolding) that could be a player-agent task
- The user said "autonomously" but you're doing the work yourself in real-time
- You have a todo list of build tasks and you're checking them off in the same session
- The result is "I built X" rather than "X is queued as task N for the player-agent"

**Correction:** When the user says "have it done autonomously" or "place in queue", STOP executing. Instead:
1. Break the work into player-tick-sized tasks (2-5 min each)
2. Write them as AGENTS.md in a new project under /home/sc/repos/
3. Create .checkpoint.json and register in master checkpoint
4. Report what you queued — not what you built

The player-agent runs every 30 minutes and the coach-agent follows up. Your only job is to set up the queue so they can execute without you.

### Static Scoring Drift

The feasibility matrix scores are a snapshot. Re-score when:
- New constraints emerge (e.g., RAM pressure, needed API key unavailable)
- A starred repo releases a major version
- You've already built three items in a row from one tag cluster (diminishing returns)

## Worked Example: Hermes System Console

The canonical example of this methodology producing a real application:

**Phase 0:** "I have 6 web apps, 16 cron jobs, 11 systemd services, and no unified view of any of it."

**Phase 1:** Discovered Hermes Dashboard (:9119) shows session metrics but not system health. Netdata (:19999) shows system health but not dev-loop progress. Gap: no app bridges them.

**Phase 2:** Gap-filling pattern — the gap between monitoring (Netdata) and development (checkpoint/coach reviews) is itself an application opportunity.

**Phase 3:** Go + Svelte 5 (same stack as HWC), one new service, zero new dependencies, no API keys. Score: 30/35.

**Phase 4:** Build Now — Hermes System Console at /home/sc/repos/hermes-system-console, port :3030, 5-tab SPA.

**Dev loop integration:** Added to master checkpoint as 5-phase build. Player builds one phase per 2h tick. Coach reviews each phase. Netdata monitors the deployed service.

Full architecture at /home/sc/workspace/system-architecture.md.

## Related Skills

- **software-development/cv-generation** — scan owned repos for CV content (different goal from combinatorial design)
- system-architecture — the full architecture document at /home/sc/workspace/system-architecture.md
- context7 — live documentation during implementation
- player-agent — builds approved candidates
- coach-agent — reviews output
