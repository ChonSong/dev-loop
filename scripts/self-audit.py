#!/usr/bin/env python3
"""
Self-Audit Engine — Grand SIE Phase 1.5.

Biweekly inward-facing system audit. Scans our own operation for:
1. Manual patterns worth automating (session replay analysis)
2. Recurring Coach rejection reasons (systemic failure patterns)
3. Dead skills (never loaded in 60+ days)
4. Zombie cron jobs (no useful output in 30+ days)
5. System health summary

Outputs a "System Health & What to Automate" brief → Discord.

Schedule: every 2 weeks, Saturday 02:00 UTC.
Cron: no_agent: true, deliver: all (Discord + local).

Exit codes:
    0 — actionable findings found (Discord notified)
    1 — clean audit (silent exit for cron)
    2 — error
"""

import argparse
import json
import os
import sqlite3
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET  # noqa: F401 — available for future extensions
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

try:
    import requests
except ImportError:
    requests = None

# ── Config ──────────────────────────────────────────────────────────────

HERMES_HOME = Path(os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes")))
STATE_DB = HERMES_HOME / "state.db"
RESPONSE_DB = HERMES_HOME / "response_store.db"
CRON_OUTPUT_DIR = HERMES_HOME / "cron" / "output"
SKILLS_DIR = HERMES_HOME / "skills"
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")

# Thresholds
MANUAL_PATTERN_THRESHOLD = 3          # times in 60 days
COACH_REJECTION_THRESHOLD = 3         # same rejection reason in 60 days
DEAD_SKILL_DAYS = 60                  # never loaded
ZOMBIE_CRON_DAYS = 30                 # no useful output
EXPENSIVE_SESSION_COST = 0.50         # threshold to flag expensive sessions
AUDIT_WINDOW_DAYS = 60                # how far back to scan
MIN_CONTENT_LENGTH = 30               # filter out one-word messages

# Known system-prompt noise (role=user but not Sean's genuine requests)
SYSTEM_NOISE_PREFIXES = [
    "[important: the user has invoked",
    "[important: you are running as a scheduled cron",
    "your active task list was preserved",
    "[context compaction — reference only]",
    "you've reached the maximum number of tool",
    "you just executed tool calls but returned an empty",
    "[nonce:",
    "[system:",
    "[Workspace::",
    "your available memory usage",
    "your current session's total",
    "your max allowed is",
]

SYSTEM_NOISE_CONTAINS = [
    "task list was preserved",
    "context compaction",
    "compaction — reference only",
    "active task list was preserved",
    "current task list",
]


# ── Data Model ──────────────────────────────────────────────────────────

@dataclass
class Pattern:
    """A repeated manual request worth automating."""
    category: str         # "question", "command", "frustration", "research"
    pattern: str          # the repeated phrase
    count: int            # occurrences
    recommendation: str   # "autoprompt", "cron", "skill", "coach/player", "skip"
    rationale: str = ""


@dataclass
class CoachTrend:
    """Recurring Coach rejection reason."""
    reason: str
    count: int
    projects: list[str]


@dataclass
class DeadArtifact:
    """An unused or dead automation artifact."""
    name: str
    kind: str              # "skill", "cron", "script", "template"
    path: str
    last_used_days: int
    recommendation: str    # "delete", "pause", "review"


@dataclass
class SystemHealth:
    sessions_30d: int = 0
    cron_runs_30d: int = 0
    total_cost_30d: float = 0.0
    active_projects: int = 0
    skills_loaded: int = 0
    dead_skills: int = 0
    zombie_crons: int = 0
    notes: list[str] = field(default_factory=list)


@dataclass
class AuditBrief:
    date: str
    patterns: list[Pattern]
    coach_trends: list[CoachTrend]
    dead_artifacts: list[DeadArtifact]
    health: SystemHealth
    recommendation: str = ""


# ── Auditors ────────────────────────────────────────────────────────────

def _is_noise(content: str) -> bool:
    """Filter out system prompt noise from genuine user messages."""
    stripped = content.strip().lower()
    for prefix in SYSTEM_NOISE_PREFIXES:
        if stripped.startswith(prefix.lower()):
            return True
    for phrase in SYSTEM_NOISE_CONTAINS:
        if phrase.lower() in stripped:
            return True
    # Filter URLs posted as standalone messages
    if len(stripped) < MIN_CONTENT_LENGTH:
        return True
    if stripped.startswith("http"):
        return True
    # Filter one-word responses
    if len(stripped.split()) == 1:
        return True
    return False


def _classify_pattern(text: str) -> str:
    """Classify a repeated message pattern."""
    lower = text.lower()
    if any(w in lower for w in ["summarise", "summarize", "what is", "explain", "how", "where", "why"]):
        return "question"
    if any(w in lower for w in ["build", "implement", "fix", "add", "create", "deploy", "run"]):
        return "command"
    if any(w in lower for w in ["not happy", "broken", "doesn't work", "still nothing", "why isn't", "frustrating"]):
        return "frustration"
    if any(w in lower for w in ["investigate", "research", "check", "scan", "find"]):
        return "research"
    return "command"


def _recommend_automation(pattern: Pattern) -> str:
    """Recommend the right automation tier for a pattern."""
    if pattern.category == "frustration":
        return "monitor"  # Flag but don't automate — needs root cause fix
    if pattern.category == "question":
        if pattern.count >= 10:
            return "cron"  # High frequency → scheduled report
        elif pattern.count >= 5:
            return "skill"  # Medium frequency → skill with saved knowledge
        return "autoprompt"  # Low frequency → saved prompt template
    if pattern.category == "command":
        if pattern.count >= 7:
            return "cron"
        return "coach/player"
    if pattern.category == "research":
        return "skill"
    return "skip"


def audit_manual_patterns() -> list[Pattern]:
    """Scan session DB for repeated Sean requests."""
    if not STATE_DB.exists():
        return []

    conn = sqlite3.connect(str(STATE_DB))
    cutoff = (datetime.now() - timedelta(days=AUDIT_WINDOW_DAYS)).timestamp()

    cursor = conn.execute("""
        SELECT LOWER(TRIM(content)) as query, COUNT(*) as cnt
        FROM messages
        WHERE role = 'user'
          AND timestamp > ?
          AND LENGTH(content) > ?
        GROUP BY LOWER(SUBSTR(TRIM(content), 1, 80))
        HAVING cnt >= ?
        ORDER BY cnt DESC
        LIMIT 50
    """, (cutoff, MIN_CONTENT_LENGTH, MANUAL_PATTERN_THRESHOLD))

    patterns = []
    for row in cursor.fetchall():
        text, count = row[0], row[1]
        if _is_noise(text):
            continue

        pattern = Pattern(
            category=_classify_pattern(text),
            pattern=text[:120],
            count=count,
            recommendation="skip",
        )
        pattern.recommendation = _recommend_automation(pattern)
        patterns.append(pattern)

    conn.close()
    return patterns


def audit_coach_rejections() -> list[CoachTrend]:
    """Analyze Coach verdicts for recurring rejection reasons."""
    trends = []
    # Check master checkpoint for project list
    master = Path(os.path.expanduser("~/repos/dev-loop/master-checkpoint.json"))
    if not master.exists():
        return trends

    try:
        data = json.loads(master.read_text())
        projects = data.get("projects", {})
    except (json.JSONDecodeError, KeyError):
        return trends

    # Collect rejection reasons from project checkpoints
    reason_counts: dict[str, tuple[int, set[str]]] = {}
    for proj_name, proj_info in projects.items():
        checkpoint_path = Path(proj_info.get("path", "")) / ".checkpoint.json"
        if not checkpoint_path.exists():
            continue

        try:
            cp = json.loads(checkpoint_path.read_text())
            coach = cp.get("coach_review", {})
            findings = coach.get("spec_gaps", []) + coach.get("findings", [])
            for f in findings:
                reason = f.get("description", f.get("item", str(f)))
                if isinstance(reason, str) and len(reason) > 10:
                    key = reason.lower().strip()[:80]
                    if key not in reason_counts:
                        reason_counts[key] = (0, set())
                    cnt, projs = reason_counts[key]
                    reason_counts[key] = (cnt + 1, projs | {proj_name})
        except (json.JSONDecodeError, KeyError, TypeError):
            continue

    for reason, (cnt, projs) in reason_counts.items():
        if cnt >= COACH_REJECTION_THRESHOLD:
            trends.append(CoachTrend(
                reason=reason[:100],
                count=cnt,
                projects=sorted(projs),
            ))

    return sorted(trends, key=lambda t: t.count, reverse=True)


def audit_skill_freshness() -> list[DeadArtifact]:
    """Check skill load counts and file freshness."""
    dead = []
    now = time.time()
    cutoff = now - DEAD_SKILL_DAYS * 86400

    # Enumerate skills
    for skill_dir in SKILLS_DIR.iterdir():
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue

        skill_name = skill_dir.name
        mtime = skill_md.stat().st_mtime

        days_since = int((now - mtime) / 86400)
        if days_since > DEAD_SKILL_DAYS:
            dead.append(DeadArtifact(
                name=skill_name,
                kind="skill",
                path=str(skill_dir),
                last_used_days=days_since,
                recommendation="delete" if days_since > 120 else "review",
            ))

    # Sort by age (oldest first)
    return sorted(dead, key=lambda d: d.last_used_days, reverse=True)[:10]


def audit_cron_freshness() -> list[DeadArtifact]:
    """Check cron output recency for zombie jobs."""
    dead = []
    now = time.time()
    cutoff = now - ZOMBIE_CRON_DAYS * 86400

    if not CRON_OUTPUT_DIR.exists():
        return dead

    # Group output files by job_id prefix
    job_dirs: dict[str, list[Path]] = {}
    for entry in CRON_OUTPUT_DIR.iterdir():
        if entry.is_dir():
            job_dirs[entry.name] = list(entry.iterdir())

    # Also check raw output files
    for entry in CRON_OUTPUT_DIR.iterdir():
        if entry.is_file() and entry.name.endswith("-latest.txt"):
            job_id = entry.name.replace("-latest.txt", "")
            mtime = entry.stat().st_mtime
            if mtime < cutoff:
                dead.append(DeadArtifact(
                    name=job_id,
                    kind="cron",
                    path=str(entry),
                    last_used_days=int((now - mtime) / 86400),
                    recommendation="pause",
                ))

    return sorted(dead, key=lambda d: d.last_used_days, reverse=True)


def audit_system_health() -> SystemHealth:
    """Aggregate system health metrics."""
    health = SystemHealth()

    if STATE_DB.exists():
        conn = sqlite3.connect(str(STATE_DB))
        cutoff = (datetime.now() - timedelta(days=30)).timestamp()

        # Session counts
        cursor = conn.execute(
            "SELECT COUNT(*) FROM sessions WHERE started_at > ?", (cutoff,)
        )
        health.sessions_30d = cursor.fetchone()[0]

        # Cost
        cursor = conn.execute(
            "SELECT COALESCE(SUM(estimated_cost_usd), 0) FROM sessions WHERE started_at > ?",
            (cutoff,),
        )
        health.total_cost_30d = cursor.fetchone()[0]

        # Cron runs
        cursor = conn.execute(
            "SELECT COUNT(*) FROM sessions WHERE source = 'cron' AND started_at > ?",
            (cutoff,),
        )
        health.cron_runs_30d = cursor.fetchone()[0]

        conn.close()

    # Active projects (from checkpoints)
    master = Path(os.path.expanduser("~/repos/dev-loop/master-checkpoint.json"))
    if master.exists():
        try:
            data = json.loads(master.read_text())
            projects = data.get("projects", {})
            health.active_projects = len(projects)
        except (json.JSONDecodeError, KeyError):
            pass

    # Skills loaded count
    health.skills_loaded = len([d for d in SKILLS_DIR.iterdir()
                                if d.is_dir() and (d / "SKILL.md").exists()])
    if not health.skills_loaded:
        health.skills_loaded = 0

    # Dead/zombie counts (quick estimate — full audit runs separately)
    dead_skills = audit_skill_freshness()
    health.dead_skills = len(dead_skills)

    zombie_crons = audit_cron_freshness()
    health.zombie_crons = len(zombie_crons)

    # Notes
    if health.sessions_30d > 5000:
        health.notes.append("High session volume — consider pruning old sessions")
    if health.cron_runs_30d < 100:
        health.notes.append("Low cron volume — check if jobs are running")
    if health.total_cost_30d > 10:
        health.notes.append(f"Cost trending high (${health.total_cost_30d:.2f}/30d)")
    if health.dead_skills > 5:
        health.notes.append(f"{health.dead_skills} dead skills — prune recommended")

    return health


# ── Synthesis ───────────────────────────────────────────────────────────

def synthesize(
    patterns: list[Pattern],
    coach_trends: list[CoachTrend],
    dead: list[DeadArtifact],
    health: SystemHealth,
) -> AuditBrief:
    return AuditBrief(
        date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        patterns=patterns,
        coach_trends=coach_trends,
        dead_artifacts=dead,
        health=health,
        recommendation=_generate_recommendation(patterns, coach_trends, dead),
    )


def _generate_recommendation(
    patterns: list[Pattern],
    coach_trends: list[CoachTrend],
    dead: list[DeadArtifact],
) -> str:
    parts = []
    build_candidates = [p for p in patterns if p.recommendation in ("cron", "skill")]
    if build_candidates:
        top = build_candidates[0]
        parts.append(
            f"Top automation candidate: *{top.pattern[:60]}* "
            f"({top.count}× in {AUDIT_WINDOW_DAYS}d). "
            f"Recommend: {top.recommendation}."
        )

    if coach_trends:
        top_ct = coach_trends[0]
        parts.append(
            f"Systemic Coach trend: '{top_ct.reason[:60]}' "
            f"({top_ct.count}× across {len(top_ct.projects)} projects)."
        )

    delete_candidates = [d for d in dead if d.recommendation == "delete"]
    if delete_candidates:
        parts.append(f"{len(delete_candidates)} dead skills ready for deletion.")

    if not parts:
        return "System healthy. No urgent automation opportunities this cycle."

    return " ".join(parts)


# ── Discord Delivery ────────────────────────────────────────────────────

def format_discord(brief: AuditBrief) -> str:
    """Compact Discord message."""
    lines = [f"## System Health & What to Automate — {brief.date}", ""]

    h = brief.health
    lines.append(
        f"**Health**: {h.sessions_30d} sessions, {h.cron_runs_30d} cron runs, "
        f"${h.total_cost_30d:.2f}/30d, {h.active_projects} active projects, "
        f"{h.skills_loaded} skills loaded"
    )
    if h.notes:
        for note in h.notes:
            lines.append(f"  ⚠️ {note}")
    lines.append("")

    if brief.patterns:
        lines.append("**Automation Candidates**")
        for p in brief.patterns[:8]:
            emoji = {"cron": "🤖", "skill": "📚", "autoprompt": "💬",
                     "coach/player": "🔄", "monitor": "👀", "skip": "➖"}
            lines.append(
                f"  {emoji.get(p.recommendation, '•')} [{p.count}×] "
                f"*{p.pattern[:70]}* → {p.recommendation}"
            )
        lines.append("")

    if brief.coach_trends:
        lines.append("**Systemic Coach Trends**")
        for ct in brief.coach_trends[:5]:
            lines.append(
                f"  • {ct.reason[:70]} ({ct.count}× in "
                f"{', '.join(ct.projects[:2])})"
            )
        lines.append("")

    if brief.dead_artifacts:
        delete = [d for d in brief.dead_artifacts if d.recommendation == "delete"]
        pause = [d for d in brief.dead_artifacts if d.recommendation == "pause"]
        if delete:
            lines.append(f"**Dead Skills** ({len(delete)} ready to delete):")
            for d in delete[:5]:
                lines.append(f"  • {d.name} ({d.last_used_days}d unused)")
        if pause:
            lines.append(f"**Zombie Crons** ({len(pause)} ready to pause):")
            for d in pause[:5]:
                lines.append(f"  • {d.name} ({d.last_used_days}d idle)")
        lines.append("")

    if brief.recommendation:
        lines.append(f"**Top Recommendation:** {brief.recommendation}")

    return "\n".join(lines)


def format_markdown(brief: AuditBrief) -> str:
    """Full markdown report."""
    lines = [f"# System Health & What to Automate — {brief.date}", ""]

    lines.append("## System Health")
    h = brief.health
    lines.append(f"- Sessions (30d): {h.sessions_30d}")
    lines.append(f"- Cron runs (30d): {h.cron_runs_30d}")
    lines.append(f"- Total cost (30d): ${h.total_cost_30d:.2f}")
    lines.append(f"- Active projects: {h.active_projects}")
    lines.append(f"- Skills loaded: {h.skills_loaded}")
    if h.notes:
        for note in h.notes:
            lines.append(f"- ⚠️ {note}")
    lines.append("")

    if brief.patterns:
        lines.append("## Automation Candidates")
        for p in brief.patterns[:10]:
            lines.append(f"- [{p.count}×] ({p.category}) {p.pattern[:80]}")
            lines.append(f"  → Recommend: {p.recommendation}")
        lines.append("")

    if brief.coach_trends:
        lines.append("## Systemic Coach Trends")
        for ct in brief.coach_trends[:8]:
            lines.append(f"- {ct.reason[:80]} ({ct.count}×)")
            lines.append(f"  Projects: {', '.join(ct.projects)}")
        lines.append("")

    if brief.dead_artifacts:
        lines.append("## Dead Automation")
        for d in brief.dead_artifacts[:10]:
            lines.append(
                f"- [{d.kind}] {d.name} — {d.last_used_days}d unused → {d.recommendation}"
            )
        lines.append("")

    if brief.recommendation:
        lines.append(f"## Recommendation\n{brief.recommendation}")

    return "\n".join(lines)


def deliver_discord(brief: AuditBrief) -> bool:
    if not DISCORD_WEBHOOK_URL:
        print("[WARN] DISCORD_WEBHOOK_URL not set")
        return False

    content = format_discord(brief)
    if len(content) > 2000:
        content = content[:1997] + "..."

    payload = {
        "content": content,
        "username": "Grand SIE — Self-Audit",
        "avatar_url": "https://i.imgur.com/AfFp7pu.png",
    }

    try:
        if requests:
            requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=15)
        else:
            data = json.dumps(payload).encode()
            req = urllib.request.Request(
                DISCORD_WEBHOOK_URL, data=data,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                resp.read()
        print(f"[OK] Audit brief delivered to Discord")
        return True
    except Exception as e:
        print(f"[ERROR] Discord delivery failed: {e}", file=sys.stderr)
        return False


# ── Main ────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Self-Audit Engine")
    parser.add_argument("--dry-run", action="store_true",
                       help="Print brief to stdout")
    parser.add_argument("--deliver", choices=["discord", "stdout", "none"],
                       default="discord")
    parser.add_argument("--section", choices=["patterns", "coach", "dead", "health"],
                       help="Run only one audit section")
    args = parser.parse_args()

    if args.section == "patterns":
        patterns = audit_manual_patterns()
        coach_trends, dead, health = [], [], SystemHealth()
    elif args.section == "coach":
        coach_trends = audit_coach_rejections()
        patterns, dead, health = [], [], SystemHealth()
    elif args.section == "dead":
        dead = audit_skill_freshness() + audit_cron_freshness()
        patterns, coach_trends, health = [], [], SystemHealth()
    elif args.section == "health":
        health = audit_system_health()
        patterns, coach_trends, dead = [], [], []
    else:
        patterns = audit_manual_patterns()
        coach_trends = audit_coach_rejections()
        dead = audit_skill_freshness() + audit_cron_freshness()
        health = audit_system_health()

    brief = synthesize(patterns, coach_trends, dead, health)

    has_findings = bool(
        [p for p in brief.patterns if p.recommendation != "skip"]
        or brief.coach_trends
        or brief.dead_artifacts
        or brief.health.notes
    )

    if args.dry_run:
        print(format_markdown(brief))
    elif args.deliver == "discord":
        if has_findings:
            deliver_discord(brief)
        else:
            print("[OK] Clean audit — nothing to report")
    elif args.deliver == "stdout":
        print(format_markdown(brief))

    sys.exit(0 if has_findings else 1)


if __name__ == "__main__":
    main()
