# Skill Library Hygiene — Audit Checklist

After every major project, run this audit.

## 1. Name Collision Check

```bash
find ~/.hermes/skills -name "SKILL.md" -exec dirname {} \; | awk -F/ '{print $NF}' | sort | uniq -d
```

For each collision:
- Flat stub (≤30 lines) vs categorized (≥100 lines): **delete the flat stub**
- Both substantial: **merge** into categorized, delete flat
- Both categorized: keep both, note the collision

## 2. Frontmatter Standardization

Every skill should have:
```yaml
---
name: <skill-name>
description: "<what it does>"
version: "2.0.0"
author: Sean
license: MIT
metadata:
  hermes:
    category: <category>
    tags: [tag1, tag2]
---
```

## 3. Project-Specific Content Extraction

If a skill contains project-specific code/examples:
- Extract to `references/<topic>.md`
- Replace in SKILL.md with a one-line pointer

## 4. Flat Stubs Already Deleted

- `skills/repo-init` → `skills/devops/repo-init`
- `skills/test-driven-development` → `skills/software-development/test-driven-development`
- `skills/blueprint` → `skills/planning/blueprint`
- `skills/vite-patterns` → `skills/software-development/vite-patterns`
- `skills/e2e-testing` → merged into `skills/software-development/e2e-testing`
- `skills/docker-patterns` → consolidated into `skills/devops/docker-patterns`

## 5. Remaining Collisions (External Plugins)

- `test-driven-development`: `obra/` vs `software-development/`
- `blueprint`: `planning/` vs `creative/baoyu-article-illustrator/references/styles/blueprint.md`
