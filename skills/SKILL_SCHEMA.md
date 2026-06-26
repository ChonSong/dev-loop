---
name: SKILL_SCHEMA
description: Formal schema for SKILL.md frontmatter fields. Authoritative reference for skill authors and the curator.
---

# SKILL.md Frontmatter Schema

Every `SKILL.md` file MUST start with YAML frontmatter delimited by `---`. The schema below defines all valid fields.

## Required Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `name` | string | Unique skill identifier. Lowercase, hyphens for spaces. No leading `/`. | `systematic-debugging` |
| `description` | string | One-line summary of what the skill does and when to use it. Max 280 chars. | `4-phase root-cause debugging: understand bugs before fixing.` |

## Optional Fields

| Field | Type | Default | Description | Example |
|-------|------|---------|-------------|---------|
| `category` | string | `""` | Grouping namespace. Used for `skills_list(category=...)`. | `software-development` |
| `tags` | list[string] | `[]` | Keyword labels for discovery and scoring. | `[debugging, quality, workflow]` |
| `source` | string | `"local"` | Origin of the skill: `local`, repo name, or URL. | `awesome-hermes-agent` |
| `is_imported` | bool | `false` | Whether skill was imported from external source. | `true` |
| `original_name` | string | _(same as `name`)_ | Preserves original name when `/` was sanitized to `-` at install. | `vendor/skill-name` |
| `related_skills` | list[string] | `[]` | Skills that complement this one. Loaded together for workflows. | `[systematic-debugging, debug-mantra]` |
| `required_commands` | list[string] | `[]` | CLI tools or binaries this skill depends on. Checked at load time. | `[git, docker, gh]` |
| `supersedes` | list[string] | `[]` | **NEW:** Skill names this replaces. The listed skills are considered deprecated when this skill is active. The curator uses this to prune duplicates and rewrite cron job skill references. | `[old-debugging-skill, debug-v1]` |
| `deprecated` | bool | `false` | **NEW:** Marks this skill as obsolete. Should not be loaded or recommended. Use `supersedes` on the replacement skill instead of setting this. Set to `true` only when no replacement exists yet. | `true` |
| `deprecated_in_favor_of` | string | `""` | **NEW:** Name of the skill that replaces this one. Redundant with `supersedes` on the target, but useful for forward references and tooling. | `systematic-debugging` |

## Rules

1. **`name` must be unique** across the entire skills directory. The curator enforces this.
2. **`supersedes` and `deprecated` work together:**
   - When skill A `supersedes: [B, C]`, skills B and C should have `deprecated: true` set.
   - The curator auto-prunes `supersedes` targets from the skill index.
   - Cron jobs referencing superseded skills get their `skills` list rewritten to the replacement.
3. **`deprecated` skills are excluded from:**
   - `skills_list()` output
   - skill-selector scoring
   - The `<available_skills>` system prompt injection
   - Skill discovery and recommendation
4. **`original_name` is auto-set by the installer** when `/` in names is sanitized to `-`. Do not set manually unless migrating.
5. **`required_commands` triggers a pre-flight check** — if any command is missing, a warning is emitted at load time.

## Example

```yaml
---
name: systematic-debugging
description: 4-phase root-cause debugging: understand bugs before fixing.
category: software-development
tags: [debugging, quality, workflow, root-cause]
source: local
is_imported: false
related_skills: [debug-mantra, post-mortem, python-debugpy]
required_commands: []
supersedes: [debug-v1, quick-fix-debug]
---
```

## Deprecated Skill Example

```yaml
---
name: debug-v1
description: Legacy debugging approach — superseded by systematic-debugging.
category: software-development
tags: [debugging, deprecated]
source: local
is_imported: false
deprecated: true
deprecated_in_favor_of: systematic-debugging
---
```

## Migration Guide

When creating a skill that supersedes existing ones:

1. Set `supersedes: [old-skill-name]` in the new skill's frontmatter.
2. Set `deprecated: true` and `deprecated_in_favor_of: new-skill-name` in the old skill.
3. Run the curator to prune the index and update cron references.
4. Verify: `skills_list()` should not return the deprecated skill.
