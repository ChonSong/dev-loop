# Gotcha System — design, format, lifecycle

## What it is

A scenario-specific memory of "things that broke before" — surfaced at the
moment a future session is about to break on them again.

The pattern: most debugging sessions end with the agent learning a gotcha
(an API quirk, a config pitfall, a regex gotcha). Without this system, the
next session re-discovers it. With it, the next session sees the gotcha
before the failure.

## Format — 5-line YAML entries (this matters)

A gotcha is **not** a paragraph. It's **not** the full skill. It's
exactly five fields:

```yaml
- id: cf-tunnel-001          # stable, kebab-case, sortable
  summary: "One-line root cause" # what the agent needs to know FIRST
  symptom: "What the failure looks like" # so trigger matching works
  fix: "The specific action"   # code or command, not advice
  why: "Why this is true"      # optional but high-value
```

Why 5 lines: longer entries get skipped. Shorter entries force the
author to capture the actual lesson, not the full skill load.

## Trigger model — combined file + command + error

Triggers live in `triggers.yaml` and match on three dimensions:

| Dimension | Weight | Example |
|---|---|---|
| Error pattern | 3 | `1033`, `cfd_tunnel`, `ERR.*origin certificate` |
| File path glob | 2 | `*cloudflare-tunnel*`, `*.cloudflared/*` |
| Command regex | 1 | `cloudflared`, `curl.*api.cloudflare.com.*tunnel` |

Higher weight = stronger match. Show outputs in score-descending order.
The agent sees the most likely gotchas first.

**Important pitfall:** When stripping wildcards for regex, replace `*`
with `.*` (not `\w+`). Real paths contain hyphens, dots, slashes.

## Lifecycle — promote-on-2nd-occurrence

```
NEW:   add <id> "summary" --fix "..."     → status=provisional, occ=1
1st:   (no action)                         → still provisional
2nd:   bump <id>                           → status=authoritative, occ=2
3rd+:  bump <id>                           → occ=N, triggers refactor review
OBSOLETE: retire <id>                      → status=obsolete
```

Why 2 not 1: one occurrence might be a misconfiguration, not a real
gotcha. Two independent occurrences = real pattern.

Why NOT auto-promote on N: human judgment is the bottleneck, not
classification. `bump` is a 2-second action and the agent should do it
deliberately, not automatically.

## Promotion target — when a gotcha deserves more

If a gotcha hits `occurrences >= 3` in 30 days, surface it in the
related skill's frontmatter. The skill gets a "Common gotchas" pointer.
The agent sees the gotcha on every skill load, not just on trigger.

Don't merge the gotcha INTO the skill. Keep it in the gotcha system.
Skills are static. Gotchas evolve. The pointer goes one way only.

## ROI measurement — honest accounting

The CLI tracks `stats.json` with:
- `shows[set_name]`: how many times each set was surfaced
- `saves_estimate`: rough count of messages saved (per-occurrence multiplier)

The estimate is rough. Don't trust it for budgeting. Use it to compare
sets against each other: if `cf-tunnel: 50` and `linkedin: 5`, you have
a cf-tunnel problem 10x more than linkedin. That's a real signal.

## Anti-patterns

- ❌ "Just add it to the existing skill" — gets buried, no trigger matching
- ❌ Auto-promote on every failure — noise drowns signal
- ❌ 50-line gotchas with full code blocks — defeats the 5-line purpose
- ❌ Triggering on EVERY file in a directory — use specific globs
- ❌ No `why` field — the symptom and fix can be re-derived; the why can't
