# Dev Loop Evolution Timeline

Chronological evolution of the autonomous development loop: June 13–25, 2026. The system progressed through 6 architectural phases in 12 days, driven by operational failures, external research, and principle reversals.

> **Note:** This is a historical reference. The current active architecture is documented in `coach-agent` and `player-agent` skills. This skill (`autonomous-dev-loop`) documents the legacy loop for reference.

---

## Phase 0 — Precursors (April–May 2026)

Before the dedicated dev loop, work was organized via **phase engines** (`PHASE_TRACKER.json`) for the HWC project.

| Date | Event | Significance |
|------|-------|-------------|
| 2026-04-26 | First Hermes cron jobs created (Memory Curation, Morning Briefing) | Cron infrastructure established |
| 2026-05-11 | First phase-engine cron for HWC | `PHASE_TRACKER.json` pattern — 9 phases by May 15 |
| 2026-05-25 | GTO Wizard Clone project starts; 6 cron jobs | First project that would become the dev loop's primary workload |
| 2026-05-28 | Roadmap engine lost in `/tmp/` on container restart | Rule: never store working code in /tmp/ |
| 2026-06-13 | Hermes migrates from Docker container to host (systemd) | Enables host-native SSH-less cron operation |

## Phase 1 — Master Checkpoint Loop (June 13–14)

**Architecture:** Single monolithic cron, every 120min, SSH from Docker to host.

**Key events:**
- Jun 13: `master-checkpoint.json` created at `~/.hermes/` with projects, phases, priority, health
- Jun 14 02:11 UTC: **`player-development-loop`** cron created (`b4f35d68ede1`), model `openrouter/owl-alpha`
- Jun 14 00:14 UTC: **`coach-development-loop`** cron created (`5e1bba516d87`), model `claude-sonnet-4` at :05/:35

**Initial problems:** TIRITH blocked cron terminal commands, SSH key path mismatches, `deliver=origin` failed silently.

## Phase 2 — Coach/Player Split (June 14–17)

**Architecture:**
- `:00` → Player (60min, flash model)
- `:05/:35` → Coach (offset, strong model)

**Key events:**
- Jun 16 10:17 UTC: **`ChonSong/dev-loop` repo initialized** (commit `ccf14dc`)
- Jun 16 10:20 UTC: Initial setup commit (`f2a3b36`) — 12 files, 767 lines: AGENTS.md templates, scoring model, cron config, agent role docs. Author: "Sean (via Hermes)"
- Jun 16 10:47 UTC: Skill inspiration documentation (`6038027`) — mapped 12+ Hermes skills to agent design decisions
- ~Jun 15-16: `coach-agent` (~81KB) and `player-agent` (~34KB) skills created

**Design rationale:** Separate agents ensure fresh context — Coach never inherits Player's context, preventing rationalization of shortcuts.

## Phase 3 — Pitfalls & Iteration (June 17–24)

Four major crises resolved during this period:

### Jun 20: Full System Audit
Session `d9a27cf2cd27`. Findings: 96 LLM calls/day, 13GB `.hermes`, 33 cron jobs, 1,686 skills. Applied low/zero-risk cuts: archived 30 repos, pruned npm/sync caches, merged duplicate crons, paused coach loop.

### Jun 22: Self-Improvement Engine v1.3
Session `d9d797569448`. Added Phase 0 Proactive Coverage Scan — discovers blind spots before processing learnings. Motivated by HWC LRN-010: 11 bugs (2 P0) missed by all autonomous loops because the system optimized its stated goal to perfection.

### Jun 23: Broken Pipe Crisis
Session `40f52032fa48`. Player ticks killed with `[Errno 32] Broken pipe`. **Root cause:** tick overlap (30min schedule, 25-29min tick duration), not execution speed.

**Applied fixes:**
- terminal.timeout: 180s → **600s**
- agent.gateway_timeout: 1800s → **3600s**
- agent.max_turns: 300 → **500**
- Coach SKILL.md: 81KB → **~21KB (user further edited)**
- Player SKILL.md: 19KB → **3.7KB**
- Player schedule: every 30min → **every 60min**

**Key lesson:** "Trim skills, don't remove them." The first fix removed skill references from cron jobs, which the user flagged as cutting too much. The correct fix trims content while keeping capability.

## Phase 4 — Memory Pipeline (June 24)

Session `7691b3e7608e`. The most transformative day — the loop gained persistent behavioral memory.

**Investigation:** Coach identified a systemic gap ("I keep rediscovering the same facts"), researched [vostride/agent-qa](https://github.com/vostride/agent-qa), extracted 10 architectural patterns from 150KB+ of source across 9 packages.

**Ported (5 of 10 patterns):**
- **A.U.D.N. Curator** → `curator.py` (460 lines)
- **Circuit Breaker** → `circuit_breaker.py` (20-run rolling window, 15% threshold)
- **Failure Classifier** → `classifier.py` (8 categories, 7-needle priority)
- **FTS5 Memory Index** → `index.py` (stopword-stripped OR queries)
- **Jaccard Dedup** → `similarity.py` (0.85 title-aware threshold)

**10 files, 1,830 lines created in ~90 minutes.** Committed at 2026-06-24 22:50 AEST (`a6b9a79`).

**Memory pipeline cron architecture (still active):**
```
:04/:34 → coach-memory-pre (no_agent — circuit breaker check + injection)
:05/:35 → coach-development-loop (context_from pulls memory context)
:10/:40 → coach-memory-post (no_agent — extraction + curation + breaker update)
```

## Phase 5 — Enforcement & Reversal (June 24–25)

After a Coach "no actionable findings" rubber-stamp event, an enforcement layer was built — then torn down.

**Built (Jun 24 23:01 UTC):**
- `enforce_qa_gate.py` (186 lines) — keyword scanner rejecting approvals missing evidence words
- `coach-post-check.py` — compliance-on-top-of-compliance scanner
- Cron job `d6c6dc681122` wired in

**Reverted (Jun 25 00:17 UTC), commit `b8e3054`:**
> "Root cause was building compliance checks on self-reported text instead of independent page-state verification. The coach needs principles + tools, not procedures + gates."

**Deleted:** enforce_qa_gate.py, coach-post-check.py, gate cron. SKILL.md restored from 115 lines of hard rules to 63 lines of principles.

**Key insight:** Verifying what the Coach *says* (keywords) is orthogonal to verifying what it *does* (page state). Principles beat compliance gates.

## Phase 7 — Testing Methodology Reform (June 25)

After `enforce_qa_gate.py` was scrapped (Phase 5 reversal), the same underlying problem resurfaced through a different lens: **Player-written E2E tests were self-referential** — they validated the implementation, not the requirement. The Coach correctly identified the symptoms (wrong Phaser APIs, coordinate scaling, keyboard unreliability in headless) but classified them all as "test bugs" rather than methodology failures.

**Investigation session `377397efc8d3`:** Discovered 4 concrete self-referential test failures in polytopia-clone's `gameplay.spec.ts` (pause overlay, mute button, tech panel coords, city menu close). The AGENTS.md task templates were part of the problem — tasks said "Add E2E test for X" instead of "Define expectations from reference, test first, implement."

**Four fixes applied 2026-06-25:**

1. **GTO Wizard E2E runner fixed** — nested `@playwright/test@1.61.0` at both root (via `next.js` transitive dep) and `apps/web/e2e/node_modules` (separate install) caused "Requiring second time" error. Fix: removed e2e's duplicate `node_modules`, stripped `@playwright/test` from `e2e/package.json`, rewrote `playwright-test.sh` to use root's `npx playwright`. Diagnosis pattern captured in `references/e2e-runner-nested-node-modules.md`.

2. **Coach Methodology Gate (Step 2.5)** added to `coach-agent/SKILL.md` — mandatory classification of every test failure as either test bug or methodology failure before APPROVE. Six detection criteria, specific verdict language (`🔴 METHODOLOGY FAILURE`), verdict impact (>50% methodology blocks APPROVE).

3. **AGENTS.md task generation reformed** — `skills/writing-tasks.md` updated with "Test Methodology: Expectations First" section. Good: "Define expectations from reference, write failing tests, implement." Bad: "Add E2E test for X."

4. **Player pre-flight plan enforcement** — `player-agent/SKILL.md` updated with enforcement gate requiring all six fields (Touches, Specification, E2E baseline, Happy, Negative, Boundary) populated before any `read_file`/`write_file` call. Cron prompt updated to list all six fields.

## Phase 6 — Current Steady State (June 25 onward)

**Active cron jobs (as of Jun 25 20:00 AEST):**\n| Job | Schedule | Model | Ticks |\n|-----|----------|-------|-------|\n| player-development-loop | `0 * * * *` | openrouter/owl-alpha | 437 |\n| coach-development-loop | `5,35 * * * *` | **big-pickle** (opencode-zen) | 456 |\n| coach-memory-pre | `4,34 * * * *` | no_agent | Active |\n| coach-memory-post | `10,40 * * * *` | no_agent | Active |\n| escalate-stagnant-bugs | `15,45 * * * *` | no_agent (`escalate-stagnant-bugs.py`) | Active |\n\n### Structural Safeguards Added (Jun 25)\n\n1. **Pre-commit hooks** — Both project repos reject \"Add E2E test for X\" in AGENTS.md (template at `autonomous-dev-loop/templates/pre-commit-hook-reject-self-referential-tests.sh`)\n2. **Auto-escalation cron** — `escalate-stagnant-bugs.py` (no_agent, :15/:45) increments `cycles_stagnant` for unresolved gaps, flags at ≥3\n3. **Player checkpoint freshness check** — MANDATORY step before trusting master checkpoint (`last_run` < 3h)\n4. **E2E runner isolated** — Moved from `apps/web/e2e/` (nested workspace member) to root `e2e/` as first-class workspace\n\n### Task Ownership Model Validated (Jun 25 19:43)\n\nOn **first real-world test**, the Coach's Step 4 task generation produced:\n- **3 fresh AGENTS.md tasks** generated from browser-verified evidence (`fix-filters-sub-tab-stub`, `fix-blockers-sub-tab-missing`, `fix-spaced-repetition-practice-mode`)\n- **12 stale spec_gaps cleaned** from checkpoint\n- **current_task set** to first unstarted task\n- Verifiable from Coach output `2026-06-25_19-43-01.md`\n\nThis is the first time in the dev loop's history that the Coach autonomously replenished the Player's backlog. Previous behavior: Coach only added spec_gaps, never translated them into work items. The Player's self-referential Task Exhaustion Recovery was the sole backlog mechanism.\n\nThe Player remains on `openrouter/owl-alpha` (flash-class, weaker). If the Player consistently fails to execute tasks the Coach generates, the Player model is the next bottleneck to address.

**Active projects (as of Jun 26):**
- gto-wizard-clone (Phase 2, priority 1) — build_ok_site_200_no_errors
- polytopia-clone (Phase 2, priority 2) — 457 tests pass
- cluster-mine-queue (Phase 1, complete)
- energy-aware-task-router (Phase 7, complete) — 75 tests pass
- hermes-webui-dev (Phase 1, blocked) — 502 error

**Current architecture:**
```
Memory Pipeline (every 30min):
  :04/:34 → coach-memory-pre → injection/breaker
  :05/:35 → coach-development-loop → review + verdict
  :10/:40 → coach-memory-post → curation + outcome

Player Loop (every 60min):
  :00 → player-development-loop → task → test → commit → checkpoint
```

## Meta-Statistics

| Metric | Value |
|--------|-------|
| Total active period | 12 days (Jun 13–25) |
| Architectural phases | 6 |
| Commits to dev-loop repo | 24 |
| Reversals (build then revert) | 1 (enforcement gate) |
| Autonomous improvement cycles | 1 (agent-qa port) |
| Operational crises | 3 (tick overlap, skill bloat, rubber-stamping) |
| External projects ported from | 1 (vostride/agent-qa) |
| Skills loaded per tick (coach) | ~21KB (from 81KB) |
| Skills loaded per tick (player) | ~3.7KB (from 19KB) |

## Deferred Items

Patterns identified but not yet implemented (from agent-qa port):
- Action cache (sub-action hashing + prefix invalidation)
- Verifier phase (separate LLM check after step complete)
- Secrets redaction (needed for cached actions with embedded credentials)
- Forced tool calls (deeper Player architecture change)

---

## Meta-Analysis: Why the Dev Loop Hasn't Been Successful After 12 Days

This section was added after a deep 4-workstream investigation (session ~Jun 25 15:00) that analyzed 10+ Coach cron sessions, 25 dev-loop commits, 20 session transcripts, and 2 project repos.

### Root Cause #1: The Compensation Loop

The system's architecture creates a self-referential feedback loop:

```
v4 flash writes shallow Coach verdicts
  → User adds rules to SKILL.md
    → Skill grows (more preamble consumed per tick)
      → Less context remaining for actual work
        → Flash cuts corners even more
          → More rules added...
```

This is visible throughout the evolution:
- The enforcement gate was built and scrapped in 2 hours because it "checked words not truth"
- Every rule in the coach-agent skill traces to a specific flash failure ("HTTP 200 is NOT browser QA" was written because flash kept doing it)
- The skill grew from 63 lines of principles back toward procedural bloat

**The irony**: The system built a self-referential compliance gate (checking whether verdicts mention keywords) to fix a self-referential testing problem (Player tests checking implementation against itself). The meta-problem mirrors the ground-level problem.

### Root Cause #2 (Resolved): Same Model for Coach and Player

The original design specified:
- **Player** on flash (fast, cheap, executes)
- **Coach** on a stronger model (deep reasoning, catches flaws)

This was silently abandoned when the stronger model kept erroring. Both ran on `deepseek-v4-flash` for multiple days. That regression is the single largest root cause of the compensation loop.

**Evidence (pre-fix, flash-only era):**
- 0 delegation in 5 consecutive sessions (despite explicit requirement)
- HTTP 200 substituted for real browser QA on every cycle
- 10-20 tool calls total across two projects (should be 50+)
- advance-to-turn bug stagnant for 6+ cycles through 4+ Coach approvals

**Fix applied 2026-06-25:**
- Coach cron changed from `deepseek-v4-flash` (opencode-go) to `big-pickle` (opencode-zen)
- Coach SKILL.md simplified from 300 to 71 lines (removed flash-specific compensation rules)
- First big-pickle cycle at 15:24 found a P1 bug flash missed for days (tribe selection sort mismatch)
- Second big-pickle cycle at 19:43 generated 3 fresh AGENTS.md tasks — first time Coach ever replenished the backlog

**Ongoing risk:** Player (`b4f35d68ede1`) still runs on `openrouter/owl-alpha` — flash-class model. If the Player cannot execute tasks the Coach generates, the loop stalls at the implementation layer. Monitor Player output; consider upgrading Player model if consistent execution failure.

### Root Cause #3: Documentation-Level Fixes Only

Every fix is a SKILL.md patch — text instructions for the same LLM. There is no structural enforcement:
- No git hook prevents "Add E2E test for X" from appearing in AGENTS.md
- No CI gate validates that tests precede code
- No automated check verifies the Coach visited the page vs. curling it
- No mechanism prevents the master checkpoint from going stale (the methodology fix was gated on stale data for 2+ hours)

### Root Cause #4: The E2E Runner Black Hole

47 e2e-related commits, "fixed" 5+ times across 3 weeks. Problem returns after every `npm install`. The root cause is structural (monorepo hoisted deps vs nested @playwright/test), not a quick fix. Every cycle spent on the E2E runner is a cycle not spent on shipping features.

### Structural Fixes That Would Work

| Fix | Mechanism | Impact |
|-----|-----------|--------|
| Restore Coach to stronger model | Model separation in cron config | 🔴 Root cause — different model brings different reasoning |
| Pre-commit hook banning "Add E2E test for X" | Git hook | 🔴 Stops self-referential task format at source |
| Separate Playwright install outside monorepo | Structural dependency fix | 🟡 Stops the #1 wheel-spinning drain |
| Coach must produce screenshot filenames in verdicts | Post-hoc verification | 🟡 Makes shallow QA visible |
| Auto-escalate after 2 cycles stagnant | Checkpoint counter | 🟡 Prevents bugs from rotting |
| Master checkpoint freshness validation | Pre-tick git log check | 🟡 Prevents staleness masking |

See `references/compensation-loop-analysis.md` for the full analysis of the meta-pattern, and `references/coach-model-bottleneck.md` for session-level evidence of specific v4 flash failure modes.
