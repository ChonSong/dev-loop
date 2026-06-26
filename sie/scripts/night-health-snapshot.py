#!/usr/bin/env python3
"""Nightly system health snapshot. Cheap, no LLM tokens, fills off-peak gap."""
import os, json, subprocess, time
from pathlib import Path

OUT = os.path.expanduser("~/.hermes/cron/output/health-snapshots")
os.makedirs(OUT, exist_ok=True)
ts = time.strftime("%Y-%m-%d_%H-%M")

snap = {}

# Disk
st = os.statvfs("/")
snap["disk"] = {
    "total_gb": round(st.f_frsize * st.f_blocks / 1e9, 1),
    "free_gb": round(st.f_frsize * st.f_bfree / 1e9, 1),
    "used_pct": round((1 - st.f_bfree / st.f_blocks) * 100, 1),
}

# RAM
try:
    r = subprocess.run(["free", "-m"], capture_output=True, text=True, timeout=5)
    for line in r.stdout.split("\n"):
        if line.startswith("Mem:"):
            parts = line.split()
            snap["ram"] = {
                "total_mb": int(parts[1]),
                "used_mb": int(parts[2]),
                "free_mb": int(parts[3]),
                "used_pct": round(int(parts[2]) / int(parts[1]) * 100, 1),
            }
except: pass

# Load (1min avg)
try:
    r = subprocess.run(["uptime"], capture_output=True, text=True, timeout=5)
    import re
    m = re.search(r"load average: ([\d.]+)", r.stdout)
    if m: snap["load_1min"] = float(m.group(1))
except: pass

# Docker containers
try:
    r = subprocess.run(["docker", "ps", "--format", "{{.Names}} {{.Status}}"],
                       capture_output=True, text=True, timeout=5)
    snap["containers"] = [l for l in r.stdout.strip().split("\n") if l]
except:
    snap["containers"] = []

# Hermes gateway health
try:
    r = subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                        "http://localhost:8642/api/v1/health"],
                       capture_output=True, text=True, timeout=5)
    snap["gateway"] = r.stdout.strip()
except:
    snap["gateway"] = "error"

# Session count today
try:
    import sqlite3
    db = os.path.expanduser("~/.hermes/state.db")
    conn = sqlite3.connect(db)
    today_start = time.time() - (time.time() % 86400) - (11 * 3600)  # approx AEST day start
    cursor = conn.execute("SELECT COUNT(*) FROM sessions WHERE started_at > ?", (today_start,))
    snap["sessions_today"] = cursor.fetchone()[0]
    conn.close()
except:
    snap["sessions_today"] = -1

path = os.path.join(OUT, f"health-{ts}.json")
with open(path, "w") as f:
    json.dump(snap, f, indent=2)

print(f"HEALTH SNAPSHOT {ts}")
print(json.dumps(snap, indent=2))
