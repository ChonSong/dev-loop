# Coach/Player Adversarial Loop

Based on **dialectical autocoding** from g3 (https://github.com/dhanji/g3) and the Block AI Research paper "Adversarial Cooperation in Code Synthesis" (Dec 2025).

## Core Concept

Two agents with different roles, different models, iterating on the same work. The Player implements. The Coach reviews and validates. This replaces the single-agent "implement and self-report" pattern.

## Architecture

Two cron jobs, offset by ~5 minutes, each with independent model configs:

```
PLAYER CRON     — every 60m, flash/cheap model (e.g. deepseek-v4-flash)
COACH CRON      — offset +5m, stronger model (e.g. claude-sonnet-4)
```

### Player Prompt Template

```markdown
You are the Player in a coach/player adversarial development loop.

## Every Run
1. Walk /home/sc/repos/*/AGENTS.md — find repos with both AGENTS.md + .checkpoint.json
2. For each repo read AGENTS.md (## Tasks) + checkpoint (current_task)
3. Find the next pending task. Round-robin: max 2 consecutive on same project.
4. Load skills from AGENTS.md ## Skills section
5. Execute one unit of work:
   - Understand project context (architecture, conventions)
   - Implement the change
   - Run tests
   - Git commit with descriptive message
6. Update .checkpoint.json (move current_task forward, add to completed)
7. Report: "✅ [project] player: [what was done]. Tests: [result]. Next: [next task]"
```

### Coach Prompt Template

```markdown
You are the Coach in a coach/player adversarial development loop.

## Every Run
1. Read the master checkpoint to find the most recent player completion
2. For that project:
   - Read AGENTS.md — find the success criteria and coach checks for the completed task
   - Read the git diff (most recent commit)
   - Read test output
3. Validate against each success criterion and coach check
4. ALL pass → update checkpoint with coach: "approved"
5. ANY fail:
   - If the fix is straightforward (typo, missing test, wrong file path) → create a corrective commit
   - If the fix is structural (wrong approach, missing feature) → revert the commit and create a fix task in AGENTS.md
   - If unsure → tag for human review
6. Report: "✅ [project] coach: approved" or "❌ [project] coach: failed — [reason]"
```

## Model Configuration

Configure via each cron job's `model` field:

```json
// Player cron
{
  "model": {"provider": "opencode-go", "model": "deepseek-v4-flash"}
}

// Coach cron
{
  "model": {"provider": "anthropic", "model": "claude-sonnet-4"}
}
```

This mirrors g3's separate `[providers.anthropic.coach]` and `[providers.anthropic.player]` blocks in `config.coach-player.example.toml`.

## Reference

- g3 repo: https://github.com/dhanji/g3
- Block AI Research paper: https://block.xyz/documents/adversarial-cooperation-in-code-synthesis.pdf
- g3 coach-player config: https://raw.githubusercontent.com/dhanji/g3/main/config.coach-player.example.toml
