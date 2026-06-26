"""
Self-Improvement Hook for Hermes

session:start  -> reads .learnings/ and injects a reminder into memory/
session:end    -> writes a capture prompt for the next session
"""

import os
from pathlib import Path
from datetime import datetime, timezone

HERMES_HOME = Path(os.environ.get("HERMES_HOME", "/opt/data"))
MEMORY_DIR = HERMES_HOME / "memory"
LEARNINGS_DIR = HERMES_HOME / "skills" / "openclaw-imports" / "self-improving-agent" / ".learnings"


def _count_entries(content: str) -> int:
    count = 0
    for line in content.split("\n"):
        stripped = line.strip()
        if stripped.startswith("- ") or stripped.startswith("* "):
            count += 1
    return count


def _read_learnings() -> dict:
    results = {}
    for name in ["LEARNINGS.md", "ERRORS.md", "FEATURE_REQUESTS.md"]:
        path = LEARNINGS_DIR / name
        if path.exists():
            content = path.read_text().strip()
            count = _count_entries(content)
            results[name] = (count, content)
        else:
            results[name] = (0, "")
    return results


def _write_session_reminder(learnings: dict, session_id: str) -> None:
    entries = []
    has_any = False
    for name, (count, content) in learnings.items():
        if count > 0:
            has_any = True
            label = name.replace(".md", "").replace("_", " ")
            entries.append(f"- **{label}**: {count} new entry(ies) to review")

    reminder_path = MEMORY_DIR / "HOOK_SELF_IMPROVEMENT_REMINDER.md"

    if not has_any:
        if reminder_path.exists():
            reminder_path.unlink()
        return

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines_out = [
        f"# Self-Improvement Reminder — {ts}",
        "",
        "Review these learnings from recent sessions before continuing:",
        "",
        *entries,
        "",
        "## Quick Log (before ending this session)",
        "",
        "If you have learned anything new, append to the appropriate file:",
        "- `.learnings/LEARNINGS.md` — corrections, discoveries, better approaches",
        "- `.learnings/ERRORS.md` — command/operation failures",
        "- `.learnings/FEATURE_REQUESTS.md` — missing capabilities the user wanted",
        "",
        "Promote proven patterns to SOUL.md or relevant skill files.",
        "",
        "---",
        f"_This reminder from session:start hook — id={session_id[:8]}_",
    ]
    reminder_path.write_text("\n".join(lines_out))


def _write_end_prompt(session_id: str) -> None:
    path = MEMORY_DIR / "NEXT_SESSION_CAPTURE_PROMPT.md"
    lines_out = [
        "# Session-End Capture Prompt",
        "",
        "Before this session ends, consider logging:",
        "",
        "- **Corrections** — something the user corrected, or you got wrong",
        "- **Discoveries** — something you learned about the task, tool, or user preferences",
        "- **Errors** — commands that failed, unexpected behaviors",
        "- **Feature requests** — things the user wanted but could not do",
        "",
        "Edit the learnings files directly — they persist across sessions.",
        "",
        "---",
        f"_from session:end hook — id={session_id[:8]}_",
    ]
    path.write_text("\n".join(lines_out))


def _clear_end_prompt() -> None:
    path = MEMORY_DIR / "NEXT_SESSION_CAPTURE_PROMPT.md"
    if path.exists():
        path.unlink()


def handle(event_type: str, context: dict) -> None:
    session_id = context.get("session_key", "unknown")[:8]
    if event_type == "session:start":
        _clear_end_prompt()
        learnings = _read_learnings()
        _write_session_reminder(learnings, session_id)
    elif event_type == "session:end":
        _write_end_prompt(session_id)