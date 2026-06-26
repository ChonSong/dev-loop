# Skill Tree — Loading Decision Map

## How to use this file

When you land on a research/spec task, use this decision tree to determine which skills to load. **Start at the top, follow the branches, stop when you have enough.** Don't load everything — load what this specific task needs.

## Quick Reference

| # of skills | When | What |
|-------------|------|------|
| 1–2 | Quick task (single question, one artifact) | Just the specific skill |
| 3–5 | Standard task (research + one output) | Pipeline + 2–3 supporting |
| 6–8 | Complex task (full PRD with research) | Pipeline + full toolkit |
| 10+ | Only via subagent delegation | Load into subagent, not main context |

## Decision Tree

### A. "Should we build this? Is this the right direction?"

```
→ planning/product-lens (always load first for any product decision)
   → If competitive context needed → phuryn/competitor-analysis
   → If problem framing needed → deanpeters/problem-framing-canvas
   → If discovery needed → deanpeters/discovery-process
```

### B. "Research how [X] works / how competitors solve [problem]"

```
→ media/youtube-content (video research)
→ phuryn/competitor-analysis (structured competitive analysis)
→ coreyhaines31/competitor-profiling (sales-focused competitive intel)
→ If scraping competitor sites → firecrawl/firecrawl-build-search or firecrawl/firecrawl-build-scrape
```

### C. "Write a PRD / spec for [feature]"

```
→ phuryn/create-prd (8-section PRD template, fastest)
   OR
→ deanpeters/prd-development (8-phase workflow, most thorough)

Then load these IF the task needs them:
   → deanpeters/problem-statement — if problem framing is weak
   → deanpeters/proto-persona — if personas are unclear
   → deanpeters/customer-journey-map — if journey context matters
   → deanpeters/epic-hypothesis — if you need testable hypotheses
   → deanpeters/epic-breakdown-advisor — if splitting complex features
   → deanpeters/user-story or phuryn/user-stories — for acceptance criteria
   → deanpeters/user-story-splitting — if stories are too large
   → phuryn/prioritization-frameworks — if prioritizing features
   → phuryn/pre-mortem — if risk analysis needed
   → deanpeters/press-release — if using Amazon Working Backwards
   → deanpeters/positioning-statement — if GTM positioning matters
```

### D. "Design the interface / create wireframes / design spec"

```
→ google-labs-code/design-md (DESIGN.md creation)
→ google-labs-code/enhance-prompt (improve prompts with design vocab)
→ anthropics/frontend-design (UI/UX development tools)
→ anthropics/canvas-design (visual design)
→ anthropics/web-artifacts-builder (HTML artifacts with React/Tailwind)
→ google-labs-code/generate-design (translate layouts to Figma)
→ google-labs-code/code-to-design (code → Figma)
→ google-labs-code/manage-design-system (design system in Figma)
→ google-labs-code/taste-design (design taste/quality)
```

### E. "Analyze users / run user research"

```
→ coreyhaines31/customer-research (research methodology)
→ deanpeters/proto-persona (hypothesis-driven personas)
→ deanpeters/customer-journey-map (journey mapping)
→ deanpeters/customer-journey-mapping-workshop (guided workshop)
→ coreyhaines31/onboarding (onboarding CRO)
→ coreyhaines31/churn-prevention (churn analysis)
```

### F. "Plan the sprint / plan execution"

```
→ phuryn/sprint-plan (sprint planning with capacity + risk)
→ phuryn/stakeholder-map (power/interest grid)
→ deanpeters/user-story-mapping (visual story mapping)
→ deanpeters/user-story-mapping-workshop (facilitated mapping session)
→ phuryn/outcome-roadmap (outcome-focused roadmaps)
```

### G. "Run a retrospective / team process"

```
→ phuryn/retro (structured sprint retro)
→ phuryn/summarize-meeting (meeting notes → actions)
→ phuryn/brainstorm-okrs (OKR brainstorming)
→ deanpeters/workshop-facilitation (interactive session protocol)
```

### H. "Write tests / validate quality"

```
→ phuryn/test-scenarios (test scenarios from user stories)
→ phuryn/job-stories (JTBD-format stories)
→ phuryn/wwas (Why-What-Acceptance format)
```

### I. "Communicate the release / go-to-market"

```
→ phuryn/release-notes (user-facing release notes)
→ deanpeters/press-release (Amazon Working Backwards)
→ deanpeters/positioning-statement (Geoffrey Moore positioning)
→ coreyhaines31/growth-loops (growth loop identification)
→ coreyhaines31/launch-strategy (launch planning)
```

### J. "Analyze data / measure success"

```
→ coreyhaines31/analytics (analytics tracking setup)
→ coreyhaines31/ab-test-setup (A/B test design)
→ coreyhaines31/page-cro (page-level conversion optimization)
→ coreyhaines31/form-cro (form optimization)
→ deanpeters/saas-revenue-growth-metrics (SaaS metrics)
→ deanpeters/saas-economics-efficiency-metrics (unit economics)
→ deanpeters/finance-metrics-quickref (32+ metrics reference)
→ phuryn/dummy-data (generate test datasets)
```

### K. "Build a web artifact / interactive prototype"

```
→ anthropics/web-artifacts-builder (React + Tailwind HTML artifacts)
→ google-labs-code/react-components (Stitch → React)
→ google-labs-code/shadcn-ui (shadcn/ui components)
→ google-labs-code/remotion (video from React)
→ google-labs-code/extract-static-html (static HTML extraction)
```

### L. "Scrape / extract data from the web for research"

```
→ firecrawl/firecrawl-build-search (query-first discovery)
→ firecrawl/firecrawl-build-scrape (page extraction)
→ firecrawl/firecrawl-build-interact (interactive page automation)
→ firecrawl/firecrawl-build (general Firecrawl integration)
```

## Anti-Patterns

- **Don't load more than 8 skills in main context.** If you need more, delegate to a subagent.
- **Don't load a skill "just in case."** Load it when the task specifically needs it.
- **Don't load umbrella + specific.** If you load `ux-research-and-specs`, you don't also need to load `phuryn/create-prd` — the umbrella tells you when to pull the specific.
- **Don't load deprecated/stub skills.** Check file size — if < 500 bytes, it's probably a stub.
