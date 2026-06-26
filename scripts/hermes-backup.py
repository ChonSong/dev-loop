#!/usr/bin/env python3
"""
Hermes Backup — complete state + optional Docker image backup.
- Git sync: every run (config, skills, memories, sessions, state, etc.)
- Docker image: only when --full-image flag passed
- No ignores — backs up EVERYTHING for true disaster recovery
- Runs from system cron or inside container
"""
import argparse
import gzip
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Paths work both inside container (HERMES_HOME=/opt/data) and on host
HERMES_HOME = Path(os.environ.get("HERMES_HOME", "/opt/data"))
# SYNC_REPO: the git working directory — MUST be writable
#   Inside container: /opt/data/cache/sync-work/hermes-sync
#   On host: ~/.cache/sync-work/hermes-sync or similar
SYNC_REPO = HERMES_HOME / "cache" / "sync-work" / "hermes-sync"
BACKUP_DIR = HERMES_HOME / "backups"
DOCKER_IMAGES_TAR = BACKUP_DIR / "docker-images.tar.gz"

SYDNEY_TZ = timezone(timedelta(hours=10))


def run(cmd, cwd=None, timeout=300):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, timeout=timeout)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "timeout"
    except Exception as e:
        return -1, "", str(e)


def get_github_token():
    for p in [
        SYNC_REPO / "netrc",           # inside the synced repo
        Path(os.path.expanduser("~/hermes-sync/netrc")),  # original location
        HERMES_HOME / ".netrc",
        HERMES_HOME / "home" / ".netrc",
        Path(os.path.expanduser("~/.netrc")),            # <-- key fallback
    ]:
        if p.exists():
            for line in p.read_text().splitlines():
                if line.strip().startswith("password"):
                    return line.split()[-1].strip()
    return os.environ.get("GITHUB_TOKEN", "")


def setup_repo(token):
    """Clone or pull hermes-sync repo."""
    repo_url = f"https://ChonSong:{token}@github.com/ChonSong/hermes-sync.git"
    run(["git", "config", "--global", "user.email", "seanos1a@gmail.com"])
    run(["git", "config", "--global", "user.name", "Sean"])
    run(["git", "config", "--global", "--add", "safe.directory", str(SYNC_REPO)])
    run(["git", "config", "--global", "--add", "safe.directory", "/opt/data/hermes-sync"])

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


def sync_all_data():
    """Copy ALL hermes state to the repo — NO ignores, complete backup."""
    changes = 0

    def copy_dir_full(src, dst, label=""):
        nonlocal changes
        if not src.exists():
            return
        if dst.exists():
            shutil.rmtree(dst)
        # Copy everything — no ignore patterns, skip unreadable files
        def skip_unreadable(dirpath, names):
            skipped = set()
            for n in names:
                fp = Path(dirpath) / n
                if fp.is_file() and not os.access(fp, os.R_OK):
                    skipped.add(n)
            if skipped:
                print(f"  ⚠ skipping {len(skipped)} unreadable file(s) in {dirpath}")
            return skipped
        shutil.copytree(src, dst, symlinks=False, ignore_dangling_symlinks=True,
                        ignore=skip_unreadable)
        changes += 1
        print(f"  ✓ {label or src.name}/")

    def copy_file(src, dst, label=""):
        nonlocal changes
        if not src.exists():
            return
        shutil.copy2(src, dst)
        changes += 1
        print(f"  ✓ {label or src.name}")

    # ── Core config ──
    copy_file(HERMES_HOME / "config.yaml", SYNC_REPO / "config.yaml")
    copy_file(HERMES_HOME / "SOUL.md", SYNC_REPO / "SOUL.md")
    copy_file(HERMES_HOME / "auth.json", SYNC_REPO / "auth.json")
    copy_file(HERMES_HOME / "kanban.db", SYNC_REPO / "kanban.db")

    # State DB — all three files
    for ext in ["", "-shm", "-wal"]:
        src = HERMES_HOME / f"state.db{ext}"
        if src.exists():
            shutil.copy2(src, SYNC_REPO / f"state.db{ext}")
            changes += 1
    print("  ✓ state.db*")

    # .env — API keys
    env_src = HERMES_HOME / ".env"
    if env_src.exists():
        secrets_dir = SYNC_REPO / "secrets"
        secrets_dir.mkdir(exist_ok=True)
        shutil.copy2(env_src, secrets_dir / ".env")
        changes += 1
        print("  ✓ .env → secrets/.env")

    # ── All directories — no ignores ──
    copy_dir_full(HERMES_HOME / "skills", SYNC_REPO / "skills")
    copy_dir_full(HERMES_HOME / "memories", SYNC_REPO / "memory")
    copy_dir_full(HERMES_HOME / "workspace", SYNC_REPO / "workspace")
    copy_dir_full(HERMES_HOME / "hooks", SYNC_REPO / "hooks")
    copy_dir_full(HERMES_HOME / "sessions", SYNC_REPO / "sessions")
    copy_dir_full(HERMES_HOME / "plans", SYNC_REPO / "plans")
    copy_dir_full(HERMES_HOME / "cron", SYNC_REPO / "cron")
    copy_dir_full(HERMES_HOME / "scripts", SYNC_REPO / "scripts")

    # Config dir — only if a separate config source exists (not the ro mount)
    config_src = HERMES_HOME / "config"
    if config_src.exists() and config_src != SYNC_REPO / "config":
        copy_dir_full(config_src, SYNC_REPO / "config", "config/")

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


def backup_docker_images():
    """Save Docker images to compressed tar, store alongside git repo."""
    import json
    BACKUP_DIR.mkdir(exist_ok=True)

    images = [
        "hermes-sync:latest",
        "ghcr.io/chonsong/agent-os:latest",
        "postgres:16-alpine",
    ]

    # Also save running container filesystems for complete recovery
    # (config, data dirs, etc.)
    containers = [
        ("hermes", "/opt/data"),
        ("hermes-dashboard", "/opt/data/hermes-dashboard"),
    ]

    print("[Docker] Saving images...")
    all_images = []
    for img in images:
        rc, out, err = run(["docker", "image", "inspect", img])
        if rc == 0:
            all_images.append(img)
        else:
            print(f"  [SKIP] {img} not found")

    if not all_images:
        print("[Docker] No images to save")
        return

    tmp_tar = BACKUP_DIR / "docker-images.tar.gz"

    with tarfile.open(tmp_tar, "w:gz", compresslevel=6) as tar:
        # Use subprocess directly to avoid text-capture issues with docker save binary output
        for img in all_images:
            print(f"  → saving {img}")
            img_name = img.replace('/', '_').replace(':', '_')
            tmp_img = BACKUP_DIR / f"{img_name}.tar"

            try:
                result = subprocess.run(
                    ["docker", "save", img, "-o", str(tmp_img)],
                    timeout=600
                )
                if result.returncode == 0 and tmp_img.exists():
                    tar.add(str(tmp_img), arcname=f"{img_name}.tar")
                    os.unlink(tmp_img)
                    print(f"    ✓ {img}")
                else:
                    print(f"    ✗ failed: {result.stderr[:200] if result.stderr else 'unknown error'}")
                    if tmp_img.exists():
                        os.unlink(tmp_img)
            except Exception as e:
                print(f"    ✗ exception: {e}")

    # Save container mounts info (for recovery reference)
    container_info = {}
    for name, path in containers:
        rc, out, _ = run(["docker", "inspect", name])
        if rc == 0:
            import json
            info = json.loads(out)
            container_info[name] = {
                "image": info[0]["Config"]["Image"],
                "mounts": [
                    {"source": m["Source"], "destination": m["Destination"]}
                    for m in info[0]["Mounts"]
                ],
                "host_config": {
                    "ports": info[0]["HostConfig"]["PortBindings"],
                }
            }

    info_path = BACKUP_DIR / "container-info.json"
    with open(info_path, "w") as f:
        json.dump(container_info, f, indent=2)
    print(f"  ✓ container info saved")

    size_mb = tmp_tar.stat().st_size / (1024 * 1024)
    print(f"[Docker] Images saved: {size_mb:.1f} MB → {tmp_tar}")


def main():
    parser = argparse.ArgumentParser(description="Hermes complete backup")
    parser.add_argument("--full-image", action="store_true",
                        help="Also backup Docker images (slow, ~6GB)")
    args = parser.parse_args()

    ts = datetime.now(SYDNEY_TZ).strftime("%Y-%m-%d %H:%M %Z")
    print(f"=== Hermes Backup — {ts} ===")

    # 1. Git sync (always)
    token = get_github_token()
    if not token:
        print("[ERROR] No GitHub token found")
        sys.exit(1)

    print("\n[1/3] Repo setup...")
    if not setup_repo(token):
        sys.exit(1)

    print("\n[2/3] Syncing ALL data (no ignores)...")
    changes = sync_all_data()
    print(f"      Total: {changes} items")

    print("\n[3/3] Push to GitHub...")
    if not commit_and_push():
        sys.exit(1)

    # 4. Docker image backup (optional, only with --full-image)
    if args.full_image:
        print("\n[Docker] Full image backup...")
        backup_docker_images()
    else:
        print("\n[Docker] Skipped (use --full-image to include)")

    print(f"\n=== Done ===")


if __name__ == "__main__":
    main()