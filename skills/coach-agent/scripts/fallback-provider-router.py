#!/usr/bin/env python3
"""
Provider Fallback Matrix Router for Coach.

Reads provider-fallback-matrix.yaml, tests each tier in order, and:
  --probe         Test all tiers and update matrix status (watchdog mode)
  --route         Return the first available model for Coach to use
  --health        Print health report for all tiers

Used as:
  1. Pre-run route: python3 fallback-provider-router.py --route
     Returns model name if available, or prints "NONE: all tiers down"
  2. Watchdog cron: python3 fallback-provider-router.py --probe
     Tests all tiers, updates matrix status, can switch Coach cron model
  3. Manual: python3 fallback-provider-router.py --health
     Prints table of all tiers with status
"""
import subprocess, json, os, sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

SKILL_DIR = Path(__file__).resolve().parent.parent
MATRIX_FILE = SKILL_DIR / "references" / "provider-fallback-matrix.yaml"
ENV_FILE = Path.home() / ".hermes" / ".env"
CRON_OUTPUT_DIR = Path.home() / ".hermes" / "cron" / "output"
COACH_JOB_ID = "5e1bba516d87"


def load_env() -> dict[str, str]:
    """Load API keys from Hermes .env."""
    keys = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            if "=" in line and "API_KEY" in line and not line.startswith("#"):
                k, v = line.strip().split("=", 1)
                keys[k] = v.strip()
    return keys


def load_matrix() -> list[dict]:
    """Parse the fallback matrix YAML."""
    import yaml
    with open(MATRIX_FILE) as f:
        data = yaml.safe_load(f)
    return data.get("tiers", [])


def test_tier(tier: dict, keys: dict[str, str]) -> tuple[str, str]:
    """
    Test a provider/model combination.
    Returns (status, detail).
    status: "active" | "throttled" | "insufficient" | "unauthorized" | "unreachable"
    """
    auth_key = keys.get(tier["auth_env"])
    if not auth_key:
        return "unauthorized", f"Key {tier['auth_env']} not in .env"

    base = tier["base_url"]
    endpoint = f"{base}/chat/completions"
    header = "Authorization: Bearer " + auth_key

    try:
        proc = subprocess.run(
            ["curl", "-s", "-w", "\n%{http_code}",
             "-H", header,
             "-H", "Content-Type: application/json",
             "-d", json.dumps({
                 "model": tier["model"],
                 "messages": [{"role": "user", "content": "ping"}],
                 "max_tokens": 1
             }),
             endpoint],
            capture_output=True, text=True, timeout=20
        )
        output = proc.stdout.strip()
        if not output:
            return "unreachable", "No response from endpoint"

        lines = output.rsplit("\n", 1)
        http_code = lines[-1] if len(lines) > 1 else ""
        body = lines[0] if len(lines) > 1 else output

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            return "unreachable", f"HTTP {http_code}, non-JSON: {body[:100]}"

        if "choices" in data:
            return "active", "OK"

        error = data.get("error", {})
        msg = error.get("message", str(error))

        if "rate limit" in msg.lower() or "FreeUsageLimitError" in msg:
            return "throttled", msg[:120]
        if "insufficient" in msg.lower() or "balance" in msg.lower() or "billing" in msg.lower():
            return "insufficient", msg[:120]
        if "unauthorized" in msg.lower() or "not found" in msg.lower() or "invalid" in msg.lower():
            return "unauthorized", msg[:120]

        return "unreachable", f"HTTP {http_code}: {msg[:120]}"

    except subprocess.TimeoutExpired:
        return "unreachable", "Timeout (20s)"
    except Exception as e:
        return "unreachable", str(e)[:120]


def save_matrix(tiers: list[dict]):
    """Write updated matrix back to YAML."""
    import yaml
    content = """# Provider Fallback Matrix
# Ordered: first available model wins. Coach iterates through tiers on failure.
# Status: "active" = available, "throttled" = rate-limited, "insufficient" = no credits, "unauthorized" = bad key

tiers:
"""
    with open(MATRIX_FILE, "w") as f:
        f.write(content)
        yaml.safe_dump(tiers, f, default_flow_style=False, sort_keys=False)
    print("Matrix updated.")


def probe_all(keys: dict[str, str]) -> list[dict]:
    """Test all tiers and update their status."""
    tiers = load_matrix()
    now = datetime.now(timezone.utc).isoformat()

    for tier in tiers:
        status, detail = test_tier(tier, keys)
        tier["status"] = status
        tier["last_tested"] = now
        if detail and status != "active":
            tier["throttle_reason"] = detail
        print(f"  {tier['id']}: {status} ({detail if status != 'active' else 'OK'})")

    save_matrix(tiers)
    return tiers


def route(keys: dict[str, str]) -> Optional[dict]:
    """Return the first active tier, testing each as needed."""
    tiers = load_matrix()
    # First, check already-active tiers
    for tier in tiers:
        if tier["status"] == "active":
            return tier

    # Probe each tier in order until we find one that works
    now = datetime.now(timezone.utc).isoformat()
    for tier in tiers:
        status, detail = test_tier(tier, keys)
        tier["status"] = status
        tier["last_tested"] = now
        if status == "active":
            save_matrix(tiers)
            return tier

    save_matrix(tiers)
    return None


def health_report(keys: dict[str, str]):
    """Print a health table for all tiers."""
    tiers = load_matrix()
    active = sum(1 for t in tiers if t["status"] == "active")
    throttled = sum(1 for t in tiers if t["status"] == "throttled")
    down = sum(1 for t in tiers if t["status"] in ("insufficient", "unauthorized", "unreachable"))

    print(f"\nProvider Fallback Matrix — {len(tiers)} tiers")
    print(f"  Active: {active} | Throttled: {throttled} | Down: {down}")
    print()

    for tier in tiers:
        icon = {"active": "✓", "throttled": "⚠", "insufficient": "✗", "unauthorized": "✗", "unreachable": "✗"}
        print(f"  {icon.get(tier['status'], '?')} Tier: {tier['id']}")
        print(f"     Model: {tier['provider']}/{tier['model']} ({tier['cost']})")
        print(f"     Status: {tier['status']}")
        if tier.get("throttle_reason"):
            print(f"     Reason: {tier['throttle_reason'][:120]}")
        print()


def find_working_model(keys: dict[str, str]) -> str:
    """Return first available model name, or 'NONE: reason'."""
    result = route(keys)
    if result:
        return result["model"]
    tiers = load_matrix()
    reasons = [f"{t['id']}: {t['status']}" for t in tiers]
    return f"NONE: all {len(tiers)} tiers down ({'; '.join(reasons)})"


def main():
    keys = load_env()
    arg = sys.argv[1] if len(sys.argv) > 1 else "--health"

    if arg == "--probe":
        print("Probing all tiers...")
        probe_all(keys)

    elif arg == "--route":
        model = find_working_model(keys)
        print(model)

    elif arg == "--health":
        health_report(keys)

    else:
        print(f"Usage: {sys.argv[0]} [--probe|--route|--health]")
        sys.exit(1)


if __name__ == "__main__":
    main()
