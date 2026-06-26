# YouTube UX Research Guide

## Finding the Right Videos

### Search Query Patterns

**For understanding how an interface works:**
- "[product name] walkthrough [year]" — full UI walkthroughs, most useful
- "[product name] tutorial" — task-focused, shows user flows
- "how to use [product name]" — beginner perspective, reveals onboarding friction

**For design rationale:**
- "[product name] design decisions" — why they built it this way
- "[product name] UX case study" — post-mortems and process
- "[creator] interview [product name]" — founder/designer interviews

**For pain points and complaints:**
- "[product name] review" — what reviewers like/dislike
- "[product name] vs [competitor]" — comparison reveals trade-offs
- "[product name] problems" / "[product name] frustrations" — direct pain points

**For domain-level patterns:**
- "[domain] UI/UX conference talk" — HCI talks, design system talks
- "designing [product type]" — generic design process
- "user testing [product type]" — watching real users struggle

### Filtering for Quality
- **Prefer videos > 5 minutes** — short videos lack depth
- **Check the channel** — design-focused channels (Figma, Google Design, NNGroup) > random reviewers
- **Sort by relevance AND upload date** — interfaces change; prefer < 2 years old
- **Check comments** — often contain alternative video recommendations
- **Conference talks > reviews** — talks explain rationale; reviews just demonstrate

## Transcript Extraction

```bash
# Always get timestamps for UX analysis
python3 SKILL_DIR/media/youtube-content/scripts/fetch_transcript.py "URL" --text-only --timestamps
```

## Analysis Framework (per video)

### 1. Interface Inventory
List every interactive element mentioned or shown:
- Navigation: menus, tabs, breadcrumbs
- Content: lists, cards, tables, feeds
- Input: forms, filters, search, toggles
- Feedback: toasts, progress, empty states

### 2. Interaction Sequences
```
1. User lands on [page] -> sees [element]
2. User clicks [action] -> system shows [response]
3. User completes [task] -> system confirms [outcome]
```

### 3. State Transitions
Loading, error, empty, success — what changes after each action.

### 4. Design Language
Color system, typography hierarchy, spacing, icon style, motion.

### 5. Accessibility Signals
Keyboard shortcuts, screen reader, contrast, touch targets.

## Multi-Video Synthesis Table

| Interface Element | Video 1 | Video 2 | Video 3 | Consensus |
|------------------|---------|---------|---------|-----------|
| Primary nav type | Top bar | Sidebar | Top bar | Top bar (2/3) |
| Search behavior | Instant | On submit | Instant | Instant (2/3) |
| Empty state | Illustrated | Text only | Illustrated | Illustrated (2/3) |
