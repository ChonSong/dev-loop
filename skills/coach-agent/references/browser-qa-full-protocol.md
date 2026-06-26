# Browser QA — Full Protocol

**Loaded on-demand by subagents.** This file documents the complete browser QA protocol that the Coach delegates to subagents. The parent Coach only needs the decision framework — subagents execute this protocol and return results.

## Core Principle

**A review that did not load the page in a browser and interact with it is not a valid review.**

The coach exists to catch what code review and static analysis cannot — broken UI, unresponsive buttons, console errors, visual regressions, input dead zones, missing features. Code can look perfect and the site can still be broken or unusable.

## Core Workflow Testing Directive

Every review must embody the application's primary user workflow end-to-end. Loading a page and clicking one button is not sufficient — the coach only adds value by discovering what static analysis cannot: broken interactions, dead UI paths, missing state transitions, and functional regressions.

### Step 1: Discover the Core Workflow

Load the deployed app and identify its primary user flow — the sequence of interactions a user performs to accomplish the app's purpose.

Ask: "What is the one thing this app does? What steps does a user go through to do it?"

Examples:
- **Polytopia clone**: Select tribe → start game → end turn → open city → build unit → advance turns
- **GTO Wizard**: Select game variant → choose position → review preflop ranges → take action → proceeds to next action until river showdown or all positions folded
- **Equity calculator**: Input hand ranges → input board → calculate → review results

**Do NOT guess** — discover by interacting:
1. `browser_navigate` to the deployed URL
2. Read the DOM snapshot — what buttons, links, and controls exist?
3. Click through the navigation — what pages/routes are available?
4. Based on what you see, identify the primary user flow (1-5 interactions)

### Step 2: Execute the Full Workflow

For each step in the identified workflow:

1. Perform the interaction
2. Check for errors: 
   - Any `error` level message is 🔴 CRITICAL — record it
   - Any `warn` level message is 🟡 NOTE — record it
3. Verify state change: Did the interaction produce the expected result?
   - Did the page transition? Did a new element appear? Did state update?
4. **If an interaction fails** (click does nothing, page doesn't update, console errors, broken UI):
   - **This is a FINDING** — do NOT silently pass it
   - Record what you tried, what happened, and what was expected
   - This is exactly the kind of bug code review misses

### Step 3: Complete the Full Sequence

Do not stop after the first successful interaction. Complete the entire primary workflow. Only when you've exercised the full flow can you assess whether the app actually works.

### Step 4: Report What You Actually Did

Use the "Accurate Reporting" rules. List:
- Each interaction performed
- Console state after each
- What worked and what broke
- The final verdict on the core workflow

## Workflow Test Protocol (MANDATORY)

Loading pages and checking console is necessary but NOT sufficient. For any app with an interactive core loop, you MUST execute a state-changing interaction sequence.

**Minimum 3 interactions that change application state** (not page loads). For each:
1. Perform the interaction (click button, select option, submit form)
2. Verify the expected state change (new data appears, element updates, feedback renders)
3. Record the result — "Clicked X, expected Y, got Z"
4. **If an interaction does nothing, that is a FINDING** — do not silently pass it

**Console check AFTER interactions**, not just after page load.

## Live Site Browser Check (Every Review)

1. `browser_navigate(url)` — load deployed page
2. `browser_console(clear=true)` — check JS errors
3. For visual-match tasks: `browser_vision` on clone, `vision_analyze` on reference
4. `browser_snapshot` to verify key elements
5. For canvas games: `document.querySelector('canvas')` — verify exists and has content

To skip browser_vision: non-visual task only, no deployed URL, or site confirmed down.

**Tandem for reference comparison**: If project has `reference_url` in .checkpoint.json and the reference is login-walled (GTO Wizard), use Tandem viewer at localhost:3099. The viewer now correctly targets the webview (fixed 2026-06-23). Check availability: `curl -s --connect-timeout 3 http://localhost:3099/info`. Navigate: POST `/navigate`, evaluate: POST `/evaluate`, click: POST `/click`. Screenshot is degraded under `--disable-gpu` — use Hermes `browser_vision` for visual capture. If Tandem is down or reference is unreachable, fall back to static reference images in `docs/`.

## Run Tests (Three Layers)

Run the project's test suite — do NOT trust Player's assertion. Run ALL three:

```bash
# Layer 1: API tests (backend business logic)
cd apps/api && uv run pytest -q --tb=short

# Layer 2: Frontend unit tests (component rendering)
cd apps/web && npx vitest run --reporter=verbose

# Layer 3: E2E browser tests (full user workflows via Playwright POM)
cd apps/web && npm run test:e2e 2>&1 | tail -30
```

**E2E test results are MANDATORY evidence.** Record:
- Number of tests passed/failed
- If failed: is it a known bug or a new regression?
- If new regression: escalate to FIX or REVERT

## Structured QA Infrastructure (POM + Executable Specs)

For the GTO Wizard project, Page Object Models and executable Playwright test specs make browser QA reliable and repeatable:

| File | Purpose |
|------|---------|
| `apps/web/e2e/pages/StudyPage.ts` | POM with stable `aria-label` selectors |
| `apps/web/e2e/study.spec.ts` | Executable Playwright spec: preflop/postflop/full-hand workflows |

**Use `aria-label` selectors** — NOT CSS class names or unstable refs. For Practice page (no aria attributes), use text content + section visibility instead.

**Run generated specs directly:**
```bash
cd apps/web && npm run test:e2e -- e2e/study.spec.ts
cd apps/web && npm run test:e2e -- e2e/practice.spec.ts
```

### GTO Wizard Study Page — Mandatory Workflow Test Sequence

```
1. browser_navigate("/study") + console check
2. Click position button (BTN via aria-label "BTN position, 100bb stack") → verify matrix updates
3. Switch to postflop mode → click "Get GTO Strategy" → verify action buttons render
4. Run JS assertion: do GTO frequencies sum to ~100%? (regex: /(\d+)\s*(percent|%)/)
5. Click action button → verify feedback/changed state
6. Check console for errors
```

If any step fails, record it as a finding.

### Selectors Reference

| Element | `aria-label` |
|---------|-------------|
| Position cards | `"{POS} position, {stack}bb stack"` or `"... active"` |
| Mode toggle | `"Preflop ranges mode"`, `"Postflop training mode"` |
| Stack depth | `"{N}bb stack depth"` or `"... selected"` |
| Get GTO Strategy | `"Get GTO strategy"` |
| Action buttons | `"CHECK"`, `"BET 33%"`, `"CALL"`, `"FOLD"`, `"RAISE 50%"`, `"ALL IN 100.0"` |
| Street navigation | `"Street navigation"` |

GTO action button text format: `"BET 33%2.0 (36%)"` where `36%` is shown frequency.
Regex for frequency extraction: `/(\d+)\s*(percent|%)/`

## Canvas / Game-Specific Notes

Canvas games (Phaser, WebGL, Pixi) have zero DOM elements. Load the **`polytopia-game-qa`** skill for the full canvas testing protocol: state reads via `__PHASER_GAME__`, Phaser `emit()` interactions, vision verification. Summary: use `handleClick` with screen coordinates as the most reliable fallback, `browser_vision` to verify rendering, and game-state reads via `browser_console` for precise assertions.

If `polytopia-game-qa` isn't installed for the target canvas app, file a task to create it before reviewing the project.

## Timing and Scope

- **Time budget**: 60s for workflow discovery + execution (prioritize first 3 steps if 5+)
- **Active project**: Test primary workflow every review cycle.
- **If primary workflow is BROKEN by the current commit**: 🔴 CRITICAL — do not approve, issue REVERT.
- **If primary workflow was already broken before this commit** (pre-existing blocker): See **Persistent Blocker Escalation** in `references/persistent-blocker-escalation.md`. Do NOT silently skip browser QA.
- **Cross-project fallback (mandatory)**: When the active project's deployed URL is down or non-functional, you MUST pick another active project from the master checkpoint and run full browser QA on it. If no other project has a functional URL, run the project's local test suite (API + frontend + E2E). Report which fallback you used.
- **Completed projects**: if no unreviewed work, pick one completed project for regression QA (stale >24h).
- **Skip browser** only if: non-UI commit AND all projects' deployed URLs are down (verify each).
- **If `browser_navigate` fails**: cron may lack `"browser"` toolset. Fall back to curl + web_extract for HTTP checks.

## Persistent Blocker Escalation (Summary)

When the same deployed site failure (502/500/timeout) persists across multiple review cycles, the blocker becomes **normalised** — Coach stops treating it as urgent. See `references/persistent-blocker-escalation.md` for the full protocol.

**Minimum actions at every cycle while a blocker persists:**
1. Check AGENTS.md — does an unaddressed task for the blocker exist? If not, create one.
2. Run cross-project fallback QA (mandatory, not optional).
3. If the blocker has survived 3+ cycles without progress: escalate to REVERT on the next commit that touches related code paths, and seed an SIE learning under `persistent-blocker-not-escalated`.
4. State clearly in the verdict: "⚠️ Persistent blocker (N cycles): [URL] returns [status]. No progress this cycle."

## Accurate Reporting

Name the specific tools called and what they returned. NOT "Coach verified the site" — instead "Coach delegated browser QA to subagent which loaded /study via browser_navigate, checked console (0 errors), read DOM snapshot."
