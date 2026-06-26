---
name: vision-qa
description: Visual QA using AI vision models (vision_analyze). Assessing documents, designs, screenshots, renders, and other visual output with specific, prompted criteria.
---

# Vision QA (AI-Powered Visual Quality Assessment)

Use when you need to visually assess rendered output — PDFs, screenshots, designs, or any visual artifact — using `vision_analyze`.

## Core Principle: Specific Prompting

**Do NOT ask generic questions.** "Rate 1-10" or "Does this look good?" produces unreliable, vague, and useless answers.

**DO ask specific, measured, criteria-driven questions.** Tell the vision model exactly what to look for and what to report.

## Prompting Template

```markdown
CRITICAL QA: I need a visual assessment of [artifact type]. Answer specifically:

1. [ELEMENT 1]: [Specific question about size, spacing, alignment, readability, etc.]
2. [ELEMENT 2]: [Specific question about whitespace, balance, proportion, etc.]
3. [ELEMENT 3]: [Specific question about color, contrast, legibility, etc.]
...
N. OVERALL: What's the single biggest visual problem that needs fixing?
```

### Good Prompt Elements

| ✅ Do | ❌ Don't |
|-------|----------|
| "Is the body text readable at standard print scale?" | "Rate this 1-10" |
| "What percentage of the page is empty white space?" | "Does this look good?" |
| "Are the bullet points too tight or well-spaced?" | "Is the spacing OK?" |
| "What's the single biggest visual problem?" | "Any issues?" |
| "Compare the heading size to the body text" | "Is the font size right?" |
| Reference the specific context: "This is a printed resume" | Assume the model knows the use case |

### Bad Prompt Patterns (from experience)

- **"Rate 1-10"** — Vision models are unreliable at scalar ratings without context. They'll give false positives.
- **Vague value judgments** — "Does this look professional?" gets a platitude back, not a useful assessment.
- **No criteria** — Without telling the model what to inspect, it defaults to surface-level observations and misses the real issues.
- **Assuming print context** — If the output is destined for print, say so. The model's default frame is screen/web.

## Workflow

1. **Generate the visual artifact** (PDF, screenshot, HTML, image)
2. **Render it to a viewable format** if needed (PDF → PNG via PyMuPDF/fitz)
3. **Call `vision_analyze`** with the image URL/path and a detailed, specific question using the template above
4. **Evaluate the response** — if it says "looks fine" without specifics, your prompt was too vague. Re-prompt with more specific criteria.
5. **Iterate** — adjust the artifact based on findings, re-render, re-assess.

## References

See `references/resume-qa-example.md` for a worked example of prompting for document QA.

## Known Pitfalls

- **Vision model reliability depends on prompt specificity.** Generic prompts produce unreliable results. A vision model that says "looks great, 9/10" may miss real problems that a specific prompt would catch.
- **Vision model auth can fail.** Verify the `vision` provider in config.yaml or `AUXILIARY_VISION_*` env vars have valid API keys before relying on the tool.
- **Split-page QA** — For multi-page documents, assess each page separately. A single assessment of one page may miss page 2 issues.
- **Font size hierarchy** — Vision models notice relative proportions. If headings dwarf body text, they'll flag it even if absolute sizes are fine.
