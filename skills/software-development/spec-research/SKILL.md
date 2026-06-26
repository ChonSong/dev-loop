---
name: spec-research
description: "Research detailed specs and requirements before writing code. Combines product diagnostics, competitive analysis, YouTube/interface research, and PRD creation into a repeatable spec-writing workflow."
---

# Spec Research — Research Before You Specify

End-to-end workflow for producing well-researched specs, PRDs, and requirements. The core principle: **a spec built without research is a spec built on assumptions**.

## When to Activate

- User asks to write a spec, PRD, or requirements document
- Before planning any multi-step feature
- When choosing between implementation approaches
- When the user says "research this before we build"
- Proactively: before any feature that touches user-facing behavior

## Workflow

### Phase 1: Product Diagnostic (product-lens)

Validate the "why" before the "what":

1. **Who is this for?** (specific person, not "users")
2. **What's the pain?** (quantify: frequency, severity, current workaround)
3. **Why now?** (what changed that makes this possible/necessary?)
4. **What's the 10-star version?** (if money/time were unlimited)
5. **What's the MVP?** (smallest thing that proves the thesis)
6. **What's the anti-goal?** (what are you explicitly NOT building?)
7. **How do you know it's working?** (metric, not vibes)

Output: go/no-go recommendation. If "yes" → proceed to research.

### Phase 2: Research Existing Solutions

**2a. Web Search**
- Search for competitor products, open-source alternatives, UX research
- Use `browser` toolset for web interaction
- Use `terminal` with `curl` for direct HTTP requests
- Key queries: "[problem] + [domain]", "[competitor] + walkthrough", "[pattern] + UX research"

**2b. YouTube Research (media/youtube-content)**
- Find videos of people using similar interfaces: walkthroughs, conference talks, user testing sessions
- Extract transcripts using `scripts/fetch_transcript.py`
- Look for: interaction patterns, pain points users mention, workflow sequences, design decisions explained by creators
- Key search terms: "[product] walkthrough", "[feature] demo", "[product] review", "how [product] works"

**2c. Visual Research**
- Use `vision_analyze` with screenshots or image URLs
- Analyze competitor UIs: layout, information density, interaction patterns, navigation structure
- If the user shares mockups or screenshots, study them for design intent

**2d. Academic/Deep Research (arxiv, blogwatcher)**
- For novel interaction patterns, search arxiv for HCI/UI papers
- Check blogwatcher for relevant industry blog posts

### Phase 3: Synthesize Findings

Create a research brief:

```
## Research Brief: [Feature Name]

### Problem Statement
[One sentence from Phase 1]

### Existing Solutions
| Solution | Approach | Strengths | Weaknesses |
|----------|----------|-----------|------------|
| [Competitor A] | [approach] | [strengths] | [weaknesses] |

### UX Patterns Observed
- [Pattern 1]: [description + source]
- [Pattern 2]: [description + source]

### Key Insights from User Videos
- [Insight 1]: [quote or observation + video source]
- [Insight 2]: [quote or observation + video source]

### Recommended Approach
[Synthesis: what should we build and why]

### Anti-Goals
- [What we're explicitly NOT building]
```

### Phase 4: Write the Spec/PRD

Use `phuryn/create-prd` or `deanpeters/prd-development` for the structured PRD template. Key sections:

1. **Problem** — from Phase 1 diagnostic
2. **Personas** — who this is for
3. **Solution** — from Phase 3 synthesis
4. **User Stories** — bite-sized, testable
5. **Metrics** — how we know it's working
6. **Non-Goals** — explicit anti-goals
7. **Dependencies** — what this needs from other systems

### Phase 5: Plan Implementation

Use `software-development/writing-plans` to break the spec into bite-sized implementation tasks (2-5 min each).

## Skill Collision Awareness

Many skills share bare names. ALWAYS use categorized paths:
- `planning/product-lens` (not `product-lens`)
- `media/youtube-content` (not `youtube-content`)
- `software-development/writing-plans` (not `writing-plans`)
- `phuryn/create-prd` (not `create-prd`)

If `skill_view` returns an ambiguity error, use the full `category/skill-name` path from the error's `matches` list.

## Tool Availability Notes

- **No `web_search` or `web_extract` tool** — use `browser` toolset or `terminal` with `curl`
- **YouTube transcripts** — use `media/youtube-content` skill's `scripts/fetch_transcript.py`
- **Visual analysis** — use `vision_analyze` with image URLs or local paths
- **Browser automation** — use `ssh sean@localhost` for host-level browser interaction

## Anti-Patterns

- **Spec without research** — writing requirements based on assumptions instead of evidence
- **Research without synthesis** — collecting links/videos but not extracting actionable insights
- **Skipping the diagnostic** — jumping to solution design before validating the problem
- **Ignoring anti-goals** — a spec without explicit non-goals will scope-creep

## Output

Save the research brief and PRD to `docs/specs/YYYY-MM-DD-feature-name.md`.
