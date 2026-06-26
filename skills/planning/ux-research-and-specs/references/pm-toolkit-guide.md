# PM Toolkit — Consolidated Skill Guide

## The Overlap Problem

`phuryn/pm-skills` (65 skills) and `deanpeters/Product-Manager-Skills` (46 skills) cover similar PM territory. Both have PRD skills, user stories, personas, etc. This guide tells you which to use when.

## Decision Matrix

| Task | Use This | Why |
|------|----------|-----|
| Write a PRD (fast) | `phuryn/create-prd` | 8-section template, fill-in-the-blank, ~3KB |
| Write a PRD (thorough) | `deanpeters/prd-development` | 8-phase workflow with examples, ~23KB, 60-120 min |
| Frame a problem | `deanpeters/problem-statement` | Empathy-driven: "I am/trying/but/because/feels" |
| Frame a problem (MITRE) | `deanpeters/problem-framing-canvas` | Look Inward, Outward, Reframe |
| Create personas | `deanpeters/proto-persona` | Hypothesis-driven, structured, evolves with research |
| Map customer journey | `deanpeters/customer-journey-map` | NNGroup framework, stages × touchpoints × emotions × KPIs |
| Facilitate journey mapping | `deanpeters/customer-journey-mapping-workshop` | Guided session protocol |
| Write user stories | `deanpeters/user-story` | Mike Cohn + Gherkin (Given/When/Then) |
| Write user stories (INVEST) | `phuryn/user-stories` | INVEST criteria + 3 C's (Card, Conversation, Confirmation) |
| Split large stories | `deanpeters/user-story-splitting` | 8 proven patterns (workflow, CRUD, business rules, etc.) |
| Map stories visually | `deanpeters/user-story-mapping` | Visual story mapping |
| Facilitate story mapping | `deanpeters/user-story-mapping-workshop` | Guided session protocol |
| Analyze competitors | `phuryn/competitor-analysis` | 5 competitors, structured profiles, differentiation opportunities |
| Profile competitors (sales) | `coreyhaines31/competitor-profiling` | Sales-ready battlecards |
| Prioritize features | `phuryn/prioritization-frameworks` | 9 frameworks, Opportunity Score recommended |
| Run a pre-mortem | `phuryn/pre-mortem` | Risk analysis on PRDs and launch plans |
| Create outcome roadmap | `phuryn/outcome-roadmap` | Transform output → outcome-focused strategic plans |
| Write release notes | `phuryn/release-notes` | User-facing release notes from tickets/changelogs |
| Create test scenarios | `phuryn/test-scenarios` | Comprehensive test scenarios from user stories |
| Write job stories | `phuryn/job-stories` | JTBD-format stories |
| Map stakeholders | `phuryn/stakeholder-map` | Power/interest grid + comms plan |
| Plan a sprint | `phuryn/sprint-plan` | Capacity, story selection, risk mapping |
| Run a retro | `phuryn/retro` | Structured sprint retro with action items |
| Summarize a meeting | `phuryn/summarize-meeting` | Transcript → structured notes + actions |
| Brainstorm OKRs | `phuryn/brainstorm-okrs` | Team OKRs aligned with company objectives |
| Amazon Working Backwards | `deanpeters/press-release` | Future press release to clarify vision |
| Positioning statement | `deanpeters/positioning-statement` | Geoffrey Moore framework |
| Feature investment | `deanpeters/feature-investment-advisor` | Prioritize feature investments |
| Facilitate workshops | `deanpeters/workshop-facilitation` | Interactive session protocol |
| CRO (conversion) | `coreyhaines31/cro` | Conversion rate optimization |
| Onboarding optimization | `coreyhaines31/onboarding` | Post-signup onboarding CRO |
| Customer research | `coreyhaines31/customer-research` | Analyze existing OR go find (Reddit/G2/forums) |
| Design specs | `google-labs-code/design-md` | DESIGN.md for design systems |
| Design-to-code | `google-labs-code/code-to-design` | Code → Figma |
| UI components | `google-labs-code/shadcn-ui` | shadcn/ui component library |
| Design taste | `google-labs-code/taste-design` | Design quality assessment |
| Web research | `firecrawl/firecrawl-build-search` | Query-first discovery + content hydration |
| Web scraping | `firecrawl/firecrawl-build-scrape` | Page extraction |
| Doc co-authoring | `anthropics/doc-coauthoring` | Collaborative document editing |
| Frontend design | `anthropics/frontend-design` | UI/UX development tools |
| Visual design | `anthropics/canvas-design` | Visual art in PNG/PDF |
| Web artifacts | `anthropics/web-artifacts-builder` | React + Tailwind HTML artifacts |

## Loading Strategy

### Quick Task (1-2 skills)
Just load the specific skill from the table above. Don't load the umbrella.

### Standard Research Task (3-5 skills)
```
1. planning/ux-research-and-specs (umbrella)
2. phuryn/competitor-analysis OR deanpeters/customer-journey-map
3. media/youtube-content (if video research needed)
4. phuryn/create-prd OR deanpeters/prd-development (for output)
```

### Full PRD with Research (6-8 skills)
```
1. planning/ux-research-and-specs (umbrella)
2. deanpeters/problem-statement
3. deanpeters/proto-persona
4. phuryn/competitor-analysis
5. deanpeters/customer-journey-map
6. deanpeters/epic-hypothesis
7. deanpeters/user-story
8. phuryn/prioritization-frameworks
```

### Complex Research (10+ skills)
**Don't load in main context.** Use subagent delegation:
- Subagent 1: Competitive analysis (phuryn/competitor-analysis + coreyhaines31/competitor-profiling)
- Subagent 2: User research (coreyhaines31/customer-research + deanpeters/customer-journey-map)
- Subagent 3: PRD drafting (deanpeters/prd-development + deanpeters/user-story)
- Main agent: Synthesize outputs

## Source Repo Quick Reference

| Repo | Skills | Best For |
|------|--------|----------|
| `deanpeters/Product-Manager-Skills` | 46 | PM methodology, discovery, stories, journeys |
| `phuryn/pm-skills` | 65 | PM lifecycle, prioritization, execution |
| `coreyhaines31/marketingskills` | 61 | Marketing, CRO, research, competitor profiling |
| `google-labs-code/stitch-skills` | 13 | Design systems, UI components, design-to-code |
| `anthropics/skills` | 17 | Doc authoring, frontend design, web artifacts |
| `firecrawl/skills` | 5 | Web research, scraping, search |
| `vercel-labs/next-skills` | 7 | Next.js best practices |
