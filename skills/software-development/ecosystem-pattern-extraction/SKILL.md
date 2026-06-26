---
name: ecosystem-pattern-extraction
description: Analyze external agent ecosystems, toolkits, and open-source repos — extract architecture patterns, run parallel deep-dives, and implement the best parts in our stack.
---

# Ecosystem Pattern Extraction

Class-level methodology for inspecting external agent tools/ecosystems, distilling their high-signal patterns, and implementing them in our Hermes-based stack.

## When to Use

- User asks "what can we learn from https://github.com/..."
- User links a GH repo and asks "analyze this" / "deep-dive" / "review"
- You encounter an interesting open-source agent toolkit, skill catalog, or harness project
- Comparing competing approaches in the agent ecosystem

## Methodology — 5-Phase Extraction

### Phase 1: Surface Survey (single call)

Read the README. Extract:
- What problem does it solve?
- Stack / language / dependencies
- 1-paragraph elevator pitch
- Architecture diagram if present
- Key stats (stars, version, contributors, LICENSE)

Read `package.json` / `pyproject.toml` for:
- Version, description
- Entry points and CLI commands
- Export surface (files field, packages)

### Phase 2: Structure Mapping (single call)

Get the repo root listing. Classify every top-level directory:
- `agents/` — subagent definitions
- `skills/` — workflow bundles
- `hooks/` — event-driven automation
- `commands/` — slash commands
- `rules/` — guidelines & constraints
- `scripts/` — build/CI/install tooling
- `mcp-configs/` — MCP server configs
- `tests/` — test suite

Identify the **density** of each. A dir with 200+ files is a core surface. A dir with 3 files is a minor surface.

### Phase 3: Signal Identification

Based on the surface scan, identify high-signal areas to deep-dive. Use these heuristics:

| Signal | What to look for |
|--------|-----------------|
| **Novel architecture** | Config-driven install, manifest pipeline, dependency resolution |
| **Directly portable** | Hooks system, env-var gating, profile tiers, tool scoping |
| **Applicable to our stack** | PostToolUse accumulators, Stop-as-aggregation, selective install |
| **Quality indicator** | >1000 tests, TDD mandate, structured PR policy, living WORKING-CONTEXT.md |

Limit to **2-3** deep-dives. More is wasteful (principle of parsimony).

### Phase 4: Parallel Deep-Dive

Use `delegate_task` with `tasks: []` array to run deep-dives simultaneously (up to 3 concurrent):

```python
# Pattern — send parallel subagents with specific extraction goals
delegate_task(tasks=[
    {"goal": "Extract X's hook system...", "context": "...", "toolsets": ["terminal", "file"]},
    {"goal": "Extract Y's install architecture...", "context": "...", "toolsets": ["terminal", "file"]},
    {"goal": "Extract Z's agent schema...", "context": "...", "toolsets": ["terminal", "file"]},
])
```

Each deep-dive should:
- Fetch the actual files (not just README claims)
- Extract concrete structures, schemas, and examples
- Note what's applicable to our stack vs what's specific to their harness
- Return a terse summary with verifiable details

### Phase 5: Synthesis — Actionability Matrix

After parallel deep-dives return, produce a matrix:

| Pattern | Effort | Impact | Priority |
|---------|--------|--------|----------|
| Hook profile env vars | Low | Medium | P1 |
| Manifest-driven install | High | High | P2 |
| Subagent tool scoping | Low | Medium | P2 |

Then **pick the highest-priority items and implement them immediately**. Extraction without implementation is research debt.

## Pitfalls

- **Don't read every file.** Large repos have 10K+ files. Top-down survey → signal ID → focused deep-dive only.
- **Don't skip Phase 1 for README.md.** The README is the author's map. Read it before forming opinions.
- **Don't implement everything.** The principle of parsimony applies — pick the highest-ROI patterns first.
- **Don't trust subagent summaries blindly.** Verify critical claims (file contents, existence checks) yourself.
- **Don't graft their architecture onto ours wholesale.** Extract the *idea*, not the *code*.
- **Don't spend on one-off browser sessions** for plain-text endpoints (raw.githubusercontent.com, .md, .json, .yaml). Use `curl` via terminal instead — it's faster and the browser stack consumes unnecessary context.

## Related Skills

- `website-investigation` — for interactive web exploration (SPAs, login flows)
- `repo-portfolio-audit` — for cataloging your own repos
- `seans-reporepo-query` — for searching your own repo catalog
- `hermes-auxiliary-config-debug` — for Hermes config debugging

## References

See `references/ecc-patterns.md` for the full extraction from the ECC (Everything Claude Code) ecosystem — hooks system, install architecture, and subagent schema.
