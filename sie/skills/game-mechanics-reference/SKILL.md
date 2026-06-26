---
name: game-mechanics-reference
description: Workflow for gathering, verifying, and embedding external documentation for game mechanics in 4X/hex-grid strategy games
category: game-development
---

# Game Mechanics Reference Skill

This skill provides a reusable workflow for gathering, verifying, and embedding external documentation for game mechanics (e.g., unit spawning, city borders, building placement). It is intended for use when expanding or polishing a 4X/hex‑grid strategy game such as Polytopia.

## When to use
- Adding or revising mechanics that lack in‑project documentation.
- Verifying that a mechanic matches an external source (wiki, rulebook, design doc).
- Building or updating a living spec (Spec.md) with concise, citable references.

## Core steps
1. Identify the mechanic(s) needing documentation.
2. Locate authoritative external sources (official wiki, design docs, community guides, rulebooks).
3. Extract concise bullet points or diagrams that capture the rule.
4. Record the source URL and version in a `references/<topic>.md` file.
5. Add the extracted points to the project’s `Spec.md` or relevant module, citing the reference.
6. Run the project’s test suite to confirm behavior aligns with the documented rule.

## Pitfalls & Mitigations
- **Out‑of‑date sources** – verify the page’s last‑updated timestamp; prefer PDFs or printed rulebooks for stable rules.
- **Over‑reliance on videos** – use video only for visual examples; always supplement with written description.
- **Ambiguous wording** – copy the exact phrasing from the source; avoid paraphrasing unless you add a clarifying note.
Version drift – note the source version e.g. Polytopia Wiki - 2024-06-15 in the reference file
- False-Positive Test Suites – a passing test suite does not guarantee a mechanic is implemented if the tests do not cover that specific logic. Always search the source code for the implementation logic (e.g., searching for 'spawn' or 'border' in the src folder) and cross-reference with the GDD, even if npm run test is green

## Supported file layout
- `references/<topic>.md` – concise reference for each mechanic (e.g., `unit-spawn.md`, `city-border.md`).
- `templates/spec-entry.md` – starter template for a spec entry (includes title, mechanic description, bullet list, reference link).
- `scripts/extract-reference.sh` – optional helper script to pull a URL and output markdown (uses `curl` + `pandoc`).

## Example
`references/unit-spawn.md`:
```
# Unit Spawn Turn Restriction
- Units cannot move on the turn they are created.
- This rule is present in the Polytopia rulebook (PDF, 2023) and reproduced in the Open‑Age design patterns doc.
- Source: https://opengameart.org/content/turn‑based‑strategy‑design‑patterns (section “Unit spawn cooldown”).
```

## Integration
- Add a `## External References` section to `Spec.md` for each mechanic.
- Use `skill_view(game-mechanics-reference)` to load this skill and its support files.

## Related Files
- `references/polytopia-clone-investigation.md` – Case study: false-positive test suite masking missing mechanics in a Polytopia clone.