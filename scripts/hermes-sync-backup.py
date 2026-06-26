#!/usr/bin/env python3
"""
Hermes Sync Backup — complete state backup to GitHub.
Runs via system cron (host) OR hermes cron (container).
Pushes everything needed to recreate Hermes on a bare machine.
"""
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Paths work both inside container (HERMES_HOME=/opt/data) and on host
HERMES_HOME = Path(os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes")))
SYNC_REPO = Path(os.environ.get("SYNC_REPO", str(HERMES_HOME / "cache" / "sync-work" / "hermes-sync")))

SYDNEY_TZ = timezone(timedelta(hours=10))


def run(cmd, cwd=None, timeout=180):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, timeout=timeout)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "timeout"
    except Exception as e:
        return -1, "", str(e)


def get_github_token():
    # 1. Environment
    t = os.environ.get("GITHUB_TOKEN", "")
    if t:
        return t
    # 2. netrc in hermes-sync mount
    for p in [HERMES_HOME / "hermes-sync" / "netrc", Path(os.path.expanduser("~/hermes-sync/netrc"))]:
        if p.exists():
            for line in p.read_text().splitlines():
                if line.strip().startswith("password"):
                    return line.split()[-1].strip()
    # 3. .env
    env_path = HERMES_HOME / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("GITHUB_TOKEN="):
                return line.split("=", 1)[1].strip()
    return ""


def setup_repo(token):
    """Clone or pull hermes-sync repo."""
    SYNC_REPO.parent.mkdir(parents=True, exist_ok=True)
    repo_url = f"https://ChonSong:{token}@github.com/ChonSong/hermes-sync.git"

    run(["git", "config", "--global", "user.email", "seanos1a@gmail.com"])
    run(["git", "config", "--global", "user.name", "Sean"])
    run(["git", "config", "--global", "--add", "safe.directory", str(SYNC_REPO)])

    if (SYNC_REPO / ".git").exists():
        rc, _, err = run(["git", "fetch", "origin"], cwd=SYNC_REPO)
        if rc != 0:
            print(f"[WARN] fetch failed: {err}, re-cloning")
            shutil.rmtree(SYNC_REPO, ignore_errors=True)
        else:
            rc2, head, _ = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=SYNC_REPO)
            branch = head.strip() or "master"
            run(["git", "reset", "--hard", f"origin/{branch}"], cwd=SYNC_REPO)
            run(["git", "clean", "-fd"], cwd=SYNC_REPO)
            return True

    if not (SYNC_REPO / ".git").exists():
        rc, _, err = run(["git", "clone", repo_url, str(SYNC_REPO)])
        if rc != 0:
            print(f"[ERROR] clone failed: {err}")
            return False
        run(["git", "config", "--global", "--add", "safe.directory", str(SYNC_REPO)])
    return True


def sync_data():
    """Copy complete hermes state to the repo."""
    changes = 0

    def rsync_dir(src, dst, label=""):
        nonlocal changes
        if not src.exists():
            return
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst, symlinks=False, ignore_dangling_symlinks=True,
                        ignore=shutil.ignore_patterns(
                            "__pycache__", "*.pyc", "*.log", ".git",
                            "node_modules", ".venv", "venv", "*.tmp",
                            "sync-work"  # don't back up our own working dir
                        ))
        changes += 1
        print(f"  ✓ {label or src.name}/")

    def copy_file(src, dst, label=""):
        nonlocal changes
        if not src.exists():
            return
        shutil.copy2(src, dst)
        changes += 1
        print(f"  ✓ {label or src.name}")

    # ── Critical state ──
    copy_file(HERMES_HOME / "config.yaml", SYNC_REPO / "config.yaml")
    copy_file(HERMES_HOME / "SOUL.md", SYNC_REPO / "SOUL.md")
    copy_file(HERMES_HOME / "auth.json", SYNC_REPO / "auth.json")
    copy_file(HERMES_HOME / "kanban.db", SYNC_REPO / "kanban.db")

    # State DB -- compress with gzip (270MB -> ~94MB, under GitHub 100MB limit)
    db_path = HERMES_HOME / "state.db"
    if db_path.exists():
        import gzip
        with open(db_path, "rb") as f_in:
            with gzip.open(SYNC_REPO / "state.db.gz", "wb", compresslevel=6) as f_out:
                shutil.copyfileobj(f_in, f_out)
        changes += 1
        print("  ✓ state.db → state.db.gz (compressed)")
    else:
        print("  ⊘ state.db not found")

    # .env — the API keys. Critical for migration. Put in secrets/ (gitignored from public repos)
    env_src = HERMES_HOME / ".env"
    if env_src.exists():
        secrets_dir = SYNC_REPO / "secrets"
        secrets_dir.mkdir(exist_ok=True)
        shutil.copy2(env_src, secrets_dir / ".env")
        changes += 1
        print("  ✓ .env → secrets/.env")

    # ── Directories ──
    rsync_dir(HERMES_HOME / "skills", SYNC_REPO / "skills")
    rsync_dir(HERMES_HOME / "memories", SYNC_REPO / "memory")
    rsync_dir(HERMES_HOME / "workspace", SYNC_REPO / "workspace")
    rsync_dir(HERMES_HOME / "hooks", SYNC_REPO / "hooks")
    rsync_dir(HERMES_HOME / "sessions", SYNC_REPO / "sessions")
    rsync_dir(HERMES_HOME / "plans", SYNC_REPO / "plans")
    rsync_dir(HERMES_HOME / "cron", SYNC_REPO / "cron")
    rsync_dir(HERMES_HOME / "scripts", SYNC_REPO / "scripts")

    return changes


def commit_and_push():
    """Stage, commit, push."""
    run(["git", "add", "-A"], cwd=SYNC_REPO)

    rc, status, _ = run(["git", "status", "--porcelain"], cwd=SYNC_REPO)
    if not status.strip():
        print("[OK] No changes — already in sync")
        return True

    n = len([l for l in status.splitlines() if l.strip()])
    ts = datetime.now(SYDNEY_TZ).strftime("%Y-%m-%dT%H:%M:%S%z")
    msg = f"auto-sync {ts} ({n} files)"

    rc, _, err = run(["git", "commit", "-m", msg], cwd=SYNC_REPO)
    if rc != 0:
        print(f"[WARN] commit: {err}")
        return False

    rc, branch, _ = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=SYNC_REPO)
    branch = branch.strip() or "master"

    rc, _, err = run(["git", "push", "origin", branch], cwd=SYNC_REPO)
    if rc != 0:
        print(f"[ERROR] push failed: {err}")
        return False

    print(f"[OK] Pushed: {msg}")
    return True


def main():
    ts = datetime.now(SYDNEY_TZ).strftime("%Y-%m-%d %H:%M %Z")
    print(f"=== Hermes Sync Backup — {ts} ===")

    token = get_github_token()
    if not token:
        print("[ERROR] No GitHub token found (GITHUB_TOKEN, netrc, .env)")
        sys.exit(1)

    print("[1/3] Repo setup...")
    if not setup_repo(token):
        sys.exit(1)

    print("[2/3] Syncing data...")
    changes = sync_data()
    print(f"      Total: {changes} items")

    print("[3/3] Push...")
    if not commit_and_push():
        sys.exit(1)

    print(f"=== Done ===")


if __name__ == "__main__":
    main()
