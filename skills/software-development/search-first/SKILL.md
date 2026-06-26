---
name: search-first
description: Research-before-coding workflow. Search for existing tools, libraries, and patterns before writing custom code. Use web_search, search_files, and skill_view before implementing.
origin: ECC (adapted for Hermes)
---

# Search First — Research Before You Code

Systematizes "search for existing solutions before implementing" — already part of the Soul of the System ("Be resourceful before asking"), this skill makes it a structured workflow.

## When to Activate

- Starting a new feature that likely has existing solutions
- Adding a dependency or integration
- Before creating a new utility, helper, or abstraction
- User asks "add X functionality" and you're about to write code from scratch

## Workflow

1. **Repo scan** — `search_files` in the project for existing implementations
2. **Skills check** — `skills_list` to see if a skill already covers this
3. **Web search** — `web_search` for libraries, packages, or patterns
4. **Evaluate** — Score candidates (functionality, maintenance, community, license, deps)
5. **Decide** — Adopt existing > Extend/wrap > Build custom (informed by research)

## Decision Matrix

| Signal | Action |
|--------|--------|
| Exact match, well-maintained, permissive license | **Adopt** — install and use |
| Partial match, good foundation | **Extend** — install + thin wrapper |
| Multiple weak matches | **Compose** — combine 2-3 small packages |
| Nothing suitable | **Build** — write custom, but informed |

## Hermes-Specific Adaptation

- Use `skills_list` and `skill_view` to check existing skills before building
- Use `search_files` to scan project codebase
- Use `web_search` with operators (`site:npmjs.com`, `site:pypi.org`, `site:github.com`)
- Use `web_extract` to read docs of candidate libraries
- For MCP tools: check `native-mcp` skill for available servers

## Pitfalls

1. **Rushing to implementation before investigation**. When presented with a complex design task, do NOT jump to code. First: investigate existing approaches (look at how others solved the same problem), explore codebases, read specs, ask clarifying questions, present options before building. The user explicitly called this out: "investigate ask questions and explore codebases where required." If the model you're running on isn't capable of architectural design (e.g., flash models), acknowledge the limitation and defer design decisions rather than producing a shallow implementation.

2. **Never write a utility from scratch without checking:** (1) project codebase, (2) existing skills, (3) npm/PyPI, (4) GitHub. The most common waste is building something that already exists.
