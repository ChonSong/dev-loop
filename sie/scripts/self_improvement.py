#!/usr/bin/env python3
"""
Self-Improvement Engine — Entry Point
Runs the full self-improvement pipeline: scan → research → author → commit.
Also callable as: python3 self_improvement.py [--scan-only] [--dry-run] [--candidate ID]
"""
import json
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────
HERMES_SYNC = Path(__file__).parent.parent.resolve()
CANDIDATES_JSON = HERMES_SYNC / "workspace" / "plans" / "skill_candidates.json"

SCANNER = HERMES_SYNC / "scripts" / "learnings_scanner.py"
AUTHOR = HERMES_SYNC / "scripts" / "skill_author.py"

# ── Run helpers ──────────────────────────────────────────────────────────────

def run_script(script_path, args=None):
    """Run a Python script, return stdout."""
    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)
    r = subprocess.run(cmd, cwd=str(HERMES_SYNC), capture_output=True, text=True)
    return r.stdout + (r.stderr if r.returncode != 0 else ""), r.returncode


def git_push(cwd=HERMES_SYNC):
    """Push hermes-sync to origin."""
    r = subprocess.run(["git", "push"], cwd=cwd, capture_output=True, text=True)
    return r.returncode == 0, r.stderr.strip()


def load_candidates():
    if not CANDIDATES_JSON.exists():
        return None
    with open(CANDIDATES_JSON) as f:
        return json.load(f)


def main():
    dry_run = "--dry-run" in sys.argv
    scan_only = "--scan-only" in sys.argv
    target = None
    for arg in sys.argv[1:]:
        if not arg.startswith("--"):
            target = arg

    sydney = timezone(timedelta(hours=10))
    ts = datetime.now(sydney).strftime("%Y-%m-%d %H:%M %Z")

    print(f"╔══════════════════════════════════════════╗")
    print(f"║   Self-Improvement Engine               ║")
    print(f"║   {ts}              ║")
    print(f"╚══════════════════════════════════════════╝")
    print(f"Dry-run: {dry_run} | Scan-only: {scan_only} | Target: {target or 'all'}\n")

    # ── Phase 1: Scan ────────────────────────────────────────────────────────
    print("─── Phase 1: Scanning learnings ───")
    out, rc = run_script(SCANNER)
    print(out)
    if rc != 0:
        print(f"[!] Scanner failed with exit {rc}")
        sys.exit(1)

    candidates = load_candidates()
    if not candidates:
        print("[!] No candidates loaded")
        sys.exit(1)

    hp_count = len(candidates.get("high_priority", []))
    total = len(candidates.get("candidates", []))
    print(f"[+] Scanned {candidates['total_scanned']} entries -> {total} candidates, {hp_count} high-priority\n")

    if scan_only:
        print("[scan-only mode, exiting after Phase 1]")
        return

    if hp_count == 0:
        print("[=] No high-priority candidates. Nothing to author.")
        return

    # ── Phase 2: Author ──────────────────────────────────────────────────────
    print("─── Phase 2: Authoring skills ───")
    args = ["--dry-run"] if dry_run else []
    if target:
        args.append(target)
    out, rc = run_script(AUTHOR, args)
    print(out)
    if rc != 0:
        print(f"[!] Author failed with exit {rc}")

    # ── Phase 3: Report ───────────────────────────────────────────────────────
    print("\n─── Phase 3: Report ───")
    candidates = load_candidates()
    authored = [c for c in candidates.get("candidates", []) if c.get("skill_authored")]
    hp = candidates.get("high_priority", [])

    print(f"Scanned at: {candidates['scanned_at']}")
    print(f"Total scanned: {candidates['total_scanned']}")
    print(f"High-priority found: {len(hp)}")
    print(f"Skills authored this run: {len(authored)}")
    if authored:
        for c in authored:
            print(f"  + {c['id']} -> skill authored")
    if hp:
        remaining = [c for c in hp if not c.get("skill_authored")]
        if remaining:
            print(f"Remaining high-priority: {len(remaining)}")
            for c in remaining:
                print(f"  -> [{c['id']}] {c['title']} (score={c.get('skill_score',0):.1f})")

    # ── Phase 4: Push ───────────────────────────────────────────────────────
    if not dry_run:
        print("\n─── Phase 4: Push to origin ───")
        ok, err = git_push()
        if ok:
            print("[+] Pushed to origin")
        else:
            print(f"[!] Push failed: {err}")
    else:
        print("\n[dry-run] Skipping push")

    print("\n=== Self-Improvement Engine complete ===")


if __name__ == "__main__":
    main()
