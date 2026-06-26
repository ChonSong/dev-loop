---
name: product-lens
description: Validate the "why" before building. Product diagnostics, feature prioritization (ICE scoring), and user journey audits. Pressure-test direction before implementation.
origin: ECC (adapted for Hermes)
---

# Product Lens — Think Before You Build

Owns product diagnosis, not implementation specs. Validates the "why" before the request becomes code.

## When to Activate

- Before starting any feature — validate the "why"
- When stuck choosing between features
- Before a launch — sanity check the user journey
- Converting a vague idea into a product brief

## Mode 1: Product Diagnostic

Like YC office hours but automated. Ask:

1. **Who is this for?** (specific person, not "developers")
2. **What's the pain?** (quantify: how often, how bad, what do they do today?)
3. **Why now?** (what changed that makes this possible/necessary?)
4. **What's the 10-star version?** (if money/time were unlimited)
5. **What's the MVP?** (smallest thing that proves the thesis)
6. **What's the anti-goal?** (what are you explicitly NOT building?)
7. **How do you know it's working?** (metric, not vibes)

Output: go/no-go recommendation. If "yes, build this" → next lane is implementation planning.

## Mode 2: Feature Prioritization (ICE Score)

When choosing between features:

1. List all candidate features
2. Score each: **Impact (1-5) × Confidence (1-5) ÷ Effort (1-5)**
3. Rank by ICE score
4. Apply constraints: runway, dependencies
5. Output: prioritized list with rationale

## Mode 3: User Journey Audit

1. Map the actual user experience end-to-end
2. Document every friction point
3. Time each step
4. Score: time-to-value (how long until first win?)
5. Recommend: top 3 fixes for onboarding

## Mode 4: Founder Review

Review current project through a founder lens:

1. **Read the docs first** — SPEC.md, PLAN.md, recent commits, MIGRATION.md
2. **Infer the thesis** — what is this trying to be?
3. **Score product-market fit signals (0-10)**
   - Usage growth trajectory
   - Retention indicators
   - Revenue signals
   - Competitive moat
4. **Identify** the one thing that would 10x this
5. **Flag** things being built that don't matter

**Output template:**

```
## Founder Review: [Project Name]

### Thesis
What it claims to be + what it's actually trying to achieve.

### Score: X/10
Breakdown by dimension (use, retention, revenue, moat).

### What's Working
Concrete evidence from this session.

### What's Broken / Missing
Specific gaps, not vague complaints.

### The One Thing
The single change that would have the most impact.

### What to Kill
Explicit list of features/tiles/requirements that are noise.

### Verdict
GO / NO-GO / PIVOT with one-line rationale.
```

### Example Output (hermes-web-computer review, 2026-05-14)

```
## Founder Review: hermes-web-computer

### Thesis
Browser-native tiled AI desktop for human+agent collaboration. "Lean by default" — no CRDTs, no VDOM diffing, backend owns truth.

### Score: 5/10
- Use: Zero external users confirmed; dev is self-hosting
- Moat: 8.5K lines but no unique IP — tiling window managers exist
- Differentiation: Shift+Space interrupt + single-wire WS multiplexer is novel
- Risk: 3 repos in confusion (HWC, agent-os, planning), SPEC was in wrong repo

### What's Working
- PTY + WS multiplexer functional
- Migration from agent-os documented
- SPEC.md v2.0 has realistic non-goals + MVP scope

### What's Broken
- Metrics in v1.3 SPEC were fictional (<5MB RSS, <50KB bundle)
- Tiered security vague (no implementation spec for AST enforcement)
- "Collaborative multi-agent" but no multi-user protocol defined
- Voice integration planned but unimplemented — no audio subprocess management

### The One Thing
Fix the SPEC metrics (make them honest) and define MVP scope. The spec's v1.3 numbers were promises that couldn't be kept.

### What to Kill
- MCP adapter (v2+ only, not MVP)
- H.265 streaming (WS binary frames sufficient)
- Cross-platform (Linux first)
- Fun-Audio-Chat (defer to v2)

### Verdict
GO — but with honest metrics and scoped MVP. The lean philosophy is right; the fiction was in the numbers.
```

## Hermes Adaptation

- Use `clarify` to ask the diagnostic questions when needed
- Output findings as markdown to `docs/` directory
- For Sean's projects: be direct, skip the filler, focus on actionable insights
- When Sean says "just build it" — skip this skill and proceed
