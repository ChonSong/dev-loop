---
name: presentation-design
description: Design presentation slides following McKinsey principles — conclusion-oriented titles, one message per slide, bar charts with callouts, minimal color, top-down communication. Use when the user asks for a slide deck, presentation, report visuals, or data-driven video segments.
version: 1.0.0
metadata:
  hermes:
    tags: [presentation, design, mckinsey, slides, data-visualization, design-principles]
    category: creative
---

# Presentation Design (McKinsey Principles)

Design slides and presentation content following McKinsey-style principles. Produces clear, data-driven, professional visuals whether for slide decks or video segments.

## When to Use

- User asks for slides, a presentation, or a pitch deck
- User wants to structure data-driven content visually
- Creating video segments that follow slide-like structure (one message per segment)
- Any time the conversation shifts to "make this more engaging" or "structure this better"

## Core Principles

### 1. Titles are Conclusions, Not Labels

- Average title length: **14 words**
- **72% of titles** should be active and result-oriented
- The title tells the audience *why* the information matters
- Titles create a narrative that flows logically slide-to-slide

**Examples:**
| Label (Avoid) | Conclusion (Use) |
|---|---|
| "Revenue by Quarter" | "Q3 Revenue Grew 18% Driven by Enterprise Expansion" |
| "AI Adoption" | "72% of Organizations Use AI but Only 28% Have Scaled" |
| "Task Analysis" | "Automatable Tasks Now Represent 821 Skills Across 47 Domains" |

### 2. Every Slide Has One Job

- **62% of slides** deliver a single, clear message
- Complex ideas → split across multiple slides
- Each point deserves its own emphasis
- One slide ≈ one thought

### 3. Slides Must Be Simple and Clear

- Average: **100 words** per slide
- Only **15% of slides** exceed 200 words (and those are appendix slides)
- Remove anything that doesn't support the single message

### 4. Use a Few Repeated Layouts

**Four layouts cover ~70% of slides:**
| Layout | Usage | 
|--------|-------|
| **Single Chart Slide** (29.7%) | Title + one chart below |
| **Chart with Bullets** (18.7%) | Chart left, supporting text right |
| **Two-Column Comparison** (12.1%) | Side-by-side with visual divider |
| **Table Slide** (10.4%) | Structured data rows |

### 5. Use Visuals Extensively

- **71% of slides** contain a chart
- **~80%** when including visual frameworks
- Charts explain what text cannot
- Every chart needs a clear story

### 6. Bar Charts are King

| Chart Type | % of Charts |
|------------|-------------|
| Bar charts | **40%** |
| Line charts | 15.9% |
| Waterfall | 10.8% |

**Prefer bar charts** for comparisons, rankings, and part-to-whole.

### 7. One Chart is Usually Enough

- **59% of chart slides** use only a single chart
- Reinforces "one slide, one message"

### 8. Use Callouts on Charts

- **72% of charts** use callouts (text/visual cues)
- Callouts highlight the most important data point
- Callouts explain the key takeaway explicitly

Example: On a bar chart showing "72% use AI, 28% scaled", a callout reads: **"44% Gap"** — the story is the gap, not the bars.

## Visual Design Rules

### Color: Minimal and Intentional

- **Dark background** (navy #0a1628 works for video/dark mode)
- **Primary accent** (golden #ffd700) — key data, callouts, conclusions
- **Secondary accent** (teal #4ecdc4) — supporting context, secondary bars
- **Warning** (red #ff3333) — risks, gaps, negative signals
- **Grey** (#3a3a5a) — unfilled states, empty bars, non-highlighted data
- Color should be the exception, not the rule

### Typography

- **Titles:** 36-72px bold, accent color
- **Body:** 24-28px regular, off-white (#e8e8f0)
- **Labels/Axes:** 18-22px muted (#8888aa)
- **Callouts:** 20-24px bold, accent color
- **Data numbers:** 48-120px bold (for hero-number slides)

### Layout Patterns for Video

When translating slides to video segments:

| Pattern | Duration | Best For |
|---------|----------|----------|
| **Bar Chart** | 8-10s | Rankings, comparisons |
| **Comparison** | 8-10s | Before/after, two options |
| **Hero Number** | 6-8s | Single impactful stat |
| **Icon Array** | 6-8s | Proportions, trust data |
| **Timeline** | 8-10s | Progression, evolution |
| **Quote/Closer** | 4-6s | Reflection, conclusion |

Add 0.5s fade-in and 0.5s fade-out per segment.

### Data Callout Patterns

Always call out the story, not the data:
- ❌ "68% of outputs need editing" (just a number)
- ✅ "Most AI work still needs human judgment" (the insight)

## Segment Structure (for Video)

Each segment should have this structure:
1. **Title (conclusion)** — up top, large, bold, accent color
2. **Visual** — chart/diagram dominating the frame (~60-70% of vertical space)
3. **Callout** — key insight highlighted, with explanation
4. **Page number** — bottom-left, subtle, for orientation

## Pitfalls

- **"Label" titles instead of conclusion titles** — if the title could be a chapter heading, rewrite it as a finding
- **Multiple messages per segment** — if you can't state the point in one sentence, split the segment
- **No chart callout** — the viewer should know what to see without guidance
- **Too many colors** — stick to 3-4 intentional colors max
- **Tiny text at 1920×1080** — never go below 18px; prefer 24px+ for body
- **Forgetting font discovery** — PIL's default font is ~8px; always check for KaTeX or DejaVu fonts

## Related Skills

- `pil-video-generation` — rendering PIL/FFmpeg videos with these segment patterns
- `hyperframes-text-workaround` — font discovery for PIL rendering
