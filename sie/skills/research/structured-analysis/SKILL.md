---
name: structured-analysis
category: research
description: Take an analytical prompt or exercise (especially from a learning resource/course) and produce a thorough, component-by-component analysis applied to the user's specific context. Supports iterative expansion — user can direct deeper exploration into specific threads.
triggers:
  - "course exercise"
  - "reflection prompt"
  - "analytical question"
  - "what stood out"
  - "how would your country"
  - "what would you tell a friend"
  - "structured exercise"
  - "analyze scenario"
  - "situational analysis"
---

# Structured Analysis

When a user shares an analytical prompt, reflection question, or scenario exercise from a learning resource (course, book, article), produce a thorough analysis by decomposing the question into components, evaluating each systematically, and delivering a synthesized judgment.

## Two Patterns

### Pattern A: Reflexive Expansion

User asks a broad reflection question → you give a concise answer → user says "expand on these specific threads" → you produce a longer version incorporating their direction.

**When to use**: Open-ended prompts like "what's one thing most exciting and one most concerning?"

**Workflow**:
1. Give a concise initial answer — don't front-load everything. The user may want the short version first.
2. When they ask for expansion, identify the specific threads they named.
3. Research (say you will, then do it — web search, data points, examples from training data).
4. Produce an expanded version organized by their threads, not by your original structure.
5. Ground claims in real data (stats, named sources, specific examples).
6. Distinguish your analysis from the source material (use "## My Take" or "### Analysis" sections).

### Pattern B: Component-Based Evaluation

User shares a structured scenario or exercise from a course → you decompose it into evaluable sub-components → assess each → deliver a synthesized judgment.

**When to use**: Scenario exercises like "How would your country use AGI?" or "What safeguards exist?"

**Workflow**:
1. **Frame the exercise** — restate the prompt in your own words so the user knows you understand the task.
2. **Decompose into components** — identify the sub-questions or dimensions the prompt implies. For political safeguard analysis:
   - Constitutional safeguards
   - Institutional safeguards (federalism, civil service, judiciary)
   - Cultural/normative safeguards (media, civil society, conventions)
   - Wildcards (governor-general, reserve powers)
3. **Evaluate each component systematically** — one at a time, with specific evidence. Name which laws, bodies, or conventions apply.
4. **Rate or score each** — use a consistent scale (e.g., 🟢 Robust / 🟡 Moderate / 🔴 Weak / 🔴 Paper tiger).
5. **Synthesize** — overall verdict table or summary judgment. Tie it back to the original prompt.
6. **Use tables** for comparison data (components vs. robustness) — they're scannable and show the user you've been systematic.

## Structure Templates

### Template: Political/Safeguard Analysis

```
For [country], the scenario:

**What existing safeguards would stop [scenario]?**

### 1. [Safeguard name] — [robustness level]
Evidence, specific laws/bodies/conventions, AGI-specific vulnerability.

### 2. [Next safeguard] — [level]
...

### Overall

| Safeguard | Robustness | Why |
|-----------|-----------|-----|
| [Name] | 🟡 Moderate | [1-liner] |
...

The honest answer: [...]
```

### Template: Multi-Thread Expansion

```
**Most exciting:** [specific thing]

**Most concerning:** [specific thing]

---

*User requested expansion on [thread A], [thread B], [thread C]:*

## [Thread A]

Analysis with data points...

## [Thread B]

Analysis with data points...

## [Thread C]

Analysis with data points...

## The thread through all of them
[Unifying observation]
```

## Best Practices

1. **Don't front-load everything** — give the concise version first, expand on request. The user may want the short version.
2. **Let the user name the threads** — when they say "expand on X, Y, Z", use THEIR structure, not yours.
3. **Ground in specifics** — use named sources, real data points, specific examples. "Some economists argue" is weaker than "Goldman Sachs estimated 300M jobs affected."
4. **Tables for comparison** — when evaluating multiple components against a common framework, use a table. It's scannable and signals thoroughness.
5. **Distinguish source material from your analysis** — if the prompt came from a course, the user knows what the source says. Add value by applying it to THEIR context (their country, their field, their situation).
6. **End with a verdict or call to action** — don't just analyze; tell the user what your analysis implies for them.

## Pitfalls

1. **Don't rewrite the course material** — the user already has it. Add value by applying it to their specific context.
2. **Don't assume the user wants the long version** — they may just want a quick thought. Default concise, expand on request.
3. **Don't use vague attributions** — "experts say" without naming who. Name the source or don't use the claim.
4. **The user is from Australia** — default to Australia for country-specific exercises unless they say otherwise. Check memory for location before defaulting.
