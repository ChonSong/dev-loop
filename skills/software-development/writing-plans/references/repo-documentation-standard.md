# Repo Documentation Standard

## Principle
Every repo in the ecosystem should be **simple to ingest for future AI agents**. Documentation is not for humans reading linearly — it's for agents that need to quickly understand structure, entry points, and integration patterns.

## Required Files

### AGENTS.md (every repo)
Quick-reference for AI agents. Max 40 lines. Always include:
```
# AGENTS.md — {repo-name}

## About
One-liner describing what this repo is and its current status (active/legacy/experimental).

## Quick Commands
```bash
# Build/run/test commands
```

## Key Files
- `path/to/important/` — what it does
- `path/to/another/` — what it does

## Integration Points
- Consumes: {input repos/data}
- Outputs: {target repos/services}

## Notes
- Any critical gotchas
- Migration status if applicable
```

### README.md (every repo)
Comprehensive documentation. Should be AI-optimized with:
- Project name + one-liner
- Architecture overview (ASCII diagram preferred)
- Quick start (build/run/test)
- Project structure (tree with inline descriptions)
- Protocol/API docs if applicable
- Component inventory with one-line descriptions
- Tech stack table
- Related projects

### MIGRATION.md (migration source repos only)
For repos that serve as migration sources (like agent-os):
- What's been migrated (table with status)
- What remains (table with complexity estimates)
- Design differences (source vs target)
- What's NOT migrating and why

## Writing Guidelines
- Use declarative facts, not instructions
- Include exact file paths, not vague references
- Use tables for comparison/inventory
- ASCII diagrams for architecture
- One-line descriptions per component
- Never say "see documentation" without linking

## Pattern
When improving a repo's docs:
1. Read existing README
2. Explore project structure
3. Write AGENTS.md (quick reference)
4. Rewrite README.md (comprehensive)
5. Add MIGRATION.md if applicable
6. git add + commit + push

## Examples
- hermes-web-computer: README.md (319 lines) + AGENTS.md
- agent-os: AGENTS.md + MIGRATION.md
- seans-reporepo: README.md rewrite + AGENTS.md
- repo-transmute: AGENTS.md
