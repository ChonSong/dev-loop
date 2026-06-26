# Interaction & Workflow Meta-Analysis

**Purpose:** Compare the original application's interaction model and user workflows against the clone — not just pixels, but what the app *does* and what a user can *accomplish*.

**Golden rule: The original site is the source of truth, not local docs.** Any interaction spec, screenshot, or doc in `docs/` may contain LLM hallucinations or be out of date. Verify everything against the real original before trusting it.

## When to Do This

- The project has an interaction spec or reference screenshots (e.g., `docs/reference-study-interaction-spec.md`)
- The project has a `reference_url` in its checkpoint (e.g., `app.gtowizard.com`)
- After major architectural changes to a page
- Before generating new feature tasks
- During backlog health check when tasks are running low

## Workflow vs Visual Comparison

| Visual Comparison (Step 1) | Interaction Meta-Analysis (Step 6) |
|-----------------------------------|--------------------------------------|
| Are the buttons the right color? | What does clicking a button *do*? |
| Is the matrix 13×13? | How does the matrix change when you select a position? |
| Are font sizes matching? | What sub-tabs exist and what content do they show? |
| Is spacing correct? | What happens when you click a hand cell? |
| Do colors match the reference? | Can a user complete the configure→study→practice workflow? |

## Meta-Analysis Protocol

### Phase 1: Check the Original Site (Primary Source)

**Do NOT start by reading local docs.** Go to the original application and document what it actually does.

If the original is publicly accessible:
```python
browser_navigate("https://app.gtowizard.com/study")
```
Document: page structure, what's interactive, what happens on each click.

If the original is login-walled (GTO Wizard):
- Use the Tandem browser at **localhost:3099** which has an authenticated session
- Navigate to each page and document behavior
- See `shared-browser-automation` skill or `Tandem browser via localhost:3099` memory for setup

**What to capture** from each page of the original:

1. **Page zones** — What are the main layout zones? (top bar, spot cards, matrix, sidebar, etc.)
2. **Component states** — What states does each component have? (active, minimized, selected, disabled)
3. **Interaction triggers** — What user actions trigger changes? (click position, click cell, switch tab, hover)
4. **State transitions** — What happens when each trigger fires? Be specific: "clicking UTG causes the matrix to reload with UTG ranges AND the right sidebar position stats to update"
5. **Information flow** — What data moves between components? (selected position → matrix → sidebar)
6. **Full workflows** — What complete user journeys exists? (landing → configure → study → practice)

### Phase 2: Map Clone's Actual Behavior

Delegate a subagent to walk through the same workflows on the live clone and document what actually happens:

```python
delegate_task(
    goal="Work through each interaction flow on the live clone at {live_url}. "
         "For each page zone and interaction trigger documented from the original, "
         "test the same action on the clone and report: "
         "(1) what the original does, "
         "(2) what the clone actually does, "
         "(3) whether they match or differ. "
         "Be specific — capture console errors, missing state changes, and dead ends.",
    context=f"Live URL: {live_url}. Project: {project}. "
            f"The original behavior was documented from the live original site.",
    toolsets=["browser", "web", "file"],
)
```

### Phase 3: Compare and Classify Gaps

For each difference found, classify:

| Type | Example | Severity |
|------|---------|----------|
| **Missing interaction** | Clicking a hand cell does something on the original but nothing on the clone | HIGH |
| **Broken workflow** | "Advance to Turn" button exists but does nothing | HIGH |
| **Missing component** | Original has 9 right sidebar sub-tabs, clone has 0 | HIGH |
| **State mismatch** | Original loads with HJ active, clone loads with UTG active | MEDIUM |
| **Incomplete data** | Tab opens but shows placeholder/empty content | MEDIUM |
| **Different behavior** | Position selector works differently than original | LOW |

### Phase 4: Generate Workflow Tasks

Each gap becomes an AGENTS.md task with:
- **What the original does** (cite specific observed behavior)
- **What the clone does instead**
- **Success criteria** (verifiable interaction — not "looks like" but "click X → Y happens")
- **Coach checks** (click-through workflow to verify)

```markdown
### Task: fix-position-active-on-load
- **Description**: Original loads /study with HJ as the active (acting) position.
  Clone loads with UTG active. Change the default active position to HJ.
- **Success criteria**:
  - Loading /study shows HJ as the acting position (highlighted card, "Take action" prompt)
  - Matrix initially shows HJ ranges, not UTG ranges
- **Coach checks**:
  - Load /study, check which position card has the active/highlighted state
  - Verify matrix shows HJ ranges (frequency data matches HJ's expected range)
  - Load original via Tandem — verify same behavior
```

Do NOT generate tasks based on assumptions or unverified docs. Every task must cite observed original behavior as evidence.

### Phase 5: Capture Screenshots for Evidence

When documenting original behavior, also capture screenshots:
```python
browser_vision(question="Capture a full-page screenshot of the original study page showing the default state")
```
These serve as evidence for gap descriptions and success criteria. Store references in the task description, not as requirements to match exactly — interaction behavior is the priority.

## Accessing the Original (Login-Walled Sites)

For GTO Wizard at `app.gtowizard.com`:
1. Tandem browser must be running on localhost:3099 with an authenticated session
2. Reference: `shared-browser-automation` skill, or `tandem-browser-start` skill
3. If Tandem is not available, fall back to the `docs/` interaction spec BUT flag each claim as unverified
4. Document in the verdict: "Verified against original via Tandem" or "Using unchecked docs — original inaccessible"

## What Not To Do

- **Don't generate tasks from unverified docs** — If you read a requirement from `docs/reference-study-interaction-spec.md` that you didn't verify against the original, say so. Hallucinated requirements waste Player ticks.
- **Don't assume the docs are correct** — The interaction spec may have been written by an LLM that inferred behavior from screenshots. Screenshots don't show animations, hover states, click responses, or state transitions.
- **Don't skip this for login-walled sites** — "It's behind login" is not an excuse. Tandem exists for this purpose. If Tandem is down, fix Tandem first, then do the analysis.
- **Don't generate visual tasks here** — Visual gaps belong to the Step 1 visual comparison output. This step is about workflow and interaction behavior.
