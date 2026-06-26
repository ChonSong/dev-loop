#!/usr/bin/env python3
"""Cron health monitor — checks all cron jobs for errors and escalates.

no_agent mode: silently exits with no output when all jobs are healthy.
When errors are found, outputs a summary. Designed to be run as a cron
job with no_agent=True so it's zero-token when healthy.
"""
import json
import os
import re
import sys
from datetime import datetime, timezone

HERMES_HOME = os.environ.get('HERMES_HOME', os.path.expanduser('~/.hermes'))
JOBS_FILE = os.path.join(HERMES_HOME, 'cron', 'jobs.json')
OUTPUT_DIR = os.path.join(HERMES_HOME, 'cron', 'output')

# Regex patterns that mark a cron output file as a failure
FAILURE_PATTERNS = [
    re.compile(r'\*\*Status:\*\*\s*(script\s+)?failed', re.I),
    re.compile(r'\(FAILED\)'),
    re.compile(r'^## Error'),
    re.compile(r'Script timed out'),
]

def is_failure_file(path):
    """Returns True if the file content indicates a failed cron run."""
    try:
        with open(path) as f:
            head = f.read(2000)
        return any(p.search(head) for p in FAILURE_PATTERNS)
    except (OSError, IOError):
        return False

def count_consecutive_failures(job_id):
    """Count consecutive failure files from newest to oldest."""
    job_output_dir = os.path.join(OUTPUT_DIR, job_id)
    if not os.path.isdir(job_output_dir):
        return 0
    files = sorted(os.listdir(job_output_dir), reverse=True)
    count = 0
    for fname in files:
        fpath = os.path.join(job_output_dir, fname)
        if os.path.isfile(fpath) and is_failure_file(fpath):
            count += 1
        else:
            break  # Stop at first non-failure (success or no data)
    return count

def format_timestamp(ts_str):
    """Format ISO timestamp to a human-readable age."""
    if not ts_str:
        return "never"
    try:
        # Handle timezone-aware strings
        ts = ts_str
        if ts.endswith('Z'):
            ts = ts[:-1] + '+00:00'
        dt = datetime.fromisoformat(ts)
        now = datetime.now(dt.tzinfo)
        delta = now - dt
        if delta.total_seconds() < 60:
            return f"{int(delta.total_seconds())}s ago"
        elif delta.total_seconds() < 3600:
            return f"{int(delta.total_seconds() / 60)}m ago"
        elif delta.total_seconds() < 86400:
            return f"{int(delta.total_seconds() / 3600)}h ago"
        else:
            return f"{int(delta.total_seconds() / 86400)}d ago"
    except (ValueError, TypeError):
        return ts_str or "never"

def main():
    if not os.path.exists(JOBS_FILE):
        print(f"JOBS_FILE_NOT_FOUND:{JOBS_FILE}")
        sys.exit(0)

    with open(JOBS_FILE) as f:
        data = json.load(f)

    total = len(data['jobs'])
    ok_count = 0
    errors = []

    for job in data['jobs']:
        status = job.get('last_status', 'unknown')
        if status == 'ok':
            ok_count += 1
            continue
        if status == 'error':
            job_id = job['id']
            seq_fails = count_consecutive_failures(job_id)
            errors.append({
                'name': job['name'],
                'id': job_id,
                'last_error': job.get('last_error') or job.get('last_delivery_error') or 'Unknown',
                'consecutive': seq_fails,
                'last_run': format_timestamp(job.get('last_run_at')),
                'schedule': job.get('schedule', {}).get('display', '?'),
                'script': job.get('script'),
                'no_agent': job.get('no_agent', False),
            })

    if not errors:
        # Silent = no output means nothing to report
        return

    # Build report — sorted by severity (most consecutive failures first)
    errors.sort(key=lambda x: x['consecutive'], reverse=True)

    lines = [f"Cron Error Report — {len(errors)}/{total} jobs failing"]
    lines.append(f"")
    
    for ej in errors:
        sev = "🔴" if ej['consecutive'] >= 5 else "🟠" if ej['consecutive'] >= 3 else "🟡" if ej['consecutive'] >= 2 else "🔵"
        lines.append(f"{sev} {ej['name']}")
        lines.append(f"   Last run: {ej['last_run']}  |  Schedule: {ej['schedule']}")
        lines.append(f"   Consecutive failures: {ej['consecutive']}")
        if ej['last_error']:
            lines.append(f"   Error: {ej['last_error']}")
        if ej['script']:
            lines.append(f"   Script: {ej['script']}")

    lines.append("")
    lines.append("---")
    lines.append(f"Other jobs: {ok_count}/{total} healthy")
    print('\n'.join(lines))

if __name__ == '__main__':
    main()
