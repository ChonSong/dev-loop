---
name: ui-refactoring-pipeline
description: When the user prefers to generate UIs via external tools (meta.ai, Muse Spark, etc.) and have you refactor the raw HTML into proper framework components. You identify what UI is needed, craft the prompt for the user, accept their pasted HTML, then refactor and integrate.
---

# UI Refactoring Pipeline

When the user lacks confidence in your raw UI generation ability, or explicitly prefers to use an external tool (meta.ai, Muse Spark when it gets an API, etc.) for UI generation, use this workflow.

## When to Trigger

- User says they don't trust your UI generation
- User mentions meta.ai, Muse Spark, or another external generation tool
- User provides raw HTML and asks you to integrate it into the project
- The frontend framework is complex (Next.js/React/Tailwind) and the UI needs polished visuals
- You're working on a visual component and realize your raw output would be mediocre — ask proactively

## Workflow

### 1. Identify the UI need

Know exactly what component you need before interrupting:
- What page / route does it live on?
- What data does it display (API endpoints, shape)?
- What interactions (click, hover, submit)?
- What framework conventions (Tailwind classes, shadcn/ui, CSS modules)?

### 2. Craft the prompt for the user

Give a **specific, copy-pasteable prompt** they can paste into meta.ai:

> **🔴 UI GENERATION NEEDED**
>
> I need a `<component name>` for the `<page>` page.
> Go to meta.ai and paste:
> ```
> "Create a dark-themed [specific description] with [key features]. Include [specific elements]."
> ```
> Paste the raw HTML output back here and I'll convert it into a proper React component.

**DO** specify: colors (dark theme), layout, key interactive elements, data display format.
**DON'T** ask the user to tweak the prompt or regenerate — accept the first output.

### 3. Receive the HTML

When the user pastes HTML back, do NOT:
- Ask follow-up questions about the output
- Ask them to regenerate with changes
- Complain about the quality

Just accept it and start refactoring.

### 4. Refactor into framework components

Take the raw HTML and convert it:

1. **Split into components** — identify container, presentational, and hook concerns
2. **Convert styles** — rewrite inline styles / class names to the project's convention (Tailwind, CSS modules, styled-components)
3. **Extract data dependencies** — identify every piece of mock data and plan the API binding
4. **Add proper states:**
   - Loading (skeleton/spinner)
   - Empty (helpful message)
   - Error (retry + message)
   - Edge cases (null, empty array, boundary values)
5. **Wire to real API** — import the fetch/query hook, replace mock data, add error boundaries
6. **Ensure accessibility** — roles, labels, keyboard navigation, focus management

### 5. Commit

- Include the generated component(s), API integration, and any new route
- Do NOT include the raw HTML the user pasted (it's the input, not the artifact)
- One-line pointer in commit body to what the external generation produced

## Pitfalls

- **Don't adapt, convert.** The generated HTML will use different conventions — rewrite it into the project's framework, don't patch around it.
- **Expect flat HTML.** External tools produce flat markup. Your job is to split it into logical React components.
- **Mock data is expected.** The generated HTML will have hardcoded demo data — replace it all, don't preserve any of it.
- **Unusable output.** If the HTML is script-based, uses unsupported libraries, or is clearly broken, say so immediately: "This won't work as-is because [reason]. Try this prompt instead:" — craft a more specific prompt and ask them to regenerate.
- **Don't redesign at generation time.** The user wants the external tool's aesthetic. Refactor for correctness and integration, not for visual redesign (unless they ask).
- **Don't ask the user to do CSS tweaks.** Every style change you can make in the codebase is faster than a round-trip through external generation.
