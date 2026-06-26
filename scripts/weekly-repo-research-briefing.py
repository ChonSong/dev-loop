#!/usr/bin/env python3
"""Wrapper: weekly repo research briefing for cron delivery.

Runs research-briefing.py from seans-reporepo with an interesting tag
intersection (agent + LLM — AI agent ecosystem) and outputs the briefing.
Designed to be used with `hermes cron create --no-agent --script`.
"""
import subprocess
import sys
from pathlib import Path

REPO_DIR = Path("/home/sc/repos/seans-reporepo")
SCRIPT = REPO_DIR / "scripts" / "research-briefing.py"

TAGS = "agent,llm"  # Agent + LLM intersection — AI agent ecosystem
ANY_MODE = False     # intersection (ALL tags must match)

def main():
    if not SCRIPT.exists():
        print(f"ERROR: research-briefing.py not found at {SCRIPT}", file=sys.stderr)
        sys.exit(1)

    cmd = [sys.executable, str(SCRIPT), "--tags", TAGS]
    if ANY_MODE:
        cmd.append("--any")

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_DIR))

    if result.returncode != 0:
        print(f"ERROR: research-briefing.py failed (exit {result.returncode})", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)

    print(result.stdout)
    sys.exit(0)

if __name__ == "__main__":
    main()
