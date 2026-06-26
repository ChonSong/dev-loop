---
name: hermes-agent-skill-authoring
description: "How to write, update, and maintain skills for Hermes Agent. Use when creating a new skill, patching an existing one, or deciding what to capture."
---

# Hermes Agent Skill Authoring

How to write, update, and maintain skills. Use when creating a new skill, patching an existing one, or deciding what to capture.

## Memory vs. Skills Boundary (Critical Distinction)

This is the single most important rule for keeping the skill library and memory system healthy:

### Memory (`MEMORY.md` / `memory/` logs) — WHO the user IS + durable situation facts
- User preferences, communication style, pet peeves
- Current project state, active blockers, infrastructure status
- Durable environment facts (OS, installed tools, project structure)
- **Keep under 70% capacity** — bloated memory wastes tokens every session

### Skills — HOW to do a class of task for this user
- Reusable procedures, workflows, tool usage patterns
- Pitfalls discovered during real work
- User style/format preferences **as they apply to that class of task**
- Rich `references/` for session-specific detail, `templates/` for boilerplate, `scripts/` for re-runnable actions

### The Test — Before Saving Anything, Ask:
1. "Will this be stale in 7 days?" → If yes, don't save to memory. Log to daily notes only.
2. "Is this about who the user is, or how to do a task?" → User = memory. Task = skill.
3. "Is this a one-off or a class?" → One-off = nothing. Class = skill.
4. "Is this environment-dependent?" → If yes, don't save (it'll become a false constraint).

### Anti-Patterns
- **Don't** save tool paths, port numbers, or server URLs to memory → belongs in skills
- **Don't** save "X is broken" → transient state, becomes a false constraint
- **Don't** save negative claims about tools → "browser tools don't work" hardens into refusal
- **Don't** let memory exceed 70% capacity → trim aggressively, move specifics to skills

## Skill Quality Standards

### Structure
```
skill-name/
├── SKILL.md              # Trigger + steps + pitfalls (this file)
├── references/           # Session-specific detail, research, API docs
│   └── <topic>.md
├── templates/            # Starter files to copy and modify
│   └── <name>.<ext>
└── scripts/              # Re-runnable verification/action scripts
    └── <name>.<ext>
```

### SKILL.md Format
```yaml
---
name: skill-name
description: "What this skill covers. Use when X, Y, Z."
---
```

Body: numbered steps, exact commands, pitfalls section, verification steps.

### Trigger Conditions (frontmatter description)
- What task types activate this skill?
- What file patterns, error messages, or user phrases are the signal?
- When should the agent load this skill vs. handle it with general tools?

### Pitfalls Section
Every skill needs a pitfalls section. These are class-level traps discovered during real work, NOT environment-dependent failures. Format:

```
### Pitfall: [Short Name]
[What goes wrong and why]
**Fix:** [What to do instead]
```

## When to Create vs. Update

### Create a new skill when:
- 5+ tool calls were needed and the approach succeeded
- A non-trivial workflow was discovered
- The user corrected your approach and the correction is reusable
- A class of task has no existing skill coverage

### Update (patch) an existing skill when:
- A step is wrong or missing
- A pitfall was discovered
- The user corrected your style/format/workflow for that class of task
- A tool command changed

### Add a support file when:
- Session-specific detail would bloat the SKILL.md
- A template or script would save repeated typing
- Research/API docs are needed for reference

## Skill Collision Resolution

When two skills share the same name (e.g., `hermes-agent` exists at root and under `autonomous-ai-agents/`):
1. Load the one that matches the task context
2. Note the collision for the curator
3. Don't try to disambiguate with `skill_view` — it will fail. Use `skill_manage(action=edit)` with the bare name (hits first match) or read the file directly.

## Preference Embedding

When the user expresses a style/format/workflow preference, the update belongs in the **SKILL.md body** of the skill that governs that task class — not just in memory. Memory captures "who the user is"; skills capture "how to do this class of task for this user."

Examples:
- User says "stop being verbose in code reviews" → update the code review skill
- User says "always use tabs not spaces" → update the coding standards skill
- User says "don't explain, just do it" → update the relevant task skill's pitfalls
