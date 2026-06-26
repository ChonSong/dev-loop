#!/usr/bin/env python3
"""
Phase 1: Learnings Scanner
Scans roadmap.json learnings + memory/.learnings/ for skill candidates.
Outputs skill_candidates.json ranked by skill_score.
"""
import json
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

# ── Paths ────────────────────────────────────────────────────────────────────
HERMES_SYNC = Path(__file__).parent.parent.resolve()
ROADMAP_JSON = HERMES_SYNC / "workspace" / "plans" / "roadmap.json"
LEARNINGS_DIR = HERMES_SYNC / "memory" / ".learnings"
CANDIDATES_OUT = HERMES_SYNC / "workspace" / "plans" / "skill_candidates.json"
SKILLS_DIR = HERMES_SYNC / "skills"

# ── Weights ─────────────────────────────────────────────────────────────────
PRIORITY_WEIGHT = {"critical": 40, "high": 30, "medium": 20, "low": 10}
AREA_MULTIPLIER = {
    "infra": 1.3, "tests": 1.2, "backend": 1.1,
    "frontend": 1.0, "docs": 0.8, "config": 0.9,
}
TYPE_WEIGHT = {"error": 0.9, "learning": 0.7, "feature": 0.6}

# ── Helpers ─────────────────────────────────────────────────────────────────

def parse_iso_timestamp(ts: str) -> Optional[datetime]:
    try:
        ts = ts.replace("Z", "+00:00")
        return datetime.fromisoformat(ts)
    except Exception:
        return None


def days_since(ts_str: str) -> float:
    ts = parse_iso_timestamp(ts_str)
    if not ts:
        return 999.0
    now = datetime.now(timezone(timedelta(hours=10)))
    # Make ts timezone-aware if it isn't
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone(timedelta(hours=10)))
    return (now - ts).total_seconds() / 86400.0


def parse_learnings_md(path: Path, entry_type: str) -> list[dict]:
    if not path.exists():
        return []
    content = path.read_text()
    # Split on ## [ID] boundaries
    parts = re.split(r"\n## \[", content)
    results = []
    for i, part in enumerate(parts):
        if not part.strip():
            continue
        full = ("## [" + part) if i > 0 else part
        id_m = re.search(r"## \[([^\]]+)\]", full)
        if not id_m:
            continue
        entry_id = id_m.group(1)

        def fld(pat, default=None):
            m = re.search(pat, full)
            return m.group(1).strip().lower() if m else default

        priority = fld(r"\*\*Priority[:\*]+\s*(\w+)", "medium")
        status = fld(r"\*\*Status[:\*]+\s*(\w+)", "pending")
        area = fld(r"\*\*Area[:\*]+\s*(\w+)", "backend")
        rec_m = re.search(r"Recurrence-Count:\s*(\d+)", full)
        recurrence = int(rec_m.group(1)) if rec_m else 1
        pk_m = re.search(r"Pattern-Key:\s*([^\s]+)", full)
        pattern_key = pk_m.group(1) if pk_m else ""
        logged_m = re.search(r"\*\*Logged[:\*]+\s*([^\n]+)", full)
        logged = logged_m.group(1).strip() if logged_m else ""
        skill_authored = bool(re.search(r"Skill-Authored|Skill-Path", full))

        # Summary: first non-meta line
        summary = ""
        lines = full.split("\n")
        in_meta = False
        for line in lines:
            if line.strip().startswith("**"):
                in_meta = True
                continue
            if in_meta and line.strip() and not line.startswith("#"):
                summary = line.strip().strip("-* ")
                break
            elif not in_meta and line.strip() and not line.startswith("#"):
                summary = line.strip()
                break

        results.append({
            "id": entry_id,
            "source": str(path.relative_to(HERMES_SYNC)),
            "type": entry_type,
            "title": entry_id,
            "summary": summary[:200],
            "priority": priority,
            "status": status,
            "area": area,
            "recurrence": recurrence,
            "pattern_key": pattern_key,
            "logged": logged,
            "skill_authored": skill_authored,
        })
    return results


def parse_roadmap_learnings() -> list[dict]:
    if not ROADMAP_JSON.exists():
        return []
    with open(ROADMAP_JSON) as f:
        roadmap = json.load(f)
    results = []
    for lr in roadmap.get("learnings", []):
        results.append({
            "id": lr.get("id", f"RLRN-{len(results)+1:03d}"),
            "source": "roadmap.json",
            "type": lr.get("type", "learning"),
            "title": lr.get("title", ""),
            "summary": lr.get("observation", "")[:200],
            "priority": lr.get("priority", "medium"),
            "status": lr.get("status", "pending"),
            "area": lr.get("area", "backend"),
            "recurrence": lr.get("recurrence_count", 1),
            "pattern_key": lr.get("pattern_key", ""),
            "logged": lr.get("logged_at", ""),
            "skill_authored": bool(lr.get("skill_authored")),
        })
    return results


def score_candidate(c: dict) -> float:
    if c.get("skill_authored") or c.get("status") in ("wont_fix", "resolved", "promoted"):
        return 0.0
    pw = PRIORITY_WEIGHT.get(c["priority"], 20)
    am = AREA_MULTIPLIER.get(c["area"], 1.0)
    tw = TYPE_WEIGHT.get(c["type"], 0.7)
    rec = c.get("recurrence", 1)
    rm = 1.5 if rec >= 5 else 1.2 if rec >= 3 else 1.0 if rec >= 2 else 0.8
    if c.get("logged"):
        rd = days_since(c["logged"])
        recency_boost = 1.2 if rd < 7 else 1.0 if rd < 30 else 0.8
    else:
        recency_boost = 1.0
    base = pw * am * tw * rm * recency_boost
    sm = {"pending": 1.0, "in_progress": 0.5}.get(c["status"], 1.0)
    return min(100.0, base * sm)


def is_high_priority(c: dict) -> bool:
    if c.get("skill_score", 0) >= 50:
        return True
    if c.get("recurrence", 1) >= 3:
        return True
    if c["priority"] in ("critical", "high") and c["area"] == "infra":
        return True
    return False


def existing_skill_for(c: dict) -> Optional[str]:
    if not SKILLS_DIR.exists():
        return None
    words = [w.lower() for w in re.findall(r"\w+", c["title"]) if len(w) > 4]
    if not words:
        return None
    for sp in SKILLS_DIR.rglob("SKILL.md"):
        try:
            content = sp.read_text().lower()
            if all(w in content for w in words[:3]):
                return str(sp.relative_to(SKILLS_DIR))
        except Exception:
            pass
    return None


def scan_all() -> dict:
    all_candidates = []
    for lr in parse_roadmap_learnings():
        all_candidates.append(lr)
    for fname, etype in [
        ("LEARNINGS.md", "learning"),
        ("ERRORS.md", "error"),
        ("FEATURE_REQUESTS.md", "feature"),
    ]:
        for entry in parse_learnings_md(LEARNINGS_DIR / fname, etype):
            all_candidates.append(entry)

    for c in all_candidates:
        c["skill_score"] = score_candidate(c)
        c["existing_skill"] = existing_skill_for(c)
        c["high_priority"] = is_high_priority(c)

    candidates = [c for c in all_candidates if c["skill_score"] > 0]
    candidates.sort(key=lambda x: x["skill_score"], reverse=True)
    high_priority = [
        c for c in candidates
        if c.get("high_priority") and c["skill_score"] >= 25 and not c.get("existing_skill")
    ]

    return {
        "scanned_at": datetime.now(timezone(timedelta(hours=10))).isoformat(),
        "total_scanned": len(all_candidates),
        "candidates": candidates[:20],
        "high_priority": high_priority[:5],
        "stats": {
            "error_count": sum(1 for c in all_candidates if c["type"] == "error"),
            "learning_count": sum(1 for c in all_candidates if c["type"] == "learning"),
            "feature_count": sum(1 for c in all_candidates if c["type"] == "feature"),
        }
    }


def write_output(result: dict):
    CANDIDATES_OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(CANDIDATES_OUT, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\n=== Learnings Scanner Report ===")
    print(f"Scanned: {result['scanned_at']}")
    print(f"Total: {result['total_scanned']} | Errors: {result['stats']['error_count']} | Learnings: {result['stats']['learning_count']} | Features: {result['stats']['feature_count']}")
    print(f"Candidates (score>0): {len(result['candidates'])} | High-priority: {len(result['high_priority'])}")
    for i, c in enumerate(result["candidates"][:5], 1):
        hp = " [HIGH]" if c.get("high_priority") else ""
        dup = f" (dup:{c.get('existing_skill')})" if c.get("existing_skill") else ""
        print(f"  {i}. [{c['id']}] {c['title']} score={c['skill_score']:.1f}{hp}{dup}")
        print(f"      area={c['area']} priority={c['priority']} recurrence={c['recurrence']} status={c['status']}")
    if result["high_priority"]:
        print(f"\nReady for authoring:")
        for c in result["high_priority"]:
            print(f"  -> [{c['id']}] {c['title']} score={c['skill_score']:.1f}")
    print(f"\nOutput: {CANDIDATES_OUT}")
    return result


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    result = write_output(scan_all())
    if not dry_run:
        print(f"\n[dry-run={dry_run}] Run skill_author.py next")
