---
name: autonomous-dev-loop
description: "Checkpoint-driven autonomous development loop. Cron-triggered every 2h, picks ONE task from a backlog, implements it, tests, commits, and advances a persistent checkpoint. Runs via SSH from Docker container to host."
version: 1.0.0
tags:
  - autonomous
  - cron
  - checkpoint
  - development-loop
  - ssh
related_skills:
  - roadmap-engine
  - self-improvement-engine
  - subagent-driven-development
---

# Autonomous Development Loop (Legacy Architecture)

> **⚠️ NOTE: The current active dev loop uses the coach-agent/player-agent pair.** See `coach-agent` and `player-agent` skills for the current architecture. This skill documents the LEGACY loop (predates the coach/player split) and should only be used as reference for checkpoint format, SSH patterns, and pitfalls that still apply to the current system.
> 
> **Active now:** `player-development-loop` (every 60min, opencode-go/owl-alpha) + `coach-development-loop` (:05/:35 past hour, opencode-zen/big-pickle). Memory pipeline: pre-inject :04/:34 → coach :05/:35 → post-curate :10/:40.\n> **Task ownership model (2026-06-25):** Coach now owns the AGENTS.md task backlog. Coach Step 4 generates 2-5 tasks per cycle from browser-verified evidence. **Validated on first real-world test (19:43)** — 3 fresh tasks generated, 12 stale spec_gaps cleaned, `current_task` set. The Player's Task Exhaustion Recovery (self-referential task generation) is now a rare safety net, not the primary backlog replenishment mechanism. See `references/task-ownership-architecture.md`.
> **Structural safeguards (2026-06-25):** pre-commit hooks (`templates/pre-commit-hook-reject-self-referential-tests.sh`) in both project repos, `escalate-stagnant-bugs` no_agent cron (`references/stagnation-escalation-pattern.md`), Player checkpoint freshness check, E2E runner moved to root workspace member.
> **Same-model regression fixed 2026-06-25:** Coach changed from deepseek-v4-flash to opencode-zen/big-pickle; coach-agent SKILL.md simplified 300→71 lines removing flash-specific compensation rules.
> **Legacy (this skill):** Master-checkpoint-driven loop (every 120min, SSH-to-host)

Checkpoint-driven autonomous development. A cron job fires every 2h, reads a master checkpoint to find the highest-priority project with pending work, executes ONE unit of work (code → test → commit), and advances both per-project and master checkpoints.

This is NOT the roadmap-engine (nightly planning across many projects) — this is a focused single-task-per-tick execution loop for in-flight development work.

## Architecture

```
cron (every 120m)
  │
  └── read ~/.hermes/master-checkpoint.json
        └── find highest-priority project with work
              └── read project/.checkpoint.json
                    └── execute ONE task
                          ├── write code
                          ├── run tests
                          ├── git commit
                          └── update both checkpoints
```

### Checkpoint Format (master-checkpoint.json)

```json
{
  "last_run": "2026-06-14T18:30:00Z",
  "active_project": "energy-aware-task-router",
  "phase": 4,
  "projects": {
    "energy-aware-task-router": {
      "status": "active",
      "priority": 1,
      "health": "32_pass_0_error_0_fail",
      "next": "Phase 4b: API key authentication middleware"
    }
  }
}
```

### Per-Project Checkpoint (.checkpoint.json)

```json
{
  "project": "energy-aware-task-router",
  "phase": 4,
  "phase_name": "Production Hardening",
  "completed": ["Phase 1: ...", "Phase 2: ..."],
  "current": "Phase 4a: rate limiting done",
  "next": "Phase 4b: API key authentication middleware",
  "health": "32_pass_0_error_0_fail",
  "last_sha": "726346c",
  "blocker": null
}
```

## When to Use

- A project has 3+ phases of work and needs unsupervised advancement
- You want to tick through a backlog autonomously (one task per tick)
- You have host SSH access from the Docker container
- TIRITH is disabled (`tirith_enabled=false` in config.yaml) or `approvals.cron_mode=auto_approve`

## When NOT to Use

- One-off tasks that finish in a single session — use direct execution
- UI/visual work requiring human judgement — use autonomous-development (vision-driven) skill
- Nightly broad planning across 10+ projects — use roadmap-engine instead

## Setup

### 1. Check TIRITH/Approvals

```yaml
# config.yaml
security:
  tirith_enabled: false   # cron cannot approve terminal commands otherwise
approvals:
  cron_mode: auto_approve  # needed for git/pytest in cron context
```

### 2. Create Master Checkpoint

Place at `~/.hermes/master-checkpoint.json` on the HOST:

```json
{
  "last_run": null,
  "active_project": null,
  "phase": 1,
  "projects": {
    "project-name": {
      "status": "active",
      "priority": 1,
      "phase": 1,
      "health": "unknown",
      "next": "First task description",
      "blocker": null
    }
  }
}
```

### 3. Create Project Checkpoint

Place at `project-root/.checkpoint.json`:

```json
{
  "project": "project-name",
  "repo": "/home/sc/repos/project-name",
  "phase": 1,
  "phase_name": "Phase Name",
  "completed": [],
  "current": null,
  "next": "Next task description",
  "health": "unknown",
  "last_sha": null,
  "blocker": null
}
```

### 4. Create the Cron Job

```bash
# Using hermes cronjob tool
cronjob(action='create',
  name='master-development-loop',
  schedule='every 120m',
  workdir='/home/sc',
  deliver='local',
  enabled_toolsets=['terminal', 'file', 'web'],
  prompt='''You are the master autonomous development loop.
...
''')
```

The cron prompt must inline the full backlog and instructions since the cron session cannot load skills from the host's directory.

## Backlog Structure

Priority order matters — the cron picks the highest-priority project with `status: active` or `pending`:

| Priority | Project | Typical Tracks |
|----------|---------|----------------|
| P1 | Primary active project | New feature build, phases 1-N |
| P2 | Test/QA improvement | Playwright rewrite, test infra fixes |
| P3 | Consolidation | Vendor libs, remove redundancy |
| P4 | Migration | Port code between projects |
| P5 | Infrastructure | CI/CD, deployment, tooling |

## SSH Access

The loop runs FROM the Docker container TO the host. Key patterns:

```bash
# Current working setup (host user sc, key in authorized_keys)
ssh -o StrictHostKeyChecking=no sc@localhost <command>

# Original setup (may not work - key path was wrong)
ssh -i /home/hermes/.ssh/id_ed25519 sean@localhost <command>
```

The SSH key must be in the host's `~/.ssh/authorized_keys`. Test with:
```bash
ssh -o StrictHostKeyChecking=no sc@localhost "echo CONNECTED"
```

### Cron Prompt Pattern

The cron job prompt must be self-contained (no skill dependency). Pattern:

```
## Every Run
1. Read master checkpoint: cat ~/.hermes/master-checkpoint.json
2. SSH to host: ssh -o StrictHostKeyChecking=no sc@localhost
3. Find highest-priority project with "status": "pending" or "active"
4. Read that project's .checkpoint.json
5. Execute ONE unit of work from that project's next task
6. If tests exist, run them before commit
7. Git add + commit if tests pass
8. Update both checkpoints
9. Report: "✅ [project]: what was done. Tests: [result]. Next: [next task]"

## Backlog
1. project-a — Phase N (next task)
2. project-b — Phase N (next task)

## Important
- ONE unit of work per run
- If blocked, note blocker in checkpoint and move to next
- Tests before commit always
- Master checkpoint at ~/.hermes/master-checkpoint.json on HOST
```

## Priority Update Rules

When a project's phase completes:
1. Update per-project checkpoint: mark current phase done, set next phase + task
2. Update master checkpoint: advance phase, update health/next
3. If project is fully complete: set status=done, advance next priority project to active

## Common Pitfalls

1. **TIRITH blocks cron terminal commands** — `tirith_enabled=false` in config.yaml is required, not just `cron_mode=auto_approve`. Both settings needed.

2. **Skill reference not found by cron** — Cron sessions run inside the container where host-installed skills aren't accessible. The cron prompt must inline the backlog — do NOT reference a skill name in `skills: []`.

3. **SSH key path mismatch** — The system prompt says `/home/hermes/.ssh/id_ed25519` but the actual key lives at `/home/hermeswebui/.hermes/home/.ssh/id_ed25519`. Use the working path (`sc@localhost`, which uses the logged-in user's key).

4. **deliver=origin fails silently** — Origin delivery was failing with "no delivery target resolved". Use `deliver=local` for cron jobs.

5. **Workdir matters for relative paths** — The cron's workdir must match where SSH commands execute. Set `workdir=/home/sc` for host-scoped operations.

6. **Checkpoint staleness** — The cron reads the checkpoint but doesn't verify it against actual git history. If the checkpoint claims "Phase 2 done" but the repo hasn't been pushed, next ticks build on unverified assumptions.

7. **Backlog projects without repos** — Gating items (like "repo not found") block the entire priority from advancing. Either clone the missing repos or remove the entries from the backlog.

8. **Memory tool drift blocks checkpoint updates** — MEMORY.md written by the curation cron uses markdown format, not the §-delimited format the memory tool expects. This prevents memory writes from the dev loop. Workaround: write directly via terminal to the file, or accept that the curation cron overwrites it daily.

9. **Broken pipe errors on long cron ticks** — Cron ticks that exceed ~180s (terminal timeout) get killed with `[Errno 32] Broken pipe`. Keep tasks small (one unit of work per tick). For longer tasks, use `delegate_task` or background processes. Fixed 2026-06-24: terminal timeout bumped to 600s, agent timeout to 3600s. Player reduced from 30min to 60min schedule to prevent tick overlap kills.

11. **Inline skill bloat kills token budget** — Player and coach skills trimmed 2026-06-24: player 19KB→3.7KB, coach 81KB→17KB (post-user-edit ~21KB). Skills now inline only essential instructions. Skills remain as human reference docs; verbose content moved inline or implicit.

11. **`skills: []` loads full skill content each tick** — Setting `skills: ["player-agent"]` on a cron job injects the full SKILL.md (~34KB player, ~94KB coach before trimming) as system context every run. This burns token budget but does NOT cause broken pipes (see pitfall 10). **When token pressure is a problem, prefer these fixes in order:**
    a) Trim the SKILL.md file itself (as done to coach-agent: 81KB→17KB) — keeps capability, reduces overhead, and works regardless of whether skills or inline prompts are used.
    b) Bump `terminal.timeout` (600s) and `agent.gateway_timeout` (3600s) — these fix actual timeout/rate-limit issues without sacrificing capability.
    c) As a last resort, remove the `skills: []` reference and inline a concise prompt. This loses the detailed operational knowledge the skill carries. Only do this when rate limits are persistent and the skill can't be trimmed further.
    
    **Lesson from 2026-06-23**: The initial fix was (c) — trimming prompts and removing skill references. This was reverted when the user flagged it as cutting too much. The correct approach was (a) + (b): trim the coach skill (81KB→17KB) and bump timeouts. The skills stay loaded, capability is preserved, and the performance issue is solved.

12. **browser_vision 401 / "Model XXX returned HTTP 401" in coach reviews** — The Coach uses `browser_vision` for visual QA. If it fails with HTTP 401 and an unexpected model name:
    - Check `~/.hermes/.env` for `AUXILIARY_VISION_MODEL` and `AUXILIARY_VISION_PROVIDER`. These env vars override `auxiliary.vision.model`/`provider` in `config.yaml` because `browser_tool.py:_get_vision_model()` reads them directly.
    - Even if the config bridge at startup writes the config values to these same env vars, stale `.env` entries can silently point vision calls at an old/unauthorized model on the wrong provider.
    - Fix: remove the stale `AUXILIARY_VISION_*` lines from `.env` and set the intended provider/model in `config.yaml` under `auxiliary.vision`:
      ```yaml
      auxiliary:
        vision:
          provider: openrouter
          model: google/gemini-2.5-flash
      ```
    - Verify the corresponding API key (`OPENROUTER_API_KEY`, etc.) is set in `.env` and has credits/access for the vision model.

13. **Self-referential testing (methodology failure)** — The most common quality failure in the dev loop. The Player writes tests alongside implementation code — those tests validate the implementation, not the requirement. Detection criteria: (a) test written in same session/commit as feature, (b) AGENTS.md task said "Add E2E test for X" where X is that feature, (c) test checks implementation internals (Phaser `children.list`, React state) not user-visible behavior, (d) test passes in headless but feature broken live. The coach-agent skill has a mandatory Methodology Gate (Step 2.5) — the coach must classify test failures as methodology failures vs test bugs and cannot APPROVE if >50% are methodology failures. Player SKILL.md enforces Specification-first pre-flight plans (all six fields required). AGENTS.md task descriptions must use "Define expectations from reference, write failing tests, implement to pass" — never "Add E2E test for X."

14. **Nested node_modules E2E runner conflict** — Monorepo projects where a transitive dep (e.g., `next.js → @playwright/test`) hoists a package to root `node_modules`, while a subdirectory independently installs the same package, causes "Requiring X second time" errors. Fix: remove the subdirectory's duplicate `node_modules`, remove the package from the subdirectory's `package.json`, and use root's binary via `npx`. If there are `.bak` directories with stale installs, remove those too. **Structurally fixed 2026-06-25**: e2e tests moved from `apps/web/e2e/` (nested under workspace member) to `e2e/` at the project root as a first-class workspace member. No more nested `node_modules`, no isolation script needed. `npm run test:e2e` from `apps/web/` delegates to root-level playwright config. 142 tests in 18 files verified. See `references/e2e-runner-nested-node-modules.md` for diagnosis script and previous workaround.

15. **The compensation loop** — The meta-pattern that explains why more rules don't solve quality problems. Each LLM failure triggers a rule addition that reduces the context budget for future work: more rules → more preamble → less context for actual reasoning → worse output → more rules. This was visible in (1) the enforcement gate that scrapped itself after 2 hours because "the gate checks words not truth," (2) the skill bloat that grew from 63 lines of principles back to 300 lines of rules, (3) every rule in the coach-agent SKILL.md tracing to a specific flash failure. **Break this by preferring structural enforcement** (different model, git hooks, pre-tick validation) over documentation-level instructions. **Fixed 2026-06-25**: Coach changed from deepseek-v4-flash to opencode-zen/big-pickle, coach-agent SKILL.md simplified 300→71 lines removing flash-specific compensation rules. Structural enforcement (pre-commit hooks, escalate-stagnant-bugs cron, checkpoint freshness check) prevents recurrence without consuming token budget. See `references/compensation-loop-analysis.md` for the full analysis, detection signals, and how to break the loop.

16. **Same-model Coach/Player regression** — The original design specified Player on flash and Coach on a stronger model. This was silently abandoned when the stronger model kept erroring. The Coach ran on the same model as the Player, meaning the reviewer can catch what the implementer missed only at the level of shared blind spots. If the model can't see a problem during implementation, it won't see it during review either. This single regression is the root cause of most downstream compensation loop iterations. **Diagnosis**: count tool calls in Coach sessions — if the Coach makes 10-20 total calls (0 delegations, curl-only browser checks, no subagent use), it's operating at flash depth despite being the reviewer. **Fix applied 2026-06-25**: Coach cron switched from deepseek-v4-flash (opencode-go) to big-pickle (opencode-zen). Coach SKILL.md simplified 300→71 lines to remove flash-specific compensation rules. Structural safeguards added to prevent regression: pre-commit hooks, auto-escalation cron, checkpoint freshness check. **If regression is suspected**: check coach-development-loop cron job config — model must be `big-pickle`, provider `opencode-zen`. See `references/coach-model-bottleneck.md` for session-level evidence of the failure modes.

## Verification Checklist

- [ ] `tirith_enabled=false` and `approvals.cron_mode=auto_approve` both set
- [ ] Master checkpoint exists at ~/.hermes/master-checkpoint.json
- [ ] SSH works: `ssh -o StrictHostKeyChecking=no sc@localhost "echo OK"`
- [ ] Cron deliver set to `local` not `origin`
- [ ] Cron workdir set to `/home/sc`
- [ ] At least one project checkpoint exists with `status: active`
- [ ] Cron prompt inlines the backlog (no skill reference)
- [ ] First cron tick ran successfully and advanced the checkpoint

## References

- `references/evolution-timeline.md` — Full 6-phase chronology (Jun 13–25) with architecture diagrams, crisis summaries, design reversals, and meta-statistics. Read this before making architectural changes to the dev loop — it records WHY each decision was made.
- `references/system-architecture.md` — Full system architecture (services, ports, pipelines, failure modes, recovery procedures). Read this for the big-picture context the dev loop operates within.
- `references/timeout-diagnosis.md` — How to diagnose `[Errno 32] Broken pipe` errors: terminal timeout vs agent idle timeout, diagnosis checklist, and when to increase terminal.timeout vs trim skill content.
- `references/compensation-loop-analysis.md` — Meta-architectural analysis of the self-defeating feedback loop where LLM failures trigger rule additions that reduce context budget, worsening the original problem. Includes detection signals and structural fixes.
- `references/coach-model-bottleneck.md` — Session-level evidence of v4 flash failure modes in the Coach role: delegation aversion, HTTP 200 proxy for browser QA, brief verdicts, session stalls, and the same-model regression.
