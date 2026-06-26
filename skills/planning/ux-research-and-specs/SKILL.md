---
name: ux-research-and-specs
description: End-to-end workflow for researching interfaces, gathering UX evidence, and producing well-structured specs/PRDs. Combines web search, YouTube transcript extraction, visual analysis, competitor research, and structured templates into a repeatable pipeline.
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [research, UX, spec, PRD, requirements, product-design, youtube, web-search]
    related_skills:
      - planning/product-lens
      - software-development/search-first
      - media/youtube-content
      - software-development/plan
      - phuryn/create-prd
      - deanpeters/prd-development
      - deanpeters/problem-statement
      - deanpeters/problem-framing-canvas
      - deanpeters/proto-persona
      - deanpeters/customer-journey-map
      - deanpeters/customer-journey-mapping-workshop
      - deanpeters/epic-hypothesis
      - deanpeters/epic-breakdown-advisor
      - deanpeters/user-story
      - deanpeters/user-story-splitting
      - deanpeters/user-story-mapping
      - deanpeters/user-story-mapping-workshop
      - deanpeters/press-release
      - deanpeters/positioning-statement
      - deanpeters/feature-investment-advisor
      - deanpeters/workshop-facilitation
      - phuryn/competitor-analysis
      - phuryn/user-stories
      - phuryn/prioritization-frameworks
      - phuryn/pre-mortem
      - phuryn/outcome-roadmap
      - phuryn/release-notes
      - phuryn/test-scenarios
      - phuryn/job-stories
      - phuryn/stakeholder-map
      - phuryn/sprint-plan
      - phuryn/retro
      - phuryn/summarize-meeting
      - phuryn/brainstorm-okrs
      - phuryn/dummy-dataset
      - phuryn/wwas
      - coreyhaines31/cro
      - coreyhaines31/onboarding
      - coreyhaines31/customer-research
      - coreyhaines31/competitor-profiling
      - google-labs-code/design-md
      - google-labs-code/enhance-prompt
      - google-labs-code/stitch-loop
      - google-labs-code/react-components
      - google-labs-code/shadcn-ui
      - google-labs-code/remotion
      - google-labs-code/generate-design
      - google-labs-code/code-to-design
      - google-labs-code/manage-design-system
      - google-labs-code/extract-static-html
      - google-labs-code/extract-design-md
      - google-labs-code/upload-to-stitch
      - google-labs-code/taste-design
      - anthropics/doc-coauthoring
      - anthropics/frontend-design
      - anthropics/canvas-design
      - anthropics/web-artifacts-builder
      - remotion-dev/remotion
      - firecrawl/firecrawl-build
      - firecrawl/firecrawl-build-search
      - firecrawl/firecrawl-build-scrape
      - firecrawl/firecrawl-build-interact
      - vercel-labs/next-best-practices
      - vercel-labs/next-cache-components
      - vercel-labs/next-upgrade
---

# UX Research & Spec Writing

## Quick Start

**Don't load all skills at once.** Use the references to decide what to load:

| Situation | # Skills | What to load |
|-----------|----------|-------------|
| Quick task | 1–2 | Just the specific skill |
| Standard task | 3–5 | Umbrella + 2–3 supporting |
| Complex task | 6–8 | Full toolkit from references |
| Research-heavy | 10+ | Delegate to subagent |

## How to Retrieve Missing Skills

**Before writing content from scratch, check if the real skill exists on GitHub:**

```bash
# Search for skills by topic
hermes skills search "<topic>"

# Browse available skills
hermes skills browse

# If you know the source repo, clone it directly:
git clone --depth 1 https://github.com/deanpeters/Product-Manager-Skills.git
git clone --depth 1 https://github.com/phuryn/pm-skills.git
git clone --depth 1 https://github.com/VoltAgent/awesome-agent-skills.git  # index only
```

**Known skill source repos:**
- **deanpeters**: `https://github.com/deanpeters/Product-Manager-Skills` — PM skills (PRD, personas, journey maps, stories, etc.)
- **phuryn**: `https://github.com/phuryn/pm-skills` — PM lifecycle skills (PRD, competitor analysis, prioritization, etc.)
- **VoltAgent**: `https://github.com/VoltAgent/awesome-agent-skills` — curated index of 1000+ skills (check README for per-skill repo URLs)

**Rule**: If a skill is a stub (empty frontmatter, no real content), search GitHub for the real version before recreating. Use `hermes skills search` or clone the source repo directly.

## Skill Library Conventions

This skill follows the library's structural conventions. See `references/skill-library-conventions.md` for the full convention document.

Key points:
- **Class-level umbrellas** with rich SKILL.md + support file dirs (references/, templates/, scripts/)
- **Update the skill** (not just memory) when user corrects style/workflow/approach
- **Don't capture**: env failures, negative tool claims, transient errors, one-off narratives
- **Memory** = who user is / current state. **Skills** = how to do this class of task.
# UX Research & Spec Writing

End-to-end workflow for researching interfaces, gathering UX evidence, and producing structured specifications. Combines multiple research channels into a repeatable pipeline that produces evidence-backed specs, not guesses.

## When to Use

- `"Research how [product/feature] should work before we build it"`
- `"Write a spec for [feature]"`
- `"Look at how competitors solve [problem]"`
- `"What do users think about [interface pattern]?"`
- `"I need a PRD for [feature]"`
- `"Research [domain] UX patterns and write up requirements"`
- Any task requiring: competitive analysis →UX research →spec writing

## Pipeline Overview

```
Phase 1: Frame     → Phase 2: Research   → Phase 3: Synthesize  → Phase 4: Spec
┌──────────────┐    ┌──────────────────┐   ┌──────────────────┐   ┌────────────┐
│ Product Lens  │    │ Web Search       │   │ Evidence Matrix  │   │ PRD/Spec   │
│ Clarify Scope │    │ YouTube Transcripts│  │ Pattern Library  │   │ User Stories│
│               │    │ Competitor Audit │   │ Trade-off Table  │   │ Plan       │
│               │    │ Visual Analysis  │   │                  │   │            │
└──────────────┘    └──────────────────┘   └──────────────────┘   └────────────┘
```

## Phase 1: Frame the Research

### 1.1 — Clarify Before Researching

Before touching any tools, answer (ask the user via `clarify` if needed):

| Question | Why |
|----------|-----|
| What problem are we solving? | Scopes the research |
| Who is it for? | Defines user segments |
| What's the MVP? | Prevents scope creep |
| What already exists? | Builds on prior art |
| What's out of scope? | Prevents tangents |
| What does success look like? | Defines acceptance criteria |

**Rule**: If the user says "just research X" and the scope is clear, skip clarifying and start. Ask only when genuinely ambiguous.

### 1.2 — Define Research Questions

Translate the problem into 3-5 specific research questions. Format:

```
RQ1: How do [competitor/product] users currently [do X]?
RQ2: What UX patterns exist for [interaction type]?
RQ3: What are the known pain points with [approach]?
RQ4: What's the simplest possible version that works?
RQ5: What edge cases must we handle?
```

Save these to the workspace at `docs/research/YYYY-MM-DD_<slug>-research-questions.md`.

## Phase 2: Multi-Channel Research

Research all four channels below. Document everything in a research log.

### 2.1 — Web Search (Discovery)

Use the `web` toolset (web_search/web_extract) for broad discovery:

```
Search queries to run (in parallel where possible):
1. "[product domain] UX patterns 2024 2025"
2. "[competitor name] interface review"
3. "[problem name] user experience problems"
4. "[interaction type] best practices"
5. "[domain] design system components"
6. "HCI research [interaction pattern]"
7. reddit "how do you use [product type]"
8. Hacker News "[product type] design"

For each query: save top 5 results with URL, title, key finding, relevance (1-5).
```

**Technique — Breadth-then-Depth**:
- Round 1: 4-6 broad queries across different angles
- Round 2: Follow up on terminology/patterns discovered in Round 1
- Round 3: Target specific gaps; stop when >80% of results are already seen

### 2.2 — Video Research / YouTube Transcript Extraction

Use the `media/youtube-content` skill to extract transcripts from YouTube. This is the primary channel for seeing how interfaces actually work in practice.

**What to search for on YouTube:**
```
YouTube search queries:
1. "[product name] walkthrough [year]"
2. "[product name] tutorial"
3. "[product name] review"
4. "how to use [product name]"
5. "[competitor] vs [competitor] comparison"
6. "[interaction pattern] UX conference talk"
7. "designing [product type] talk"
8. "user testing [product type]"
9. "[domain] UI/UX case study"
10. "building [product type] interview"
```

**Workflow per video:**

```bash
# 1. Get transcript with timestamps
python3 SKILL_DIR/media/youtube-content/scripts/fetch_transcript.py "URL" --text-only --timestamps

# 2. If transcript is long (>50K chars), split and process in chunks
# 3. Extract: workflow steps, UI patterns mentioned, pain points, design decisions
```

**UX-Specific Video Analysis Output Format:**

For each video, extract:
```
Video: [Title] — [URL] — [Duration]
Summary: [2-3 sentence overview]
Interface Elements Observed:
- [element]: [description of how it works]
User Flow: [step-by-step walkthrough of key flows]
Pain Points Mentioned: [list]
Design Decisions Noted: [list with rationale]
Quotes:  "[notable quote]" — [timestamp]
Relevance to Our Research: [1-5] + why
```

See `references/youtube-ux-research-guide.md` for detailed video search strategies, filtering, and multi-video synthesis tables.

### 2.3 — Competitor / Reference Interface Audit

Identify 3-5 competitor or reference products. For each, document using the template at `references/competitor-audit-template.md`.

If the browser is available, navigate to each competitor site and take screenshots. Use `vision_analyze` to extract structure from screenshots.

### 2.4 — Literature & Standards (Academic + Professional)

Search for:
```
arXiv queries:
- "human-computer interaction [topic]"
- "user experience [domain]"
- "interface design [pattern]"
- "usability evaluation [approach]"

Professional sources:
- Nielsen Norman Group articles (nngroup.com)
- W3C specifications (for web interfaces)
- Apple HIG / Google Material Design guidelines
- Laws of UX (lawsofux.com)

Search: "[pattern] UX research site:nngroup.com"
Search: "W3C [component type] specification"
Search: "[design system] guidelines"
```

## Phase 3: Synthesize Evidence

### 3.1 — Evidence Matrix

Create a matrix mapping each research question to the evidence found:

```
| RQ# | Question | Web Evidence | Video Evidence | Competitor Evidence | Key Finding |
|-----|----------|-------------|---------------|-------------------|-------------|
| RQ1 | ...      | [source]    | [source]      | [source]          | [finding]   |
| RQ2 | ...      | [source]    | [source]      | [source]          | [finding]   |
```

Color-code: ✅ Strong evidence (3+ sources agree) | ⚠️ Conflicting evidence | 🔍 Single source

### 3.2 — Pattern Library

Document patterns discovered:

```
Pattern: [Name]
Description: [what it is and how it works]
Seen In: [where we found it]
Evidence: [screenshot/transcript citation]
Good For: [when to use it]
Watch Out For: [pitfalls]
Our Adaptation: [how we'll use/modify it]
```

### 3.3 — Trade-off Analysis

For each major design decision, document the trade-offs:

```
Decision: [What we're deciding]
Option A: [approach]
- Pros: [...]
- Cons: [...]
- Seen In: [...]

Option B: [approach]
- Pros: [...]
- Cons: [...]
- Seen In: [...]

Recommendation: [X] + rationale based on our constraints
```

## Phase 4: Produce the Spec

### Choose Output Format Based on Task

| Task Type | Output | Skill to Use |
|-----------|--------|-------------|
| Quick feature addition | Feature brief | Write inline (< 1 page) |
| New feature / product | Full PRD | `phuryn/create-prd` (8-section) or `deanpeters/prd-development` (8-phase workflow) |
| Process from discovery → PRD | Structured process | `deanpeters/prd-development` + supporting skills below |
| Redesign | UX Spec | See UX Spec Template below |
| Quick decision | Decision Record | See Decision Record below |

### Supporting Skills (load as needed)

These are real, full-content skills from the deanpeters and phuryn collections:

| Skill | Purpose |
|-------|---------|
| `deanpeters/problem-statement` | Frame the problem with evidence |
| `deanpeters/problem-framing-canvas` | MITRE-style problem framing (Look Inward, Outward, Reframe) |
| `deanpeters/proto-persona` | Create hypothesis-driven personas |
| `deanpeters/customer-journey-map` | Map customer experience across touchpoints |
| `deanpeters/customer-journey-mapping-workshop` | Guided journey mapping session |
| `deanpeters/epic-hypothesis` | Turn initiatives into testable hypotheses |
| `deanpeters/epic-breakdown-advisor` | Break epics into stories (9 patterns) |
| `deanpeters/user-story` | Write user stories with acceptance criteria |
| `deanpeters/user-story-splitting` | 8 proven story splitting patterns |
| `deanpeters/user-story-mapping` | Visual story mapping |
| `deanpeters/press-release` | Amazon Working Backwards method |
| `deanpeters/positioning-statement` | Geoffrey Moore positioning framework |
| `deanpeters/feature-investment-advisor` | Prioritize feature investments |
| `deanpeters/workshop-facilitation` | Interactive session protocol |
| `phuryn/competitor-analysis` | Full competitive landscape analysis |
| `phuryn/user-stories` | INVEST-compliant stories with 3 C's |
| `phuryn/prioritization-frameworks` | 9 prioritization frameworks |
| `phuryn/pre-mortem` | Risk analysis on PRDs |
| `phuryn/outcome-roadmap` | Transform output → outcome roadmaps |
| `phuryn/test-scenarios` | Create test scenarios from stories |
| `phuryn/job-stories` | JTBD-format job stories |
|| `phuryn/stakeholder-map` | Power/interest grid + comms plan |

**For the full decision matrix** (which skill to use when, and how phuryn vs deanpeters overlap), see `references/pm-toolkit-guide.md`.

### Feature Brief Template (< 1 page)
# Feature Brief: [Name]

## Problem
[One paragraph: who has this pain, how bad is it, what do they do today]

## Proposed Solution
[One paragraph: what we're building, core interaction]

## User Story
As a [user type], I want to [action] so that [outcome].

## Acceptance Criteria
- [ ] [Measurable criterion]
- [ ] [Measurable criterion]

## Out of Scope
- [What we're explicitly NOT building]

## Open Questions
- [ ] [Question that needs answer before/during implementation]
```

### Full PRD Template

```markdown
# PRD: [Feature Name]

## 1. Executive Summary
- **Problem**: [one paragraph]
- **Solution**: [one paragraph]
- **Success Metric**: [how we measure if this works]

## 2. Research Summary
### Key Findings
[Top 5-7 findings from research, with evidence citations]

### Competitor Landscape
[Brief comparison table of 3-5 competitors]

### User Feedback / Pain Points
[What users struggle with today]

## 3. Target Users
### Primary Persona
- **Who**: [description]
- **Goal**: [what they want to accomplish]
- **Pain**: [what frustrates them]
- **Context**: [when/where they use this]

### Secondary Persona (if applicable)
[same structure]

## 4. User Journeys
### Happy Path
1. [step] → [step] → [step]
2. Time-to-value: [estimate]

### Edge Cases
- [edge case]: [how we handle it]
- [edge case]: [how we handle it]

## 5. Functional Requirements

### Must Have (P0)
- [ ] [requirement] — [evidence source]
- [ ] [requirement] — [evidence source]

### Should Have (P1)
- [ ] [requirement]
- [ ] [requirement]

### Nice to Have (P2)
- [ ] [requirement]

## 6. Non-Functional Requirements
- **Performance**: [specific targets]
- **Accessibility**: [WCAG level]
- **Mobile**: [responsive / native / both]
- **Browser Support**: [list]

## 7. Information Architecture
[Site map / screen flow / navigation structure]

## 8. Interface Specifications

### [Screen/Component Name]
- **Purpose**: [what it does]
- **Layout**: [description or wireframe reference]
- **Interactions**: [what happens on click/hover/input]
- **States**: [empty/loading/error/success]
- **Accessibility**: [ARIA roles, keyboard nav]

### [Next Screen/Component]
[same structure]

## 9. Analytics / Metrics
| Metric | How Measured | Target |
|--------|-------------|--------|
| [metric] | [method] | [target] |

## 10. Open Questions & Decisions
| Question | Decision | Rationale | Date |
|----------|----------|-----------|------|
| [question] | [decision] | [why] | [date] |

## 11. Out of Scope
- [explicit non-goal]

## 12. Dependencies
- [dependency] — [status]

## 13. Release Plan
- **MVP**: [what ships first]
- **Iteration 2**: [what comes next]
- **Future**: [deferred items]
```

### UX Spec Template

```markdown
# UX Spec: [Feature/Redesign Name]

## Design Principles
1. [principle]: [description]
2. [principle]: [description]

## User Flow
[ASCII flow diagram or description]

## Screen Specifications

### Screen: [Name]
- **URL/Route**: [path]
- **Purpose**: [what it accomplishes]

```
[ASCII wireframe or structured layout description]

┌─────────────────────────────────┐
│ Header: [logo] [nav] [actions]  │
├─────────────────────────────────┤
│                                  │
│ [main content area]              │
│                                  │
├─────────────────────────────────┤
│ Footer: [links]                  │
└─────────────────────────────────┘
```

- **Components**: [list of components on this screen]
- **Interactions**:
  - [trigger]: [result]
  - [trigger]: [result]
- **Responsive Behavior**:
  - Desktop: [behavior]
  - Tablet: [behavior]
  - Mobile: [behavior]

## Component Specifications

### [Component Name]
- **States**: [default/hover/active/disabled/error]
- **Content Rules**: [what text/content goes here]
- **Accessibility**: [ARIA, keyboard, screen reader]

## Error States & Edge Cases
| Scenario | UI Response | Copy |
|----------|------------|------|
| [scenario] | [what happens] | [error message] |

## Animation / Transitions
- [element]: [animation description + duration]
```

### Decision Record (for quick decisions)

```markdown
# Decision: [Short Title]
Status: Proposed | Accepted | Deferred
Date: YYYY-MM-DD

## Context
[What's the situation? What's the problem?]

## Decision
[What did/will we decide?]

## Consequences
- Good: [...]
- Bad: [...]
- Neutral: [...]

## Alternatives Considered
- [Alternative]: [why we rejected it]
```

## Output File Structure

Save all research artifacts to the workspace:

```
docs/research/
  YYYY-MM-DD_<slug>-research-questions.md
  YYYY-MM-DD_<slug>-evidence-matrix.md
  YYYY-MM-DD_<slug>-pattern-library.md

docs/research/videos/
  <slug>-<platform>-<source>.md

docs/research/screenshots/
  <competitor>-<page>.png

docs/references/
  <slug>-<title>.md

docs/plans/
  YYYY-MM-DD_<slug>.md   (implementation plan)

docs/specs/
  YYYY-MM-DD_<slug>-prd.md
```

## Execution Strategy

### For Quick Research (single question, < 30 min):
1. Web search 3-5 targeted queries
2. Check one YouTube walkthrough if relevant
2. Synthesize into a decision record or 1-page brief
4. Done

### For Medium Research (feature spec, 1-2 hours):
1. Frame: define 3-5 research questions
2. Web search (breadth-then-depth, 2 rounds)
3. YouTube: find and extract 2-3 relevant videos
4. Competitor audit: 2-3 reference products
5. Synthesize: evidence matrix + pattern library
6. Output: Feature brief or lightweight PRD

### For Deep Research (full PRD, half day):
1. Full Phase 1: clarify + research questions
2. Full Phase 2: all four channels, multiple rounds
3. Full Phase 3: evidence matrix + trade-offs + pattern library
4. Full Phase 4: complete PRD with user journeys, IA, screen specs
5. Review: check for gaps, missing edge cases
6. Handoff: save to `docs/specs/`, create implementation plan

### For Research-Heavy Tasks (10+ skills needed):
**Don't load all skills in main context.** Use subagent delegation:
- Subagent 1: Competitive analysis (load phuryn/competitor-analysis + coreyhaines31/competitor-profiling)
- Subagent 2: User research (load coreyhaines31/customer-research + deanpeters/customer-journey-map)
- Subagent 3: PRD drafting (load deanpeters/prd-development + deanpeters/user-story)
- Main agent: Orchestrate, synthesize outputs, quality check

See `references/subagent-delegation-patterns.md` for detailed patterns and templates.

## Quality Checklist

Before delivering any spec:

- [ ] Every claim has an evidence source (not just opinion)
- [ ] Research questions are answered (or marked as unresolved)
- [ ] No "invented" UI patterns — everything is grounded in research
- [ ] Acceptance criteria are measurable
- [ ] Out of scope is explicit
- [ ] Edge cases are identified
- [ ] Personas are specific (not "users" or "developers")
- [ ] Metrics are specific numbers, not vague ("fast" → "< 200ms")
- [ ] Open questions are flagged, not silently decided

## Pitfalls

- **Skill collisions**: When this skill references other skills by name (e.g., `media/youtube-content`, `planning/product-lens`), always use the full categorized path. Bare names like `youtube-content` or `product-lens` collide across local skills_dir and external_dirs, causing `skill_view` to fail with "Ambiguous skill name." If you hit this error, use the path from the error's `matches` list.
- **Confirmation bias**: Don't just search for evidence supporting your initial idea. Search for contradicting evidence and failed approaches too.
- **Stale sources**: Prefer sources from the last 2 years unless citing foundational HCI research.
- **Fake specificity**: "Users want it fast" is not a requirement. "Page loads in < 2s on 3G" is.
- **YouTube autoplay trap**: Don't just watch one video. The first result is often not the best. Check the comments for alternative recommendations.
- **Competitor copying**: The goal is to understand patterns, not clone. Always ask "how does this apply to OUR context?"
- **Over-researching**: Set a time budget. A feature brief doesn't need 50 sources. Match depth to decision importance.
