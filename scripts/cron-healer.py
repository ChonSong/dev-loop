#!/usr/bin/env python3
"""
cron-healer.py — Programmatic cron job model fallback.
No LLM calls. Reads jobs.json directly, switches models on erroring jobs,
sends Discord notification via bot API.

Only escalates jobs that have errored 2+ CONSECUTIVE times
to avoid premature fallback on a job that hasn't run yet.

Model fallback chain (in order of preference):
  1. deepseek-v4-flash-free  / opencode-zen  — free
  2. openrouter/owl-alpha    / openrouter    — paid, reliable
  3. deepseek-v4-flash       / opencode-zen  — paid, cheap
"""

import json
import os
import urllib.error
import urllib.request
from datetime import datetime

HERMES_HOME = os.path.expanduser("~/.hermes")
JOBS_FILE = os.path.join(HERMES_HOME, "cron", "jobs.json")
ENV_FILE = os.path.join(HERMES_HOME, ".env")
LOG = os.path.join(HERMES_HOME, "logs", "cron-healer.log")
HEAL_HISTORY = os.path.join(HERMES_HOME, "cron", "heal-history.json")

# Fallback chain: current_model → try next (first match wins)
FALLBACK_CHAIN = {
    "deepseek-v4-flash-free": [
        ("openrouter", "openrouter/owl-alpha"),
        ("opencode-zen", "deepseek-v4-flash"),
    ],
    "openrouter/owl-alpha": [
        ("opencode-zen", "deepseek-v4-flash"),
        ("opencode-zen", "deepseek-v4-flash-free"),
    ],
    "deepseek-v4-flash": [
        ("opencode-zen", "deepseek-v4-flash-free"),
    ],
}

def load_env():
    """Load env vars from .env file."""
    env = {}
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    env[key.strip()] = val.strip().strip('"').strip("'")
    return env

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")

def load_history():
    if not os.path.exists(HEAL_HISTORY):
        return {}
    try:
        with open(HEAL_HISTORY) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}

def save_history(history):
    os.makedirs(os.path.dirname(HEAL_HISTORY), exist_ok=True)
    with open(HEAL_HISTORY, "w") as f:
        json.dump(history, f, indent=2)

def notify_discord(message, env):
    """Send a Discord notification using the bot API."""
    token = env.get("DISCORD_BOT_TOKEN") or os.environ.get("DISCORD_BOT_TOKEN", "")
    channel = env.get("DISCORD_CHANNEL_ID") or os.environ.get("DISCORD_CHANNEL_ID", "")
    home_channel = env.get("DISCORD_HOME_CHANNEL") or os.environ.get("DISCORD_HOME_CHANNEL", "")

    channel_id = home_channel or channel
    if not token or not channel_id:
        log("No Discord credentials found, skipping notification")
        return

    # Use Discord Bot API to send message
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    payload = json.dumps({"content": f"🔧 **Cron Healer**: {message}"}).encode()
    req = urllib.request.Request(
        url, data=payload,
        headers={
            "Authorization": f"Bot {token}",
            "Content-Type": "application/json",
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            log(f"Discord notification sent: {resp.status}")
    except urllib.error.HTTPError as e:
        if e.code == 403:
            log("Discord notification skipped (stale bot token)")
        else:
            log(f"Discord notification failed (HTTP {e.code}): {e}")
    except Exception as e:
        log(f"Discord notification failed: {e}")

def main():
    log("=" * 60)
    log("Starting cron health check")

    env = load_env()

    if not os.path.exists(JOBS_FILE):
        log(f"Jobs file not found: {JOBS_FILE}")
        return

    with open(JOBS_FILE) as f:
        data = json.load(f)

    jobs = data.get("jobs", [])
    if not isinstance(jobs, list):
        log(f"Unexpected jobs format: {type(jobs)}")
        return

    history = load_history()
    now = datetime.now().isoformat()
    healed = []
    dirty = False

    for job in jobs:
        job_id = job.get("id", "")
        name = job.get("name", "unnamed")
        model = job.get("model")
        provider = job.get("provider")
        last_status = job.get("last_status")
        no_agent = job.get("no_agent", False)

        # Skip script-only jobs
        if no_agent:
            continue

        # Skip null-model jobs
        if not model or not provider:
            continue

        # Track consecutive failures
        job_history = history.get(job_id, {"consecutive_errors": 0, "last_status": None})

        if last_status == "error":
            job_history["consecutive_errors"] += 1
        elif last_status == "ok":
            job_history["consecutive_errors"] = 0

        job_history["last_status"] = last_status
        job_history["last_seen"] = now
        history[job_id] = job_history

        # Warn at first error, escalate at 2+
        if job_history["consecutive_errors"] == 1:
            log(f"  ⚠️  {name}: first consecutive error ({provider}/{model}) — warning issued")
            notify_discord(
                f"⚠️ **{name}** first consecutive error on `{provider}/{model}`. "
                f"Next error will trigger auto-heal.",
                env
            )

        # Only escalate if 2+ consecutive errors
        if job_history["consecutive_errors"] < 2:
            continue

        # Check if we have a fallback for this model
        if model not in FALLBACK_CHAIN:
            log(f"  {name}: {job_history['consecutive_errors']}x errors on '{model}' — no fallback defined")
            continue

        # Reset counter and apply fallback
        job_history["consecutive_errors"] = 0
        next_provider, next_model = FALLBACK_CHAIN[model][0]

        log(f"  Healing {name} ({job_id}): {provider}/{model} → {next_provider}/{next_model} "
            f"(had {job_history['consecutive_errors'] + 1}x consecutive errors)")
        job["provider"] = next_provider
        job["model"] = next_model
        dirty = True
        healed.append({
            "name": name,
            "job_id": job_id,
            "from": f"{provider}/{model}",
            "to": f"{next_provider}/{next_model}",
        })

    save_history(history)

    if not healed:
        if any(j.get("last_status") == "error" for j in jobs):
            log("Erroring jobs found, but none met 2+ consecutive failure threshold yet")
        else:
            log("No jobs needed healing")
        return

    # Write back jobs file
    with open(JOBS_FILE, "w") as f:
        json.dump(data, f, indent=2)

    log(f"Healed {len(healed)} job(s):")
    for h in healed:
        log(f"  {h['name']}: {h['from']} → {h['to']}")

    summary = "\n".join(f"{h['name']}: {h['from']} → {h['to']}" for h in healed)
    notify_discord(
        f"🩹 **{len(healed)} job(s) auto-healed** (2+ consecutive failures)\n```\n{summary}\n```",
        env
    )

    log("Done")

if __name__ == "__main__":
    main()
