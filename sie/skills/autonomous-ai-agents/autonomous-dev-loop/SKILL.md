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

# Autonomous Development Loop

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

9. **Broken pipe errors on long cron ticks** — Cron ticks that exceed ~180s (terminal timeout) get killed with `[Errno 32] Broken pipe`. Keep tasks small (one unit of work per tick). For longer tasks, use `delegate_task` or background processes.

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

- `references/system-architecture.md` — Full system architecture (services, ports, pipelines, failure modes, recovery procedures). Read this for the big-picture context the dev loop operates within.
