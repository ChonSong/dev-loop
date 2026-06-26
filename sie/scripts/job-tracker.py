#!/usr/bin/env python3
"""
Job tracker — CLI for managing the apply queue and application history.
Integrates with the daily pipeline output.

Usage:
  python3 ~/.hermes/scripts/job-tracker.py status         — show today's queue + stats
  python3 ~/.hermes/scripts/job-tracker.py queue [N]       — list queue (default all, or first N)
  python3 ~/.hermes/scripts/job-tracker.py apply <N> [note] — mark job #N as applied
  python3 ~/.hermes/scripts/job-tracker.py skip <N> [reason] — skip job #N
  python3 ~/.hermes/scripts/job-tracker.py history [N]     — show application history (default today, or N days)
  python3 ~/.hermes/scripts/job-tracker.py log <title>@<company> <url> — manually log an application
"""
import os, sys, json, time
from datetime import date, datetime, timedelta
from pathlib import Path

JOBS_DIR = Path(os.path.expanduser('~/.hermes/jobs'))
QUEUE_DIR = JOBS_DIR / 'queue'
APPS_FILE = JOBS_DIR / 'applications.json'

def load_apps():
    if APPS_FILE.exists():
        with open(APPS_FILE) as f:
            return json.load(f)
    return []

def save_apps(apps):
    with open(APPS_FILE, 'w') as f:
        json.dump(apps, f, indent=2)

def get_latest_queue():
    """Get the most recent queue file."""
    if not QUEUE_DIR.exists():
        return None
    queue_files = sorted(QUEUE_DIR.glob('*-queue.json'))
    if not queue_files:
        return None
    with open(queue_files[-1]) as f:
        return json.load(f)

def cmd_status():
    apps = load_apps()
    queue = get_latest_queue()

    today = date.today().isoformat()
    applied_today = [a for a in apps if a.get('date') == today]
    applied_all = [a for a in apps if a.get('status') == 'applied']
    interviews = [a for a in apps if a.get('status') == 'interviewing']

    print(f"📊 JOB TRACKER — {datetime.now().strftime('%a %d %b %Y')}")
    print(f"{'='*50}")
    print(f"Applied total:     {len(applied_all)}")
    print(f"Applied today:     {len(applied_today)}")
    print(f"Interviewing:      {len(interviews)}")
    print(f"History entries:   {len(apps)}")

    if queue:
        entry = queue.get('count', len(queue.get('jobs', [])))
        print(f"\nLatest queue:      {entry} jobs ({queue.get('date', '?')})")
        print(f"  To list:     python3 ~/.hermes/scripts/job-tracker.py queue")
        print(f"  To apply:    python3 ~/.hermes/scripts/job-tracker.py apply <N>")
    else:
        print(f"\nNo queue found. Pipeline runs at 08:00 daily.")

    if applied_today:
        print(f"\n✅ Applied today:")
        for a in applied_today:
            print(f"   • {a.get('title')} @ {a.get('company')}")

def cmd_queue(limit=None):
    queue = get_latest_queue()
    if not queue:
        print("No queue found.")
        sys.exit(1)
    jobs = queue.get('jobs', [])
    if not jobs:
        print("Queue is empty.")
        return

    if limit:
        limit = int(limit)
        jobs = jobs[:limit]

    # Check which are already applied
    apps = load_apps()
    applied_ids = {a.get('job_key') for a in apps if a.get('status') in ('applied', 'interviewing')}

    print(f"📋 APPLY QUEUE — {queue.get('date', '?')}")
    print(f"{'='*60}")
    for i, job in enumerate(jobs, 1):
        title = job.get('title', '?')
        company = job.get('company', job.get('company_name', '?'))
        location = job.get('location', '')
        url = job.get('url', job.get('externalUrl', ''))
        seniority = job.get('seniority', '')
        salary = job.get('salary', '')
        source = job.get('_source', '?')

        # Determine if already applied
        status_char = ' '
        url_key = job.get('url', job.get('externalUrl', ''))
        if url_key in applied_ids:
            status_char = '✓'

        print(f"\n  [{i}]{status_char} {title}")
        print(f"     {company} | {location}")
        if seniority:
            print(f"     Level: {seniority}")
        if salary:
            print(f"     Salary: {salary}")
        print(f"     [{source}]")
        if url:
            print(f"     {url}")
        if status_char == '✓':
            print(f"     ✅ Already applied")

    print(f"\nTotal: {len(jobs)}")
    print(f"Usage: python3 track.py apply <N>")
    print(f"       python3 track.py skip <N>")

def cmd_apply(n, note=""):
    queue = get_latest_queue()
    if not queue:
        print("No queue found.")
        sys.exit(1)
    jobs = queue.get('jobs', [])
    idx = int(n) - 1
    if idx < 0 or idx >= len(jobs):
        print(f"Invalid job #{n}. Queue has {len(jobs)} jobs.")
        sys.exit(1)
    job = jobs[idx]

    app = {
        'date': date.today().isoformat(),
        'ts': int(time.time()),
        'status': 'applied',
        'title': job.get('title', '?'),
        'company': job.get('company', job.get('company_name', '?')),
        'location': job.get('location', ''),
        'url': job.get('url', job.get('externalUrl', '')),
        'source': job.get('_source', '?'),
        'job_key': job.get('url', job.get('externalUrl', '')),
        'note': note or '',
    }

    apps = load_apps()
    apps.append(app)
    save_apps(apps)
    print(f"✅ Marked as APPLIED:")
    print(f"   {app['title']} @ {app['company']}")
    if note:
        print(f"   Note: {note}")

def cmd_skip(n, reason=""):
    queue = get_latest_queue()
    if not queue:
        print("No queue found.")
        sys.exit(1)
    jobs = queue.get('jobs', [])
    idx = int(n) - 1
    if idx < 0 or idx >= len(jobs):
        print(f"Invalid job #{n}.")
        sys.exit(1)
    job = jobs[idx]

    app = {
        'date': date.today().isoformat(),
        'ts': int(time.time()),
        'status': 'skipped',
        'title': job.get('title', '?'),
        'company': job.get('company', job.get('company_name', '?')),
        'url': job.get('url', job.get('externalUrl', '')),
        'source': job.get('_source', '?'),
        'job_key': job.get('url', job.get('externalUrl', '')),
        'note': reason or 'skipped',
    }

    apps = load_apps()
    apps.append(app)
    save_apps(apps)
    print(f"⏭ Skipped #{n}: {app['title']} @ {app['company']}")
    if reason:
        print(f"   Reason: {reason}")

def cmd_history(days=None):
    apps = load_apps()
    if not apps:
        print("No application history.")
        return

    if days:
        cutoff = date.today() - timedelta(days=int(days))
        apps = [a for a in apps if datetime.fromisoformat(a.get('date', '2000-01-01')).date() >= cutoff]

    # Reverse chrono
    apps.sort(key=lambda a: a.get('ts', 0), reverse=True)

    print(f"📜 APPLICATION HISTORY")
    print(f"{'='*60}")
    statuses = {}
    for a in apps:
        s = a.get('status', '?')
        statuses[s] = statuses.get(s, 0) + 1
        print(f"\n  {a.get('date','')} [{s}] {a.get('title','')} @ {a.get('company','')}")
        url = a.get('url', '')
        if url:
            print(f"     {url}")
        note = a.get('note', '')
        if note:
            print(f"     📝 {note}")

    print(f"\n{'='*60}")
    print(f"Total: {len(apps)}")
    for s, c in sorted(statuses.items()):
        print(f"  {s}: {c}")

def cmd_log(entry, url=""):
    """Manually log an application outside the queue."""
    parts = entry.split('@', 1)
    title = parts[0].strip()
    company = parts[1].strip() if len(parts) > 1 else '?'

    app = {
        'date': date.today().isoformat(),
        'ts': int(time.time()),
        'status': 'applied',
        'title': title,
        'company': company,
        'url': url,
        'source': 'manual',
        'job_key': url,
        'note': '',
    }

    apps = load_apps()
    apps.append(app)
    save_apps(apps)
    print(f"✅ Logged: {title} @ {company}")

def main():
    args = sys.argv[1:] if len(sys.argv) > 1 else ['status']
    cmd = args[0]

    if cmd == 'status' or cmd == 'stats':
        cmd_status()
    elif cmd == 'queue' or cmd == 'list':
        cmd_queue(args[1] if len(args) > 1 else None)
    elif cmd == 'apply':
        if len(args) < 2:
            print("Usage: track.py apply <N> [note]")
            sys.exit(1)
        note = ' '.join(args[2:]) if len(args) > 2 else ''
        cmd_apply(args[1], note)
    elif cmd == 'skip':
        if len(args) < 2:
            print("Usage: track.py skip <N> [reason]")
            sys.exit(1)
        reason = ' '.join(args[2:]) if len(args) > 2 else ''
        cmd_skip(args[1], reason)
    elif cmd == 'history' or cmd == 'log':
        cmd_history(args[1] if len(args) > 1 else None)
    elif cmd == 'log-manual':
        if len(args) < 2:
            print("Usage: track.py log <Title>@<Company> [url]")
            sys.exit(1)
        url = args[2] if len(args) > 2 else ''
        cmd_log(args[1], url)
    else:
        print(f"Unknown command: {cmd}")
        print("Commands: status, queue [N], apply <N> [note], skip <N> [reason], history [days]")
        sys.exit(1)

if __name__ == '__main__':
    main()
