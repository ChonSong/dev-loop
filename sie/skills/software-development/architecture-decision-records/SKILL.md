---
name: architecture-decision-records
description: Capture architectural decisions as structured ADRs during coding sessions. Maintains a log so future sessions understand why the codebase is shaped the way it is.
origin: ECC (adapted for Hermes)
---

# Architecture Decision Records

Capture architectural decisions as they happen. Decisions shouldn't live only in chat history — produce structured ADR documents alongside the code.

## When to Activate

- User explicitly says "record this decision" or "ADR this"
- Choosing between significant alternatives (framework, library, pattern, DB, API design)
- User says "we decided to..." or "the reason we're doing X instead of Y is..."
- User asks "why did we choose X?" (read existing ADRs)
- During planning phases when architectural trade-offs are discussed

## ADR Format

```markdown
# ADR-NNNN: [Decision Title]

**Date**: YYYY-MM-DD
**Status**: proposed | accepted | deprecated | superseded by ADR-NNNN
**Deciders**: [who was involved]

## Context

What is the issue motivating this decision?
[2-5 sentences describing the situation, constraints, and forces]

## Decision

What are we proposing?
[1-3 sentences stating the decision clearly]

## Alternatives Considered

### Alternative 1: [Name]
- **Pros**: [benefits]
- **Cons**: [drawbacks]
- **Why not**: [specific reason rejected]

### Alternative 2: [Name]
- **Pros**: [benefits]
- **Cons**: [drawbacks]
- **Why not**: [specific reason rejected]

## Consequences

### Positive
- [benefit 1]

### Negative
- [trade-off 1]

### Risks
- [risk and mitigation]
```

## Workflow

1. **Detect** — notice a decision moment in conversation or code changes
2. **Initialize** — if `docs/adr/` doesn't exist, create it with `README.md` index and `template.md`
3. **Document** — write the ADR with context, alternatives, rationale
4. **Index** — update the README.md table of contents
5. **Reference** — cite ADR numbers in commit messages and PR descriptions

## ADR Index (README.md)

```markdown
# Architecture Decision Records

| ID | Title | Date | Status |
|----|-------|------|--------|
| ADR-0001 | [Title](adr-0001-title.md) | YYYY-MM-DD | accepted |
```

## Hermes Adaptation

- Store ADRs in project's `docs/adr/` directory
- Use `write_file` to create new ADRs
- Use `search_files` to find existing ADRs
- Reference ADRs in git commit messages: `feat: add Redis caching (ADR-0003)`
