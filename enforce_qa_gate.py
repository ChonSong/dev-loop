#!/usr/bin/env python3
"""Post-cycle verification — rejects approvals that lack browser QA evidence.

Inject as a cron shell hook AFTER the Coach runs. Reads the checkpoint notes
and verifies they contain actual interaction evidence, not just infrastructure checks.

Usage:
    python3 enforce_qa_gate.py --project polytopia-clone

Exit codes:
    0 — Pass (QA evidence found)
    1 — Fail (no browser QA evidence)
    2 — Fail (can't read checkpoint)
"""

import argparse
import json
import re
import sys
from pathlib import Path


# Required evidence patterns per project type
CANVAS_GAME_EVIDENCE = [
    r"game phase",
    r"currentPhase",
    r"turn",
    r"humanTribe",
    r"city",
    r"unit",
    r"__PHASER_GAME__",
    r"(console|game state)",
    r"(browser|subagent)",
]

WEB_APP_EVIDENCE = [
    r"browser",
    r"subagent",
    r"(navigation|page load)",
    r"console error",
    r"(200|status)",
    r"(visual|interaction).*(comparison|check|verif)",
    r"pages? (compared|loaded|checked|inspected)",
]

FORBIDDEN_PATTERNS = [
    r"(skill|qa skill).*(not installed|unavailable|missing)",
    r"visual comparison skipped",
    r"no browser QA",
    r"regression check only",
]

INSUFFICIENT_PATTERNS = [
    r"only.*(curl|ss|pytest|port)",
    r"(just|only).*health",
    r"nothing.*(to review|actionable)",
    r"skipped.*(browser|QA|game)",
    r"no.*regression",
]


def read_checkpoint(checkpoint_path: str) -> dict | None:
    """Read .checkpoint.json from the project repo."""
    path = Path(checkpoint_path) / ".checkpoint.json"
    if not path.exists():
        # Try repos path
        path = Path(checkpoint_path) / ".checkpoint.json"
        if not path.exists():
            return None
    return json.loads(path.read_text())


def check_evidence(notes: str, evidence_patterns: list[str]) -> list[str]:
    """Check which evidence patterns are matched in the notes."""
    matched = []
    for pattern in evidence_patterns:
        if re.search(pattern, notes, re.IGNORECASE):
            matched.append(pattern)
    return matched


def check_forbidden(notes: str, forbidden_patterns: list[str]) -> list[str]:
    """Check for forbidden evasion patterns."""
    found = []
    for pattern in forbidden_patterns:
        if re.search(pattern, notes, re.IGNORECASE):
            found.append(pattern)
    return found


def check_insufficient(notes: str, insufficient_patterns: list[str]) -> list[str]:
    """Check for insufficient-work patterns."""
    found = []
    for pattern in insufficient_patterns:
        if re.search(pattern, notes, re.IGNORECASE):
            found.append(pattern)
    return found


def main():
    parser = argparse.ArgumentParser(
        description="Enforce QA evidence gate — reject approvals that lack browser QA",
    )
    parser.add_argument("--project", required=True, help="Project name")
    parser.add_argument("--repo", default=f"{Path.home()}/repos", help="Repos root directory")
    parser.add_argument("--type", default="canvas", choices=["canvas", "web", "api"],
                        help="Project type for evidence requirements")
    parser.add_argument("--verbose", action="store_true", help="Detailed output")

    args = parser.parse_args()

    # Find the project repo
    repo_dir = Path(args.repo) / args.project
    if not repo_dir.exists():
        print(f"ERROR: Repo not found at {repo_dir}")
        sys.exit(2)

    checkpoint = read_checkpoint(str(repo_dir))
    if not checkpoint:
        print(f"ERROR: .checkpoint.json not found in {repo_dir}")
        sys.exit(2)

    # Get coach review notes
    coach = checkpoint.get("coach_review", {})
    notes = coach.get("notes", "")

    if not notes:
        print("FAIL: No coach_review.notes found — Coach didn't write a verdict?")
        sys.exit(1)

    if args.verbose:
        print(f"--- Verdict notes ---\n{notes}\n---")

    # Select evidence patterns based on project type
    evidence_patterns = CANVAS_GAME_EVIDENCE if args.type == "canvas" else WEB_APP_EVIDENCE

    # Check for forbidden evasion patterns
    forbidden = check_forbidden(notes, FORBIDDEN_PATTERNS)
    if forbidden:
        print(f"FAIL: Coach used forbidden evasion pattern(s): {forbidden}")
        print(f"  Match: {notes[:200]}...")
        sys.exit(1)

    # Check for insufficient-work patterns
    insufficient = check_insufficient(notes, INSUFFICIENT_PATTERNS)
    if insufficient:
        print(f"FAIL: Coach used insufficient-work pattern(s): {insufficient}")
        print("  Project needs actual browser QA, not health-check shortcuts.")
        sys.exit(1)

    # Check for required evidence
    matched = check_evidence(notes, evidence_patterns)

    if args.verbose:
        print(f"Required patterns: {evidence_patterns}")
        print(f"Matched: {matched}")

    # Canvas games need at least 3 evidence markers
    min_evidence = 3 if args.type == "canvas" else 2

    if len(matched) < min_evidence:
        print(f"FAIL: Only {len(matched)}/{min_evidence} evidence patterns matched")
        print(f"  Required: {evidence_patterns}")
        print(f"  Matched: {matched}")
        sys.exit(1)

    print(f"PASS: {len(matched)} evidence patterns matched")
    sys.exit(0)


if __name__ == "__main__":
    main()
