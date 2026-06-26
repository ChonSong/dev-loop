# Hybrid Orchestrator Skill

## Overview

This skill enables OpenClaw agents to classify incoming tasks and recommend the appropriate execution path: OVERSTORY, OPENCLAW, HYBRID, or DIRECT.

## When to Use

Invoke this skill when:
- Receiving a task that will take more than 10 minutes
- Task scope involves multiple files or complex requirements
- Task involves production systems (higher risk)
- You're unsure whether to spawn child agents or handle directly
- Task requires specialist tools (memory, knowledge, research)

## Classification Criteria

### Duration
- **>10 min** = Overstory/Hybrid candidate
- **<=10 min** = Direct (prefer OpenClaw for speed)

### Tools Required
- **OpenClaw specialists**: memory, knowledge-manager, researcher, skills, long-term patterns
- **Overstory specialists**: worktree isolation, quality gates, mail protocol, merge

### Risk Level
- **High risk**: production, database, auth, migration, payment → HYBRID or OPENCLAW
- **Low risk**: safe to iterate → OVERSTORY

### Certainty
- **High certainty**: clear spec, defined requirements → OVERSTORY
- **Low certainty**: exploratory, debugging → OPENCLAW

## Decision Matrix

| Approach | Conditions |
|----------|------------|
| OVERSTORY | duration > 10min, certainty = high, risk = low |
| OPENCLAW | requires specialist agents, exploratory work |
| HYBRID | duration > 10min, risk = high OR certainty = low |
| DIRECT | duration <= 10min, simple task |

## Usage

```bash
# From any agent context, analyze a task:
# 1. Identify task complexity
# 2. Check tool requirements
# 3. Assess risk and certainty
# 4. Make recommendation

# Example decision flow:
Task: "Add OAuth to the dashboard"
- Duration: ~30 min (multi-file changes)
- Tools: code, tests (generic + overstory)
- Risk: auth = high
- Certainty: medium (spec exists but may need design)
→ Recommend: HYBRID (Overstory execution + OpenClaw oversight)
```

## Integration Points

- Wrapper script: `workspace/scripts/hybrid-route.sh`
- Heuristics: `workspace/scripts/heuristics.json`
- Claude Code reference: System context includes this capability
- Skills location: `workspace/skills/` (symlinked from `.openclaw/skills/`)

## Examples

**Overstory Task:**
> "Add user authentication with tests to the dashboard"
- Classification: OVERSTORY
- Rationale: Clear spec, multi-file, quality gates beneficial

**OpenClaw Task:**
> "Debug why the memory system stopped persisting"
- Classification: OPENCLAW
- Rationale: Requires exploratory work, memory specialist

**Hybrid Task:**
> "Migrate production database schema"
- Classification: HYBRID
- Rationale: High risk, needs oversight during execution