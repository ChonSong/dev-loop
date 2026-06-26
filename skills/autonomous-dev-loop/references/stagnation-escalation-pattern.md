# Stagnation Escalation Pattern

> Pattern: detect bugs stagnant for N+ cycles, auto-escalate
> Added: 2026-06-25
> Used by: `escalate-stagnant-bugs` cron job (no_agent, :15/:45)

## Problem

Spec gaps in project checkpoints can languish for hours (6+ cycles in the worst case — the advance-to-turn bug) because neither the Coach nor the Player has structural motivation to escalate them. The Coach notes them, the Player skips to the next task, and the gap stays in "new" status forever.

## Solution

A no_agent cron script that:
1. Reads all project checkpoints (derived from master-checkpoint.json)
2. For each spec_gaps entry not already "escalated" or "fixed": increments `cycles_stagnant` by 1
3. When `cycles_stagnant >= 3`: sets `status: "escalated"` and prints a message (which the no_agent cron delivers)

This is pure arithmetic — no LLM needed, runs in <1 second, costs 0 tokens.

## Implementation

Script lives at `~/.hermes/scripts/escalate-stagnant-bugs.py`:

```python
#!/usr/bin/env python3
"""
Auto-escalation script: detects stagnant bugs (spec_gaps with cycles_stagnant >= 3)
and marks them as 'escalated'.

Increments cycles_stagnant each run for any non-escalated, non-fixed gap.
Exits 0 (always). Prints one line per escalation, or stays silent if none.
"""

import json
import os
import re
import sys

MASTER_CHECKPOINT = "/home/sc/repos/dev-loop/master-checkpoint.json"
REPOS_BASE = "/home/sc/repos"


def load_json(path: str) -> dict | None:
    try:
        with open(path) as f:
            return json.load(f)
    except json.JSONDecodeError:
        try:
            with open(path) as f:
                raw = f.read()
            cleaned = re.sub(r",\s*([}\]])", r"\1", raw)
            return json.loads(cleaned)
        except (json.JSONDecodeError, OSError):
            return None


def main() -> int:
    master = load_json(MASTER_CHECKPOINT)
    if master is None:
        print("ERROR: Cannot read master checkpoint", file=sys.stderr)
        return 0

    for project_name in master.get("projects", {}):
        checkpoint_path = os.path.join(REPOS_BASE, project_name, ".checkpoint.json")
        if not os.path.isfile(checkpoint_path):
            continue
        checkpoint = load_json(checkpoint_path)
        if checkpoint is None:
            continue

        modified = False
        for gap in checkpoint.get("spec_gaps", []):
            status = gap.get("status", "new")
            if status not in ("escalated", "fixed"):
                gap["cycles_stagnant"] = gap.get("cycles_stagnant", 0) + 1
                modified = True
                if gap["cycles_stagnant"] >= 3:
                    gap["status"] = "escalated"
                    print(f"ESCALATED: {gap['item']} (stagnant for {gap['cycles_stagnant']} cycles at priority {gap.get('priority', '?')})")

        if modified:
            with open(checkpoint_path, "w") as f:
                json.dump(checkpoint, f, indent=2)
                f.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

## Cron Job Definition

```json
{
  "job_id": "e461becc33cf",
  "name": "escalate-stagnant-bugs",
  "schedule": "15,45 * * * *",
  "no_agent": true,
  "script": "escalate-stagnant-bugs.py",
  "deliver": "local"
}
```

## Key Design Decisions

1. **Increment then escalate** — doing both in one pass means a gap 3 cycles old gets picked up on the 3rd pass, capped at cycles_stagnant=3. There's no 4-cycle wait.
2. **Silent when nothing to escalate** — no_agent mode with empty stdout means zero noise. The user only hears about escalations.
3. **Exit 0 always** — even broken checkpoints produce exit 0 so the cron never errors on bad input.
4. **The script does NOT create tasks in AGENTS.md** — it only marks the gap as "escalated". The Coach or Player picks up the escalated status in their next tick.

## Future Extensions

- Auto-create a P1 task in AGENTS.md when a gap is escalated (steps toward full self-healing)
- Fire a Discord alert for P1 escalated bugs
- Count total cycles a gap has been stagnant before escalation (not just since 0)
