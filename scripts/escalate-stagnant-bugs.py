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
    """Load JSON, with lenient fallback for trailing commas."""
    try:
        with open(path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        try:
            with open(path, "r") as f:
                raw = f.read()
            # Remove trailing commas before closing brackets/braces
            cleaned = re.sub(r",\s*([}\]])", r"\1", raw)
            return json.loads(cleaned)
        except (json.JSONDecodeError, OSError):
            return None


def main() -> int:
    master = load_json(MASTER_CHECKPOINT)
    if master is None:
        print(f"ERROR: Cannot read master checkpoint", file=sys.stderr)
        return 0

    projects = master.get("projects", {})
    if not projects:
        return 0

    any_escalated = False

    for project_name in projects:
        repo_path = os.path.join(REPOS_BASE, project_name)
        checkpoint_path = os.path.join(repo_path, ".checkpoint.json")

        if not os.path.isfile(checkpoint_path):
            continue

        checkpoint = load_json(checkpoint_path)
        if checkpoint is None:
            continue

        spec_gaps = checkpoint.get("spec_gaps", [])
        if not spec_gaps:
            continue

        modified = False
        for gap in spec_gaps:
            status = gap.get("status", "new")

            # Increment cycles_stagnant for any non-escalated, non-fixed gap
            if status not in ("escalated", "fixed"):
                gap["cycles_stagnant"] = gap.get("cycles_stagnant", 0) + 1
                modified = True
                cycles = gap["cycles_stagnant"]

                if cycles >= 3:
                    gap["status"] = "escalated"
                    any_escalated = True
                    print(
                        f"ESCALATED: {gap['item']} (stagnant for {cycles} cycles at priority {gap.get('priority', '?')})"
                    )

        if modified:
            with open(checkpoint_path, "w") as f:
                json.dump(checkpoint, f, indent=2)
                f.write("\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
