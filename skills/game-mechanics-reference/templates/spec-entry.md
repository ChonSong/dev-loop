---
title: Spec Entry Template
description: Boilerplate markdown for a new spec entry that captures a mechanic, its rule, and external reference.
---

# {{Mechanic Title}}

## Rule Summary
- **Core rule:** {{One‑sentence summary of the mechanic}}.
- **Key constraints:** {{Bullet list of constraints (e.g., turn restriction, border limits)}}.

## External Reference
- **Source:** {{URL or document reference}}.
- **Version consulted:** {{Date or version number}}.

## Implementation Checklist
- [ ] Verify behavior against the external source.
- [ ] Add unit tests that cover the rule.
- [ ] Update `Spec.md` with this entry under `## External References`.
- [ ] Reference the entry from relevant source files or documentation.

*Create a matching `references/<topic>.md` file to store the full external citation and any additional details.*