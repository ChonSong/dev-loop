# Content Compilation

When a user shares scrapped or copied course/learning material across multiple messages and asks for a compiled reference document.

## When to Use

- User pastes sections of a course, article, or documentation across multiple messages
- User asks "create a complete doc" or "compile this into a document"
- User has been feeding material incrementally and wants it all in one place

## Workflow

1. **Track sections across messages** — as the user sends material, note headings and structure. Don't compile mid-stream; wait for the final request.

2. **Identify the document type**:
   - **Course material compilation** — structured sections with headings, quotes, tables
   - **Analysis/essay** — thesis-driven with arguments and evidence
   - **Reference doc** — dense information organized by topic

3. **Structure for course/learning compilations**:
   - Numbered top-level sections
   - Block quotes (`>`) for direct source citations with attribution
   - Tables for comparative data (course comparisons, statistics, timelines)
   - Bold key terms and figures
   - Include a file path at the end so the user knows where it lives

4. **Supplement with analysis when invited** — if the user engages with the material and asks for expansion, add opinionated sections after the compiled content. Distinguish course content from your own analysis clearly.

5. **Save format**: Markdown `.md` in the workspace directory (`/home/sc/workspace/`). Don't over-format — simple markdown renders well in Hermes WebUI.

6. **Update incrementally** — if the user sends more material after the initial doc, `patch` the file to add new sections rather than rewriting the whole thing.

## Example Structure

```markdown
# Why Does AGI Matter?

## 1. [Section Heading]

Content from course...

> *"Direct quote"* — **Source**

## 2. [Next Section]

...

---

## N. [Original Analysis / Expansion]

Your own take on the topic...

---

*Compiled from [Source Title]. Original: [URL]*
```

## Pitfalls

1. **Don't compile mid-stream** — wait until the user explicitly asks for the document. They may be sending material for discussion, not archiving.
2. **Attribute sources** — distinguish course material from your own analysis. Block quotes + attribution for sourced material.
3. **Don't rewrite on every update** — use `patch` for targeted additions. The user sent more content; add it as a new section, don't restructure the whole doc.
4. **File naming** — use descriptive kebab-case names. `why-agi-matters.md`, not `course-notes.md`.
