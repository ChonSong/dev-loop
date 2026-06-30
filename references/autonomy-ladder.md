# Autonomy Ladder — How Capabilities Climb from C → A

> **Source:** Steward-OS Architecture — Autonomy Bands; OWASP Top 10 for Agentic Applications 2026.  
> **Rule:** Every action sits in a band. The band determines how much human is in the loop. Promotion is earned, not assumed.

---

## The Bands

| Band | Human in loop? | When safe | Example |
|---|---|---|---|
| **C** — Human-gated | Human takes the irreversible action | Action is irreversible, reputational, or a values call | Morning briefing content posted to Discord, closing a GitHub issue |
| **B** — Session-autonomous | Agent works, human reachable at decision points | Work benefits from autonomy but human owns final call | Coach review tick, Player implementation tick |
| **A** — Autonomous | No human present, runs on schedule/trigger | Reversible, low-blast-radius, AND (mechanical OR watchdog-verified) | Session pruning, deploy verification, log rotation |

## The Safety Bar for Band A

An action qualifies for Band A ONLY when ALL three conditions are met:

| Condition | Test |
|---|---|
| **Reversible** | Can the wrong action be undone? Is the cost negligible? |
| **Low-blast-radius** | Does it affect ≤1 surface? No cascading effects? |
| **Verified** | Is it mechanical (deterministic, no LLM) OR independently watched by a watchdog? |

**CRITICAL:** If an action is irreversible AND touches a public surface AND can't be made mechanical → it does NOT belong in Band A. Keep at C, or keep a human on the final step in B.

## Promotion Recipe (C → B → A)

For each rung:

### C → B: Earn supervised autonomy
1. Run the action in Band C for ≥10 cycles, logging every decision.
2. Identify the decision points where the agent would need to stop and ask.
3. At each decision point, log: what the agent would have done vs. what the human did.
4. When agreement rate >90% at all decision points → qualify for B.
5. Move to Band B with explicit "stop and ask" rules for the remaining ambiguous decisions.

### B → A: Earn unattended trust
1. Make it mechanical where possible (deterministic code, no LLM).
2. Build the watchdog BEFORE removing the human.
3. Verify the watchdog catches at least one deliberately wrong action.
4. Roll out gradually: small batch → verify → expand → full.
5. Make it idempotent and silent-on-no-op.
6. Keep the kill switch: every A job stays pausable, its effects reversible.

## Our Cron Job Classification (2026-06-29)

### Band A — Autonomous (32 jobs)

These are mechanical, reversible, or watchdog-verified. Safe to run unattended.

| Job ID | Name | Why Band A |
|---|---|---|
| `e4d95660ab35` | seans-reporepo refresh | `no_agent: true`, script-only |
| `64280d3687bf` | context-budget-audit | LLM but `deliver: local`, analysis only |
| `ecb3846b907b` | hermes-web-computer rebuild | LLM, `deliver: local`, build check |
| `65520f7d71f9` | skill-selector-prep | `no_agent: true`, script |
| `5b47d796f26f` | html-in-canvas-api-monitor | LLM, `deliver: local`, monitoring |
| `35dfd98f75e8` | Commitment Auditor | LLM, `deliver: local`, analysis |
| `e8f57eddfa43` | Daily QA Audit wiz | LLM, `deliver: local`, QA |
| `ed2a80c4636e` | HWC Health Audit | LLM, `deliver: local`, analysis |
| `29347c54bf6a` | GTO Deploy Log Rotation | `no_agent: true`, script |
| `db0a0cecb971` | Night Health Snapshot | `no_agent: true`, script |
| `bd4cecc76077` | Night DB Compaction | `no_agent: true`, script |
| `aa0b2cde6de1` | weekly-repo-research-briefing | `no_agent: true`, script |
| `5d06462b5271` | gto-wizard-health-check (LLM) | LLM, `deliver: local` |
| `4961f5714c31` | cron-healer | `no_agent: true`, script |
| `e353ec3108b6` | Daily Seek Search | `no_agent: true`, script |
| `bdbfb3d0bfd8` | Daily Indeed Search | `no_agent: true`, script |
| `b46255a1ad22` | Daily Job Pipeline | `no_agent: true`, script |
| `a773daee3f7d` | Dev Loop Log Rotation | `no_agent: true`, script |
| `38a9145e2062` | skill-auto-archive | `no_agent: true`, script |
| `d995048fa26d` | skill-discovery | LLM, `deliver: local` |
| `57ee4a02789b` | Nightly SkillSpector | `no_agent: true`, script |
| `3196a93364b8` | deploy-verify | `no_agent: true`, script, read-only |
| `c1d5931cc726` | skill-context-trimmer | `no_agent: true`, script |
| `e461becc33cf` | escalate-stagnant-bugs | `no_agent: true`, script |
| `64339e205c2a` | coach-provider-watchdog | `no_agent: true`, script |
| `2880db7731a5` | dev-knowledge-rebuild | `no_agent: true`, script |
| `b50e2d568fe6` | coach-model-selector | `no_agent: true`, script |
| `a7a1d1498843` | skill-curation-discover | `no_agent: true`, script |
| `a183ad0c72a4` | session-pruner | `no_agent: true`, script |
| `752d51adb96d` | Polytopia deploy loop ⚠️ | `no_agent: true` BUT deploys to live site — **needs watchdog** |
| `2e2e8fd7f3e5` | 3DCP Landscape Monitor ⚠️ | `no_agent: true`, `deliver: origin` — **public write without watchdog** |
| `ab4511dbc8b0` | gto-wizard-health-check (no_agent) ⚠️ | `no_agent: true`, `deliver: origin` — **public write without watchdog** |

### Band B — Session-autonomous (7 jobs)

LLM-driven, requires judgment. Human reachable at decision points.

| Job ID | Name | Why Band B |
|---|---|---|
| `166753e315ea` | GTO Wizard QA Sweep | LLM, every 4h, auto-delivers QA findings |
| `b4f35d68ede1` | player-development-loop | Core implementation — LLM writes code |
| `5e1bba516d87` | coach-development-loop | Core review — LLM evaluates code |
| `83e9c3a48cff` | Self-Improvement Engine | LLM judgment on system improvements |
| `abcdf5f6211e` | Daily Queue Summary | LLM summarizes job queue |
| `bf9d66f13b3a` | skill-curation-evaluate | LLM evaluates skill quality |
| `2e5218015242` | dev-loop-steward | LLM, every 3h, auto-delivers analysis |

### Band C — Human-gated (5 urgent)

These write to public surfaces without watchdog. They should stay at Band C or get a watchdog.

| Job ID | Name | Current | Issue | Fix |
|---|---|---|---|---|
| `56685e569e5f` | Morning Briefing | `deliver: origin` | LLM generates news content, auto-posts to Discord daily. Hallucination risk. | Change to `deliver: local` + add human-approval step before delivery |
| `91fb5f28f06d` | opportunity-radar | `deliver: origin` | Auto-delivers research findings. Low risk but unverified. | Change to `deliver: local` or add watchdog |
| `8a57d7393f8c` | dev-loop-telescope | `deliver: discord` | Script auto-posts to Discord every 6h. Script output is the message. | Low risk (deterministic script) — could stay at A with a content watchdog |
| `d948ab773678` | dev-loop-staleness-check | `deliver: discord` | Script auto-posts staleness alerts to Discord. | Low risk — alerts only fire when system is stuck. Acceptable. |
| `f5c915150c7a` | dev-loop-eval-baseline | `deliver: discord` | Weekly eval results to Discord. | Low risk — factual benchmark results. |
| `f47269000cf0` | coach-verdict-watchdog | `deliver: origin` | LLM watchdog auto-delivers. | Watchdog needs a watchdog? Meta. Keep at B — it watches the watcher. |

### Disabled/Paused (1)

| Job ID | Name |
|---|---|
| `44e20aeed5e2` | hermes-daily-backup (paused) |

## Action Items (Highest Priority First)

### 🔴 P0: Polytopia Deploy Watchdog
**Job:** `752d51adb96d` — deploys to `hex.codeovertcp.com` every 30 min with zero verification.
**Risk:** Broken deploy → 30 min before human notices. No watchdog.
**Fix:** Add a post-deploy verification watchdog that checks HTTP 200 + core game loop loads.

### 🔴 P0: Morning Briefing Human Gate
**Job:** `56685e569e5f` — generates news content via LLM, auto-posts to Discord.
**Risk:** Hallucinated news posted as fact to public Discord. Daily.
**Fix:** Change `deliver` to `local`, save briefing to file. Human reviews, then triggers delivery.

### 🟡 P1: Tag All Cron Jobs With Bands
Apply `[Band-X]` prefix to all cron job names. Makes the autonomy level visible in `cronjob list`.

### 🟡 P1: Apply Toolset Presets
Coach cron → `coach-review` preset. Player cron → `player-implement` preset.

### 🟢 P2: 3DCP + GTO Health Check Watchdogs
`2e2e8fd7f3e5` (3DCP) and `ab4511dbc8b0` (gto health check) both `deliver: origin` with no watchdog. Low-traffic, low-risk, but still unverified public writes.

---

## Promotion Log

Track when capabilities move between bands. Empty until first promotion.

| Capability | Started | Band C | Band B | Band A | Watchdog? |
|---|---|---|---|---|---|
| Deploy verification | 2026-04 | - | - | 2026-04 | no_agent=mechanical ✓ |
| Coach review | 2026-05 | - | 2026-05 | - | - |
| Player implementation | 2026-05 | - | 2026-05 | - | - |
| Session pruning | 2026-05 | - | - | 2026-06 | no_agent=mechanical ✓ |
| Cron healing | 2026-04 | - | - | 2026-04 | no_agent=mechanical ✓ |
| Watcher intake | 2026-06 | - | - | 2026-06 | no_agent=mechanical ✓ |
| Steward health | 2026-06 | - | - | 2026-06 | no_agent=mechanical ✓ |
| (add new capabilities here) | | | | | |

---

## Kill Switch Policy

Every Band A job must be:
1. **Pausable** — `cronjob pause <id>` works, no side effects
2. **Reversible** — effects can be undone (or wrong-action cost is negligible)
3. **Monitored** — `cron-healer` watches for errors, escalates if recurring

Jobs that cannot meet all three → not Band A.
