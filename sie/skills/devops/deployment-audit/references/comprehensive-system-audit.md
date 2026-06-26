# Comprehensive System Health Audit

Full-stack investigation of the running system — beyond just a single deployment check. Use when the user asks "what's the state of things?", "review recent sessions", "how are we doing?", before starting complex multi-step work, or after long gaps between sessions.

## Overview

A multi-dimensional orientation that combines historical context, current infrastructure state, scheduling health, and autonomous pipeline status into a single assessment with prioritized next steps.

---

## Phase 1: Historical Context Reconnaissance

Before checking any running process, know what happened before.

### 1a. Browse Recent Sessions

```python
session_search()  # browse mode — chronological previews
```

Look for:
- What project was the user last working on?
- Were there unresolved bugs, pending commits, known issues?
- Any error patterns in recent cron job runs?

### 1b. Targeted Query Search

Search for specific topics relevant to the context:

```python
session_search(query="topic area", limit=5)
```

Use topic-specific queries: "roadmap", "autonomous", "deploy", "disk space", "bug", "error".

### 1c. Read Core Context Files

Read these in order — they form a layered understanding:

| File | What it tells you |
|------|-------------------|
| `SOUL.md` | Core identity, behavioral directives, heartbeats vs cron rules |
| `MEMORY.md` | Active projects, infrastructure facts, pending watch items, lessons |
| `commitments.md` | Active process commitments the agent has made |
| `HEARTBEAT.md` | Current phase, system status, upcoming priorities |
| `memory/YYYY-MM-DD.md` (last 3-5 days) | What was actually done day-by-day |

### 1d. Cross-Reference Daily Logs

Read the most recent 3-5 daily logs. Look for:
- Multiple work streams on the same day (session-switching is easy to miss)
- **Files Changed** sections — show what parts of the codebase were touched
- **Pending** sections — uncompleted work, deferred tasks, known gaps
- Trend: is a problem getting worse? (e.g., disk usage increasing, same bug reappearing)

---

## Phase 2: Infrastructure Surface Scan

Now check the running system.

### 2a. Cron Health Audit

```python
cronjob(action='list')
```

Check every job:
- **Status:** `ok` or `error`?
- **Next run:** scheduled correctly? Not overdue?
- **Delivery:** `local`/`origin`/`all` — is output reaching the right destination?
- **Frequency:** Is the cadence appropriate? Every-15-min watchdog on a systemd-managed service is waste.
- **Stuck jobs:** Jobs that last ran days ago with weekly/monthly schedules — normal? Forgotten?
- **Duplicates:** Two jobs doing the same check?

### 2b. Skills Infrastructure Audit

```bash
# Total skills
find /home/hermeswebui/.hermes -name "SKILL.md" -not -path "*/index-cache/*" \
  -not -path "*/node_modules/*" 2>/dev/null | wc -l

# Category distribution
ls /home/hermeswebui/.hermes/skills/ 2>/dev/null

# Index cache health
ls -la /home/hermeswebui/.hermes/skills/index-cache/*.json 2>/dev/null
# Fresh index caches = skill-selector prep is working
```

Check:
- Are skills being loaded? (Skill-selector auto-loads at session start)
- Are index caches present and recent?
- Is the skill-selector-prep cron running? (weekly Sunday)
- Any obvious gaps? (missing categories for common tasks)

### 2c. Disk Usage

```bash
df -h /workspace /opt/data / 2>/dev/null
```

Tiers:
- **< 80%** — normal
- **80-89%** — elevated, worth noting
- **90-95%** — high risk, schedule cleanup soon
- **> 95%** — critical, block any big writes (npm install, git clone, docker pull) until cleared

Check auto_prune setting in config.yaml:
```bash
grep -r "auto_prune" ~/.hermes/config.yaml 2>/dev/null
```

### 2d. Git & Auth Status

```bash
# Current workspace
cd /workspace && git remote -v 2>/dev/null
git status --short 2>/dev/null | head -20

# GitHub auth
gh auth status 2>&1 | head -5
which gh 2>/dev/null

# SSH key test
ssh -i /home/hermeswebui/.hermes/container_key sean@172.19.0.1 "echo OK" 2>/dev/null
```

Check:
- Is the workspace a git repo with the correct remote?
- Are there uncommitted changes?
- Is `gh` authenticated?
- Can you SSH to the host?

### 2e. Host Service Health (via SSH)

```bash
ssh -i /home/hermeswebui/.hermes/container_key sean@172.19.0.1 "
echo '=== Systemd active services ==='
systemctl --user --no-pager is-active <service1> <service2> 2>/dev/null

echo ''
echo '=== Process on key ports ==='
ss -tlnp 2>/dev/null | grep -E ':3005|:8003|:8564|:8787|:8501'

echo ''
echo '=== All running user services ==='
systemctl --user --no-pager list-units --type=service --state=running 2>/dev/null
"
```

### 2f. Autonomous Pipeline State

If the user has autonomous development infrastructure (roadmap engine, self-improvement pipeline, etc.):

```bash
# Check roadmap state
ls /opt/data/hermes-sync/workspace/plans/roadmap.json 2>/dev/null
# Check for scripts
ls /opt/data/hermes-sync/scripts/*.py 2>/dev/null
# Check /tmp fallback (if container-based)
ls /tmp/hermes-sync/scripts/*.py 2>/dev/null
```

Signals:
- **Scripts exist** — pipeline operational
- **roadmap.json exists** — persistent planning state
- **Scripts missing** — pipeline broken, decide whether to restore or accept the gap
- **roadmap.json missing** — no autonomous direction, fall back to manual tasking

---

## Phase 3: Synthesis & Priority Framework

### 3a. Multi-Dimensional State

Organize findings into:

| Layer | Checks | Status |
|-------|--------|--------|
| **Identity** | SOUL.md, MEMORY.md, commitments.md up to date? | ✅🟡❌ |
| **Scheduling** | All cron jobs green, correct frequency? | ✅🟡❌ |
| **Services** | Expected services running on expected ports? | ✅🟡❌ |
| **Infrastructure** | Disk space, git auth, SSH connectivity? | ✅🟡❌ |
| **Skills** | Library healthy, index caches fresh? | ✅🟡❌ |
| **Autonomy** | Roadmap engine, self-improvement pipeline? | ✅🟡❌ |

### 3b. Priority Ranking

```
🔴 CRITICAL — blocks all work
  Disk > 95%, services down, no auth, core infra broken

🟡 HIGH — degrades capability
  Disk 85-95%, autonomous pipeline broken, stale skills

🔧 MEDIUM — inconvenience
  Redundant cron jobs, minor config drift, one-off gaps

🟢 LOW — nice to fix
  Documentation gaps, non-critical feature deficits
```

### 3c. Presentation Format

Present findings structured as:

1. **What's Working** (✅) — give confidence, no surprises
2. **What's Broken** (🔴❌) — critical to know, may need user decision
3. **What's At Risk** (🟡) — will become critical if ignored
4. **Recommended Next Steps** — priority-ordered, actionable items

## When to Perform

- User asks "what's the state of everything", "review sessions", "how are we doing"
- Before any major infrastructure or deployment change (baseline first)
- After being idle 2+ days (context recovery)
- Start of a complex multi-phase task that depends on infrastructure
- Debugging "why is nothing working" — start with the system, not the code

## Related Skills

Deeper dives into specific dimensions:
- `deployment-audit` — web app deployment verification (title, API, tunnel)
- `cron-job-diagnosis` — fixing broken cron jobs
- `cron-job-optimization` — cron frequency/redundancy audit
- `disk-space-cleanup` — targeted disk recovery
- `development-communication` — keeping the user informed during the audit

## Pitfalls

- **Don't skip Phase 1 (context).** Starting with port checks without knowing what the user last did risks re-fixing already-fixed problems.
- **Don't check everything if not needed.** If the user just asks "did my deploy work?", use `deployment-audit` — not a full system audit.
- **SSH failure ≠ host down.** The container_key may be at a different path than expected. Check `/home/hermeswebui/.hermes/container_key`, `/home/hermes/.ssh/id_ed25519`, and the SSH config (`~/.ssh/config`).
- **Process name can mislead.** A process called `agent-os` on port 3005 might be the HWC server under a different binary name. Check the actual binary path via `/proc/PID/exe`.
- **Cron jobs accumulate silently.** A job paused months ago stays paused. Review the full list, not just the enabled ones.
- **Disk runs out during checks.** Full disk will cause write failures for your own audit output. Check disk FIRST before any multi-file writes.
- **Skills count includes duplicates.** The same skill can appear in multiple paths if HERMES_HOME is overridden. Count unique SKILL.md files per path.
