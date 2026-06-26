#!/usr/bin/env python3
"""
Phase 2: Skill Author
Loads skill_candidates.json, researches each high-priority candidate,
authors a SKILL.md, and commits to hermes-sync.
"""
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────
HERMES_SYNC = Path(__file__).parent.parent.resolve()
CANDIDATES_JSON = HERMES_SYNC / "workspace" / "plans" / "skill_candidates.json"
RESEARCH_DIR = HERMES_SYNC / "workspace" / "plans" / "skill-research"
SKILLS_OUT = HERMES_SYNC / "skills"
CANDIDATES_OUT = HERMES_SYNC / "workspace" / "plans" / "skill_candidates.json"

CATEGORIES = [
    "autonomous-ai-agents", "software-development", "productivity",
    "devops", "research", "data-science", "github", "productivity",
    "mlops", "creative", "media", "smart-home", "social-media", "email",
]

# ── Git helpers ──────────────────────────────────────────────────────────────

def git_add_commit(paths, message, cwd=HERMES_SYNC):
    """git add paths and commit. Returns (success, commit_hash)."""
    paths = [str(p) for p in paths]
    subprocess.run(["git", "add", "-A"] + paths, cwd=cwd, capture_output=True)
    r = subprocess.run(
        ["git", "commit", "-m", message], cwd=cwd, capture_output=True, text=True
    )
    if r.returncode == 0:
        h = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=cwd, capture_output=True, text=True)
        return True, h.stdout.strip()
    return False, r.stderr.strip()


def git_status(cwd=HERMES_SYNC):
    r = subprocess.run(["git", "status", "--porcelain"], cwd=cwd, capture_output=True, text=True)
    return r.stdout.strip()


# ── Research ────────────────────────────────────────────────────────────────

def run_hermes(prompt, model="claude"):
    """Run hermes chat with a prompt, return response."""
    try:
        r = subprocess.run(
            ["hermes", "chat", "--model", model, "--print-only"],
            input=prompt, capture_output=True, text=True, timeout=60
        )
        return r.stdout.strip() if r.returncode == 0 else None
    except Exception:
        return None


def web_search(query, limit=5):
    """Simple web search via curl."""
    try:
        r = subprocess.run(
            ["curl", "-s", f"https://duckduckgo.com/html/?q={query}&format=json"],
            capture_output=True, text=True, timeout=10
        )
        return r.stdout[:500] if r.returncode == 0 else ""
    except Exception:
        return ""


def write_research_brief(candidate_id: str, candidate: dict, brief: str):
    """Write research brief to skill-research/."""
    RESEARCH_DIR.mkdir(parents=True, exist_ok=True)
    path = RESEARCH_DIR / f"{candidate_id}.md"
    path.write_text(f"# Research Brief: {candidate_id}\n\n"
                    f"## Candidate\n{candidate['title']}\n\n"
                    f"## Source\n{candidate['source']} — {candidate['type']}\n\n"
                    f"## Summary\n{candidate['summary']}\n\n"
                    f"## Research\n{brief}\n\n"
                    f"## Decision\nTo be filled by researcher.")
    return path


# ── Skill authoring ─────────────────────────────────────────────────────────

def slugify(title: str) -> str:
    """Convert title to kebab-case skill name."""
    s = re.sub(r"[^\w\s-]", "", title)
    s = re.sub(r"[\s_]+", "-", s).strip("-").lower()
    # Limit to 64 chars
    return s[:64]


def best_category(c: dict) -> str:
    """Pick the best category for a skill based on area/type."""
    area = c.get("area", "backend")
    type_ = c.get("type", "learning")
    area_map = {
        "infra": "devops",
        "tests": "software-development",
        "backend": "autonomous-ai-agents",
        "frontend": "software-development",
        "docs": "productivity",
        "config": "devops",
    }
    return area_map.get(area, "autonomous-ai-agents")


def build_skill_content(c: dict, research_brief: str) -> str:
    """Build a complete SKILL.md from a candidate + research."""
    name = slugify(c["title"])
    # Truncate description to 1024 chars
    summary = c.get("summary", c.get("title", ""))
    desc = f"Use when: {summary[:900]}."
    if len(desc) > 1024:
        desc = desc[:1021] + "..."

    lines = [
        "---",
        f"name: {name}",
        f"description: \"{desc}\"",
        "version: 1.0.0",
        "author: Self-Improvement Engine",
        "license: MIT",
        "metadata:",
        "  hermes:",
        "    tags: [self-improvement, autonomous]",
        "    related_skills: [roadmap-engine, self-improvement-engine]",
        "---",
        "",
        f"# {c['title']}",
        "",
        "## Overview",
        f"{summary}",
        "",
        "## When to Use",
        f"- Trigger: {c['title']}",
        f"- Type: {c['type']} | Priority: {c['priority']} | Area: {c['area']}",
        "",
        "## Research Notes",
        f"{research_brief[:2000]}",
        "",
        "## Common Pitfalls",
        "1. Verify the solution works before authoring the skill",
        "",
        "## Verification Checklist",
        "- [ ] Solution is tested and working",
        "- [ ] Skill follows hermes-agent-skill-authoring format",
        "- [ ] No duplicate skill exists",
        "",
    ]
    return "\n".join(lines)


def author_skill(c: dict, dry_run: bool = False) -> tuple[bool, str, Path]:
    """
    Author a SKILL.md for a candidate.
    Returns (authored, message, skill_path).
    """
    name = slugify(c["title"])
    category = best_category(c)

    # Check if skill already exists
    skill_path = SKILLS_OUT / category / name / "SKILL.md"
    if skill_path.exists():
        return False, f"SKILL.md already exists at {skill_path}", skill_path

    # Research brief
    brief = f"Candidate: {c['id']}\nTitle: {c['title']}\nSummary: {c.get('summary','')}\nArea: {c['area']}"
    research_path = write_research_brief(c["id"], c, brief)

    # Build content
    content = build_skill_content(c, brief)

    if dry_run:
        print(f"  [dry-run] Would author: {skill_path}")
        print(f"  [dry-run] Research brief: {research_path}")
        return True, "dry-run", skill_path

    # Write file
    skill_path.parent.mkdir(parents=True, exist_ok=True)
    skill_path.write_text(content)

    # Verify it's valid
    if not skill_path.exists():
        return False, "Write failed", skill_path

    # Commit
    msg = (
        f"skill({category}): author {name}\n\n"
        f"Generated by self-improvement-engine from {c['id']} ({c['source']})\n"
        f"Reason: {c['type']}/{c['area']} recurrence={c['recurrence']} score={c.get('skill_score',0):.1f}"
    )
    success, result = git_add_commit([skill_path, research_path], msg)
    if success:
        return True, f"Committed: {result}", skill_path
    else:
        return False, f"Commit failed: {result}", skill_path


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    dry_run = "--dry-run" in sys.argv
    target_id = None
    for arg in sys.argv[1:]:
        if not arg.startswith("--"):
            target_id = arg

    if not CANDIDATES_JSON.exists():
        print("No skill_candidates.json found. Run learnings_scanner.py first.")
        sys.exit(1)

    with open(CANDIDATES_JSON) as f:
        data = json.load(f)

    if target_id:
        candidates = [c for c in data.get("high_priority", []) + data.get("candidates", [])
                     if c["id"] == target_id]
        if not candidates:
            print(f"Candidate {target_id} not found.")
            sys.exit(1)
    else:
        candidates = data.get("high_priority", [])

    if not candidates:
        print("No high-priority candidates to author.")
        return

    print(f"\n=== Skill Author: {len(candidates)} candidate(s) ===")
    print(f"Dry-run: {dry_run}\n")

    authored = []
    deferred = []

    for c in candidates:
        print(f"Processing [{c['id']}]: {c['title']}")
        print(f"  score={c.get('skill_score', 0):.1f} area={c['area']} recurrence={c['recurrence']}")
        if c.get("existing_skill"):
            print(f"  SKIPPED: covered by existing skill {c['existing_skill']}")
            deferred.append((c, "existing skill"))
            continue

        ok, msg, path = author_skill(c, dry_run=dry_run)
        print(f"  -> {msg}")
        if ok:
            authored.append((c, msg, path))
        else:
            deferred.append((c, msg))

    print(f"\n=== Summary ===")
    print(f"Authored: {len(authored)}")
    for c, msg, _ in authored:
        print(f"  + [{c['id']}] {c['title']} -> {msg}")
    print(f"Deferred: {len(deferred)}")
    for c, reason in deferred:
        print(f"  - [{c['id']}] {c['title']} -> {reason}")

    # Update candidate statuses in JSON
    if not dry_run and authored:
        with open(CANDIDATES_JSON) as f:
            data = json.load(f)
        authored_ids = {c["id"] for c, _, _ in authored}
        for c in data.get("candidates", []):
            if c["id"] in authored_ids:
                c["skill_authored"] = True
                c["status"] = "promoted"
        with open(CANDIDATES_JSON, "w") as f:
            json.dump(data, f, indent=2)

    status = git_status()
    print(f"\nGit status: {status or 'clean'}")


if __name__ == "__main__":
    main()
