---
name: spec-audit
description: "Audit a design spec (GDD, PRD, spec doc) against actual codebase implementation. Verifies every claim in the spec against real code, flags contradictions, identifies gaps, and produces an updated spec that is ground-truthed against the codebase. Trigger when asked to 'review GDD', 'audit spec', 'verify spec against code', 'spec review', 'check spec accuracy', or when given a large reference document to integrate into an existing spec."
---

# Spec Audit — Ground-Truth Design Docs Against Code

Audit a design specification against the actual codebase to find contradictions, false claims, missing features, and undocumented behavior. Produces an updated spec where every claim is verified against real code.

## When to Activate

- User asks to review, audit, or verify a GDD/PRD/spec document
- User provides a reference document (e.g., real game manual, competitor spec) to integrate
- Spec claims don't match observed behavior
- Before a major implementation sprint, to get the spec honest

## Core Principle

**Every claim in the spec must be traceable to code.** If the spec says "X works" but the code doesn't implement X, the spec is wrong — not the code (unless the spec is the agreed-upon target and the code is behind). Resolve the contradiction explicitly: either update the spec to match reality, or mark the gap as a known pending item.

## Workflow

### Phase 1: Ingest

1. Read the spec document completely.
2. Read any reference material the user provided (manuals, competitor docs, wikis).
3. Build a mental model of the spec's claims — list every testable assertion.

### Phase 2: Codebase Survey

Before auditing individual claims, survey the codebase structure:

1. **Map the architecture** — what files/modules exist, what's the tech stack.
2. **Identify key files** — for each major system (combat, cities, units, AI, map gen, etc.), find the primary implementation file.
3. **Note the data model** — enums, interfaces, type definitions. These are the ground truth for what features exist.

Use `search_files` with targeted patterns to find implementation of each spec claim. Use `read_file` to verify specifics.

### Phase 3: Claim-by-Claim Verification

For each testable claim in the spec:

1. **Search** for the relevant code (grep for function names, type names, string literals).
2. **Read** the implementation to verify behavior.
3. **Classify** the result:
   - ✅ **Implemented** — code matches the spec claim.
   - ⚠️ **Partial** — code implements something similar but differs in details (note the difference).
   - ❌ **Not implemented** — code doesn't exist or does something different.
   - 🔴 **Contradiction** — spec says X, code does Y, and both are clearly intentional.

### Phase 4: Gap Analysis

After verifying all claims, identify:

1. **Spec falsehoods** — claims that contradict the code. These must be fixed in the spec.
2. **Missing spec items** — implemented features the spec doesn't mention. Add them.
3. **Aspirational spec items** — spec describes something not yet implemented. Mark clearly as "not yet implemented" with a gap list entry.
4. **Reference doc → spec deltas** — when integrating a reference document, identify which parts are already in the spec, which are new, and which conflict.

### Phase 5: Rewrite

Produce the updated spec with:

1. **Accurate descriptions** — every claim now traceable to code.
2. **Implemented markers** — each section notes what's implemented vs pending.
3. **Consolidated gap list** — a single, deduplicated list of everything not yet implemented, organized by category.
4. **No contradictions** — if the spec and code disagree, the spec now reflects reality (or explicitly marks the gap as the target to implement).

## Output Format

For the updated spec document:

- Keep the original structure where possible — update in full, don't just append notes.
- Use `✅ Implemented` / `❌ Not implemented` / `⚠️ Partial` markers on sections.
- The gap list at the end should be a flat checklist organized by system (Combat, Units, Cities, etc.).
- When a spec section described something aspirational that conflicts with code, **rewrite the section to describe what the code actually does**, then add a gap entry for the aspirational target.

## User Workflow Preference

When the user provides a large reference document (game manual, competitor spec, wiki), they want **thorough integration** — not a summary, not a surface-level comparison. They expect:
- Every section of the reference doc read and audited against the codebase
- Specific line numbers cited for every claim verification
- A fully updated spec document (not a separate audit report)
- Gaps organized by system, not as a flat brainstorm list

## Anti-Patterns

- **Don't trust the spec** — even if it says "verified from game code", verify it yourself.
- **Don't trust the code comments** — they may be aspirational too. Verify the actual logic.
- **Don't preserve contradictions** — if spec §4.2 says "×4 wall bonus" and the gap list says "no wall bonus", resolve it. One of them is wrong.
- **Don't skip the reference doc** — if the user gave you a 50-page game manual, read every section. The value is in the details they didn't know to ask about.
- **Don't be shallow** — "combat works" is not enough. Check the exact formula, the edge cases, the skill interactions.

## Tool Strategy

- `search_files` with `target: 'content'` for finding implementations of specific features.
- `read_file` for verifying exact logic (damage formulas, stat tables, etc.).
- `execute_code` for running quick checks against the codebase (e.g., "what techs exist in TECH_DEFS?").
- `terminal` with `grep -r` for broad searches when `search_files` isn't enough.

## Lessons Learned

### Resolving Contradictions Between Spec, Code, and Gap List

The most common pattern: the spec describes something as implemented, the gap list says it's not implemented, and the code does something different from both. Resolution process:
1. **Trust the code** — read the actual implementation, not comments
2. **Fix the spec** to describe what the code actually does
3. **Fix the gap list** — remove false gaps, add real ones
4. **Never leave a contradiction** — if spec §X says "Y works" and gap list says "no Y", one must change

### When the User Provides a Large Reference Document

The user wants **thorough integration**, not a summary. Process:
1. Read the entire reference doc section by section
2. For each section, audit against the codebase (search → read → classify)
3. Integrate the reference material into the spec as the target
4. Mark each section with ✅/❌/⚠️ status
5. Produce a consolidated gap list organized by system

### Codebase Survey First, Then Audit

Don't audit claims in isolation. First survey the codebase architecture:
- Map all files/modules and their responsibilities
- Identify key data model files (enums, interfaces) — these are ground truth for what features exist
- Then verify individual claims against the relevant implementation files

### Common Verification Patterns

- **Formulas**: Read the exact code, trace variable names. Don't trust spec variable names matching code variable names — verify the actual computation.
- **Tables** (unit stats, tech trees, building defs): Cross-reference every row against the code's data structures. Missing rows = gaps.
- **Enums**: If the spec lists 7 map types but the enum has 4, that's a gap. If the enum has entries the spec doesn't mention, the spec is incomplete.
- **Skills/abilities**: Search for the skill name in code. If it doesn't appear, it's not implemented — regardless of what the spec claims.

## Session-Specific Notes

See `references/polytopia-gdd-audit-2026-06-15.md` for the detailed audit trail from the Polytopia Clone GDD review session.
