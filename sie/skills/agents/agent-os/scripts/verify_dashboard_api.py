#!/usr/bin/env python3
"""Verify all dashboard API endpoints return valid JSON after deployment.

Usage: python3 verify_dashboard_api.py

Run from inside the hermes container or any machine that can reach localhost:1332.
"""
import urllib.request
import json
import sys

BASE = "http://localhost:1332"

# All routes the dashboard frontend calls, with correct HTTP methods
ROUTES = [
    ("GET",  "/api/status"),
    ("GET",  "/api/sessions?limit=20&offset=0"),
    ("GET",  "/api/sessions/demo-session-1/messages"),
    ("DELETE","/api/sessions/demo-session-1"),
    ("GET",  "/api/sessions/search?q=demo"),
    ("GET",  "/api/logs?lines=10"),
    ("GET",  "/api/analytics/usage?days=7"),
    ("GET",  "/api/analytics/models?days=7"),
    ("GET",  "/api/config"),
    ("GET",  "/api/config/defaults"),
    ("GET",  "/api/config/schema"),
    ("GET",  "/api/config/raw"),
    ("PUT",  "/api/config"),
    ("GET",  "/api/model/info"),
    ("GET",  "/api/model/options"),
    ("GET",  "/api/model/auxiliary"),
    ("POST", "/api/model/set"),
    ("GET",  "/api/env"),
    ("PUT",  "/api/env"),
    ("DELETE","/api/env"),
    ("POST", "/api/env/reveal"),
    ("GET",  "/api/cron/jobs"),
    ("POST", "/api/cron/jobs"),
    ("POST", "/api/cron/jobs/cron-1/pause"),
    ("POST", "/api/cron/jobs/cron-1/resume"),
    ("POST", "/api/cron/jobs/cron-1/trigger"),
    ("DELETE","/api/cron/jobs/cron-1"),
    ("GET",  "/api/profiles"),
    ("POST", "/api/profiles"),
    ("PATCH","/api/profiles/default"),
    ("DELETE","/api/profiles/default"),
    ("GET",  "/api/profiles/default/setup-command"),
    ("GET",  "/api/profiles/default/soul"),
    ("PUT",  "/api/profiles/default/soul"),
    ("GET",  "/api/skills"),
    ("PUT",  "/api/skills/toggle"),
    ("GET",  "/api/tools/toolsets"),
    ("GET",  "/api/providers/oauth"),
    ("DELETE","/api/providers/oauth/github"),
    ("POST", "/api/providers/oauth/github/start"),
    ("POST", "/api/providers/oauth/github/submit"),
    ("GET",  "/api/providers/oauth/github/poll/session-123"),
    ("DELETE","/api/providers/oauth/sessions/session-123"),
    ("POST", "/api/gateway/restart"),
    ("POST", "/api/hermes/update"),
    ("GET",  "/api/actions/restart/status"),
    ("GET",  "/api/dashboard/plugins"),
    ("POST", "/api/dashboard/plugins/rescan"),
    ("GET",  "/api/dashboard/themes"),
    ("PUT",  "/api/dashboard/theme"),
    ("GET",  "/api/docker/info"),
    ("GET",  "/api/docker/version"),
    ("GET",  "/api/docker/containers/json?all=true"),
    ("POST", "/api/docker/containers/abc123/start"),
    ("POST", "/api/docker/containers/abc123/stop"),
    ("POST", "/api/docker/containers/abc123/restart"),
    ("POST", "/api/docker/containers/abc123/remove"),
    ("GET",  "/api/system/uptime"),
]

passed = 0
failed = 0

for method, path in ROUTES:
    try:
        req = urllib.request.Request(BASE + path, method=method)
        r = urllib.request.urlopen(req, timeout=5)
        body = r.read()
        json.loads(body)  # Must be valid JSON
        print(f"✓ {method:8} {path}")
        passed += 1
    except urllib.error.HTTPError as e:
        print(f"✗ {method:8} {path} — HTTP {e.code}")
        failed += 1
    except json.JSONDecodeError:
        print(f"✗ {method:8} {path} — HTML returned (route missing or wrong method)")
        failed += 1
    except Exception as e:
        print(f"✗ {method:8} {path} — {e}")
        failed += 1

print(f"\n{passed}/{len(ROUTES)} passed")
sys.exit(0 if failed == 0 else 1)
