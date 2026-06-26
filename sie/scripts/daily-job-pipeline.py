#!/usr/bin/env python3
"""
Daily job pipeline — merges Seek + Indeed results, deduplicates, filters for
entry-level, and produces an apply queue.
Designed for cron (no_agent) — output IS the queue you read.
"""
import os, sys, json, re, time
from datetime import datetime, date
from pathlib import Path

JOBS_DIR = Path(os.path.expanduser('~/.hermes/jobs'))
REGISTRY_FILE = JOBS_DIR / 'registry.json'
QUEUE_DIR = JOBS_DIR / 'queue'
APPS_FILE = JOBS_DIR / 'applications.json'

# Titles that indicate entry-level suitability
ENTRY_KEYWORDS = [
    'graduate', 'junior', 'associate', 'entry level', 'entry-level',
    'intern', 'trainee', 'cadet', 'undergraduate', 'new grad',
    'analyst', 'coordinator', 'assistant', 'support officer',
    'graduate program', 'grad program', 'graduate role',
]

# Titles that indicate NOT entry-level (overrides)
SENIOR_KEYWORDS = [
    'senior', 'lead', 'principal', 'director', 'head of',
    'manager', 'staff', 'architect', 'vp ', 'vice president',
    'cto', 'ceo', 'cfo', 'chief', 'lead developer',
]

# Jr managers are still entry — negate if preceded by these
MANAGER_NEGATIONS = ['assistant', 'associate', 'junior', 'graduate', 'trainee']

def load_registry():
    if REGISTRY_FILE.exists():
        with open(REGISTRY_FILE) as f:
            return json.load(f)
    return {'seen_urls': {}, 'seen_ids': {}, 'applications': {}, 'last_run': None}

def save_registry(reg):
    with open(REGISTRY_FILE, 'w') as f:
        json.dump(reg, f, indent=2)

def load_apps():
    if APPS_FILE.exists():
        with open(APPS_FILE) as f:
            return json.load(f)
    return []

def save_apps(apps):
    with open(APPS_FILE, 'w') as f:
        json.dump(apps, f, indent=2)

def job_key(job):
    """Unique key for a job — URL if available, else title+company hash."""
    url = job.get('url', job.get('externalUrl', ''))
    if url:
        return url
    title = job.get('title', '')
    company = job.get('company', job.get('company_name', ''))
    return f"{title}|{company}"

def job_id(job):
    """Short unique identifier."""
    key = job_key(job)
    source = job.get('_source', 'unknown')
    return f"{source}_{abs(hash(key))}"

def is_entry_level(job):
    """
    Heuristic to determine if a job is entry-level suitable.
    Returns: 'yes', 'no', 'maybe'
    """
    title = (job.get('title') or '').lower()
    seniority = (job.get('seniority') or '').lower()
    salary = job.get('salary') or ''
    description = ''
    if job.get('descriptionHtml'):
        description = job['descriptionHtml']
    elif job.get('description'):
        description = job['description']

    # Direct seniority field from Seek (most reliable)
    if seniority:
        entry_types = {'intern', 'entry level', 'graduate', 'trainee', 'junior'}
        if seniority in entry_types:
            return 'yes'
        mid_types = {'mid level', 'associate'}
        if seniority in mid_types:
            return 'maybe'
        if 'senior' in seniority or 'lead' in seniority or 'director' in seniority:
            return 'no'

    # Title-based filtering
    title_lower = title

    # First check for senior signals
    for kw in SENIOR_KEYWORDS:
        if kw in title_lower:
            # Check if negated
            negated = False
            for neg in MANAGER_NEGATIONS:
                if neg in title_lower:
                    negated = True
                    break
            if not negated:
                return 'no'

    # Check for entry signals
    for kw in ENTRY_KEYWORDS:
        if kw in title_lower:
            return 'yes'

    # Salary hint — low salary suggests entry
    if salary:
        salary_str = str(salary).lower()
        # Extract numbers
        nums = re.findall(r'\$?(\d{2,3})[k\s]', salary_str)
        if nums:
            min_salary = min(int(n) for n in nums)
            if min_salary <= 80:
                return 'maybe'

    # Fallback for generic roles that are often entry-level
    generic_entry = [
        'customer service', 'administrative', 'reception', 'data entry',
        'support officer', 'help desk', 'service desk',
    ]
    for kw in generic_entry:
        if kw in title_lower:
            return 'maybe'

    return 'maybe'  # Conservative — let user decide

def find_today_files():
    """Find job files from today."""
    today = date.today().isoformat()
    files = []
    for f in sorted(JOBS_DIR.glob('*.json')):
        if f.name in ('registry.json', 'applications.json'):
            continue
        if f.is_dir():
            continue
        files.append(f)
    return files

def main():
    print("=" * 70)
    print(f"🧹 DAILY JOB PIPELINE — {datetime.now().strftime('%a %d %b %Y %H:%M')}")
    print("=" * 70)

    os.makedirs(QUEUE_DIR, exist_ok=True)
    registry = load_registry()

    # --- Phase 1: Load new jobs ---
    job_files = sorted(JOBS_DIR.glob('*-seek.json')) + sorted(JOBS_DIR.glob('*-indeed.json'))
    today_files = [f for f in job_files if datetime.fromtimestamp(f.stat().st_mtime).date() >= date.today()]

    if not today_files:
        # Fall back to most recent files
        newest = {}
        for f in job_files:
            base = f.name
            if '-seek' in base:
                newest['seek'] = f
            elif '-indeed' in base:
                newest['indeed'] = f
        today_files = list(newest.values())

    print(f"\n📂 Loading from {len(today_files)} file(s):")
    all_jobs = []
    for f in today_files:
        with open(f) as fh:
            jobs = json.load(fh)
        print(f"   {f.name}: {len(jobs)} jobs")
        all_jobs.extend(jobs)

    print(f"\n📊 Total raw: {len(all_jobs)}")

    # --- Phase 2: Deduplicate ---
    seen = set()
    unique = []
    for job in all_jobs:
        key = job_key(job)
        if key and key not in seen and key not in registry['seen_urls']:
            seen.add(key)
            unique.append(job)

    print(f"🆕 New (not in registry): {len(unique)}")

    # --- Phase 3: Filter ---
    entry = []
    maybe = []
    for job in unique:
        verdict = is_entry_level(job)
        if verdict == 'yes':
            entry.append(job)
        elif verdict == 'maybe':
            maybe.append(job)

    print(f"🎯 Entry-level (yes): {len(entry)}")
    print(f"🤔 Entry-level (maybe): {len(maybe)}")
    print(f"❌ Skipped (senior): {len(unique) - len(entry) - len(maybe)}")

    # --- Phase 4: Update registry ---
    now = date.today().isoformat()
    for job in unique:
        key = job_key(job)
        if key:
            registry['seen_urls'][key] = now
        jid = job_id(job)
        registry['seen_ids'][jid] = now
    registry['last_run'] = now
    save_registry(registry)

    # --- Phase 5: Produce queue ---
    queue = entry + maybe
    ts = int(time.time())
    queue_file = QUEUE_DIR / f'{ts}-queue.json'
    with open(queue_file, 'w') as f:
        json.dump({'ts': ts, 'date': now, 'count': len(queue), 'jobs': queue}, f, indent=2)

    # --- Phase 6: Print queue ---
    print(f"\n{'=' * 70}")
    print(f"📋 APPLY QUEUE — {len(queue)} jobs to consider")
    print(f"{'=' * 70}")

    # Group by source for readability
    from itertools import groupby
    queue_sorted = sorted(queue, key=lambda j: j.get('_source', 'unknown'))
    for source, group in groupby(queue_sorted, key=lambda j: j.get('_source', 'unknown')):
        grp = list(group)
        print(f"\n─── {source.upper()} ({len(grp)} jobs) ───")
        for i, job in enumerate(grp[:25], 1):
            title = job.get('title', '?')
            company = job.get('company', job.get('company_name', '?'))
            location = job.get('location', '')
            salary = job.get('salary', '')
            url = job.get('url', job.get('externalUrl', ''))
            seniority = job.get('seniority', '')
            remote = ' [REMOTE]' if job.get('isRemote') or job.get('remote_type') == 'remote' else ''
            verdict = ' ✓' if is_entry_level(job) == 'yes' else ''
            print(f"\n  {i}. {title}{remote}{verdict}")
            print(f"     {company} | {location} {salary}")
            if seniority:
                print(f"     Level: {seniority}")
            if url:
                print(f"     {url}")
        if len(grp) > 25:
            print(f"\n     ... and {len(grp)-25} more")

    print(f"\n{'=' * 70}")
    print(f"📝 Registry: {len(registry['seen_urls'])} seen URLs")
    print(f"   Queue saved: {queue_file}")
    print(f"{'=' * 70}")

    # Print application stats
    apps = load_apps()
    applied_today = [a for a in apps if a.get('date', '') == now]
    if applied_today:
        print(f"\n✅ Already applied today: {len(applied_today)}")
        for a in applied_today:
            print(f"   • {a.get('title')} @ {a.get('company')}")

if __name__ == '__main__':
    main()
