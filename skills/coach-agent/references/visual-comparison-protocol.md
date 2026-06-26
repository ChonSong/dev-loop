# Visual Comparison Protocol

The Coach is responsible for comparing the deployed clone against reference screenshots of the original GTO Wizard. The Player does NOT do comparison — that's the Coach's validation role.

## Architecture

```
Coach → loads reference via vision_analyze
      → loads live page via browser_vision
      → compares systematically using checklist
      → generates gap-fix tasks in AGENTS.md
      → commits + pushes

Player → picks next generated gap-fix task
       → implements one fix per tick
       → commits + pushes

Coach → loads reference again
      → verifies the specific gap is closed
      → APPROVE / FIX / REVERT
```

## When to Do This

**Every cycle as Step 1** — the comparison is delegated to a foreground subagent as the FIRST action of the review protocol, before commit review. See the `FIRST-STEP` section in the parent SKILL.md.

This ensures the comparison always gets its own execution budget and is never deferred due to time pressure from commit review.

**Additional triggers** (beyond the mandatory Step 1):
- After major structural changes to a page (e.g., stripping quiz flow)
- When the user explicitly requests visual polish
- When a reference screenshot is newly added to `docs/`

## Required Tools

| Tool | What For |
|------|----------|
| `vision_analyze(reference)` | Load `docs/reference-<page>.png` to understand target design |
| `browser_navigate(live_url)` | Navigate to deployed clone |
| `browser_vision(question)` | Capture current state of clone for comparison |
| `browser_console(expression)` | Read DOM metrics, grid data, or frequencies |

## Checklist Template

```markdown
### Comparing {page} against {reference}

1. **Hand matrix** — 13×13 grid cells: color coding, font sizes, hover states, cell spacing
2. **Position buttons** — active position highlight, stack labels, action prompts
3. **Stack depth selector** — pill buttons, active state styling
4. **Right sidebar** — styled suits, combo grid, color coding
5. **Typography & spacing** — font sizes, padding, density matching reference
6. **GTO frequency display** — chips/badges on cells, % format
```

## How to Diff

Compare reference vs live descriptions section by section. Use a table for clear gap identification:

| Section | Reference | Live | Gap |
|---------|-----------|------|-----|
| Board cards | Styled playing cards, centered | Cards present, same colors | Match |
| Action buttons | "BET 1.8 (33%)" with GTO freq chip | "BET 33%: 2.0 (36%)" no GTO chip | Missing frequency display |
| Post-action feedback | Comparison overlay with EV diff | Nothing happens after click | Missing feature |
| Cell colors | Red=Raise, Blue=Call, Gray=Fold | Red=Raise, Gray=Fold, no Blue | Missing Call color |

The table format forces specificity — you can't write "looks different" in a row. Each row has a specific gap or says "Match".

## Output Format

For each gap found, generate a task entry like:

```markdown
### Task: fix-{specific-issue}
- **Description**: Reference shows X but clone shows Y. Specific delta.
- **Location**: File + line if known
- **Success criteria**: Verifiable condition for closure
- **Coach checks**: How Coach will verify the fix
```

Number each gap task and add them to the active AGENTS.md task list above the deferred section. Each gap = one Player tick.

## Pitfalls

1. **Loading order matters** — Always `vision_analyze` the reference FIRST, then `browser_navigate` the live page. The reference image stays in context for comparison.
2. **Be specific** — "Matrix cell font is too small" is not a task. "Matrix cell font is 10px in clone, reference shows 12px. Update `.study-matrix-cell` font-size to 12px." is a task.
3. **One gap per commit** — Each visual fix should be its own commit so Coach can verify individually.
4. **Don't generate more tasks than needed** — Aim for 2-5 gap tasks per comparison pass. More than that and the Player's backlog stalls.
5. **Reference screenshots can be stale** — If the original site changed after the screenshot was taken, comparing against it will produce fake gaps. When the original is accessible (not login-walled, or via Tandem browser), verify the reference screenshot still matches current original behavior before using it as ground truth. If the original is inaccessible, flag each gap with "unverified against current original — screenshot from [date]".
6. **Vision description drift** — The same reference image described twice may produce slightly different descriptions from vision_analyze. Cross-reference between descriptions rather than relying on a single pass.
7. **Structural differences are not gaps** — If the clone uses a position bar instead of position columns, that's a different layout approach, not necessarily a gap. Flag only missing *functional* visual elements: absent buttons, wrong colors on interactive elements, missing feedback states.
8. **Game variant mismatch** — The reference may show a heads-up scenario while the clone renders 6-max. This is an architectural choice, not a visual gap — unless the task specifically asks for heads-up.

> **This protocol handles *visual* parity (pixel-level matching). For *interaction* parity (does the app behave the same when you click things?), see `references/interaction-workflow-qa.md`.** The two protocols are complementary — run both. Interaction gaps (missing features, broken workflows) outrank visual gaps (wrong colors, spacing).
