#!/usr/bin/env python3
"""Cloudflare Tunnel health probe — checks tunnel process, binary, DNS, origin, and CF Access config in one shot.

Usage:
  python3 cloudflare-tunnel-probe.py [--tunnel NAME] [--url URL] [--local PORT]

Exits 0 if everything is healthy, 1 if any check fails.
Prints actionable diagnosis for each failure.

Examples:
  python3 cloudflare-tunnel-probe.py
  python3 cloudflare-tunnel-probe.py --tunnel hermes-webui --url https://hermes.codeovertcp.com --local-port 8787
"""

import argparse
import json
import os
import subprocess
import sys
import urllib.request
from urllib.error import URLError

def run(cmd):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "timeout"

def check(name, ok, detail=""):
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {name}")
    if detail:
        print(f"         {detail}")
    return ok

def main():
    p = argparse.ArgumentParser(description="Cloudflare Tunnel health probe")
    p.add_argument("--tunnel", default="hermes-webui", help="Tunnel process name pattern")
    p.add_argument("--url", default="https://hermes.codeovertcp.com", help="Public URL")
    p.add_argument("--local-port", default="8787", help="Local origin port")
    p.add_argument("--binary", default="/home/sean/.hermes/bin/cloudflared", help="cloudflared binary path")
    args = p.parse_args()

    all_ok = True
    print(f"Cloudflare Tunnel Probe: {args.tunnel}")
    print(f"  Public: {args.url}  Local: http://127.0.0.1:{args.local_port}")
    print()

    # 1. Process running
    rc, out, _ = run(f"pgrep -f 'cloudflared.*{args.tunnel}'")
    pid = out.split()[0] if out else None
    all_ok &= check("Tunnel process running", pid, f"PID: {pid}" if pid else "No process found")

    # 2. Binary exists
    binary_ok = os.path.isfile(args.binary)
    all_ok &= check(f"Binary exists ({args.binary})", binary_ok)
    if not binary_ok:
        print("         Fix: curl -sL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o BINARY && chmod +x BINARY")

    # 3. DNS resolution
    try:
        import socket
        host = args.url.split("//")[1].split("/")[0]
        ips = socket.getaddrinfo(host, 443)
        ip_list = list(set(r[4][0] for r in ips))
        all_ok &= check("DNS resolves", True, f"IPs: {', '.join(ip_list[:4])}")
    except Exception as e:
        all_ok &= check("DNS resolves", False, str(e))

    # 4. Local origin
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{args.local_port}/", method="HEAD")
        with urllib.request.urlopen(req, timeout=5) as resp:
            all_ok &= check("Local origin responds", resp.status == 200, f"HTTP {resp.status}")
    except Exception as e:
        all_ok &= check("Local origin responds", False, str(e))

    # 5. Public URL (tunnel + origin through Cloudflare)
    try:
        req = urllib.request.Request(args.url, method="HEAD")
        with urllib.request.urlopen(req, timeout=10) as resp:
            all_ok &= check("Public URL responds", resp.status == 200, f"HTTP {resp.status}")
    except URLError as e:
        code = e.code if hasattr(e, 'code') else '?'
        all_ok &= check("Public URL responds", False, f"HTTP {code}: {e.reason}")

    # 6. CF Access endpoint (404 here = Access app misconfigured)
    try:
        from urllib.parse import urlparse
        parsed = urlparse(args.url)
        access_url = f"{parsed.scheme}://{parsed.netloc}/cdn-cgi/access/login"
        req = urllib.request.Request(access_url, method="HEAD")
        with urllib.request.urlopen(req, timeout=10) as resp:
            all_ok &= check("CF Access endpoint", resp.status in (200, 302, 403), f"HTTP {resp.status}")
    except URLError as e:
        code = e.code if hasattr(e, 'code') else '?'
        if code == 404:
            all_ok &= check("CF Access endpoint", False,
                "HTTP 404 - Access app misconfigured. "
                "Go to Zero Trust > Access > Applications > Add self-hosted application.")
        else:
            all_ok &= check("CF Access endpoint", False, f"HTTP {code}: {e.reason}")

    print()
    if all_ok:
        print("All checks passed")
    else:
        print("Some checks failed - see above for diagnosis")
    sys.exit(0 if all_ok else 1)

if __name__ == "__main__":
    main()
