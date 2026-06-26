---
name: repo-scope-extension
description: Extend a project repo with a structured domain-research module — organized docs, cross-linked artifacts, README update, version bump, and push.
---

# Repo scope extension — adding a domain research module

When the user asks you to "extend the scope of our repo" with research on a specific domain or market, use this pattern to produce clean, usable, version-controlled documentation.

## When to use

- User provides a research table, report, or market analysis and asks you to "put this in the repo"
- User says "add this research to the project" or "extend scope of our repo for X"
- User shares a structured analysis they want persisted as part of the project's knowledge base

## Process

### 1. Explore existing state

Before writing anything, determine:

- **Repo location**: workspace or repos/ directory
- **Git remote**: who owns it, where it's hosted (`git remote -v`)
- **Current structure**: what's in src/, docs/, examples/, tests/
- **Existing README**: tone, depth, links to docs
- **Current version**: in pyproject.toml, package.json, etc.

### 2. Plan the module structure

Create a flat directory under `docs/`:

```
docs/research/
├── INDEX.md               ← master navigation (required)
├── vendor-database.md      ← one file per topic area
├── regulatory-pathway.md
├── financial-model.md
└── ...                     ← as many as needed
```

**Rules:**
- Every file must be self-contained (reader should understand it without external context)
- Every file must link to related files (cross-reference)
- INDEX.md must list all files with a 1-line "what it covers" column
- No subdirectories within research/ (keep discoverable)

### 3. Write each document

Each document should:

- **State its topic in a heading** — a reader should know within 2 seconds if this is what they need
- **Use tables** for structured data (vendor specs, lab capabilities, cost breakdowns, risk matrices)
- **Provide action items** — after reading, the user should know what to do next
- **Use relative links** to cross-reference other docs in the module
- **Avoid soft claims** — if data is estimated, label it. If it's a quote from a source, cite it.

Format decisions:
- Use markdown tables, not HTML. They're readable in source and in rendered form.
- Use `---` thematic breaks sparingly — headings provide structure.
- Lists of 3+ items with sub-detail per item → use a table.
- Time estimates → put them in a timeline table, not prose.

### 4. Write INDEX.md

The INDEX.md is the entry point. Include:
- A brief explanation of what the module covers
- A table of all files with "What it covers" and purpose columns
- A "how this fits the project" diagram or text
- Any key external contacts from the research

### 5. Update the README

Add a "Research module — [topic]" section to the repo's README.md that:
- Links to INDEX.md as the entry point
- Lists each research doc in a table with a 1-line description
- Includes the module in any architecture flow diagram

Use patch() on README.md — don't rewrite the whole file.

### 6. Bump version

Increment the minor version (0.1.0 → 0.2.0) in the project's version file and pyproject.toml / package.json.

### 7. Commit & push

```
git add -A
git commit -m "v0.X.0 — extend repo scope with [topic] research module

[multi-line summary of every file added and why]"
git push origin main
```

## Pitfalls

- **Don't guess the repo location.** The user's workspace changes. Always check the [Workspace::v1: ...] tag in their message.
- **Don't leave INDEX.md as an afterthought.** It's the only way a future reader navigates a 10+ file module.
- **Don't rewrite the README from scratch.** Use patch() to add the research section.
- **Don't skip git push.** Research in a local-only branch is invisible — the point is persisting it in the repo.
- **Don't create subdirectories** under docs/research/ — flat is more discoverable.
- **Don't write research docs in docs/ root.** They belong in their own subdirectory so they can be found and optionally excluded from builds.

## Related skills

- `website-investigation` — using Hermes browser tools to do prior research before writing docs
- `architecture-decision-records` — adding ADRs for technical decisions separate from domain research
- `search-first` — researching before coding, which often precedes a scope extension

## Reference templates

This skill provides no reference files — the research module artifacts are project-specific and live in the repo, not in this skill. The structure in step 2 is the template.
