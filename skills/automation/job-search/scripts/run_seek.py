#!/usr/bin/env python3
"""
Standalone Seek job search via Apify API.
"""
import os, json, time, sys, urllib.request, urllib.error

BASE = 'https://api.apify.com/v2'

def get_token():
    path = os.path.expanduser('~/.hermes/secrets/apify.env')
    with open(path) as f:
        val = f.read().strip()
        if '=' in val:
            val = val.split('=', 1)[1].strip()
        return val

def api(url, data=None, token=None):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    if data is not None:
        req = urllib.request.Request(url, data=json.dumps(data).encode(), headers=headers, method='POST')
    else:
        req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors='replace')[:500]
        print(f'HTTP {e.code}: {body}', file=sys.stderr)
        sys.exit(1)

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Search Seek via Apify')
    parser.add_argument('--keywords', default='Data Scientist', help='Search term')
    parser.add_argument('--location', default='Sydney', help='City/suburb')
    parser.add_argument('--state', default='NSW', help='State')
    parser.add_argument('--remote', action='store_true', help='Remote only')
    parser.add_argument('--max', type=int, default=200, help='Max results')
    parser.add_argument('--outdir', default='~/.hermes/jobs')
    parser.add_argument('--days', type=int, default=7, help='Days to look back')
    args = parser.parse_args()

    token = get_token()
    outdir = os.path.expanduser(args.outdir)
    os.makedirs(outdir, exist_ok=True)

    work_arrangements = ['remote'] if args.remote else ['remote', 'hybrid', 'on-site']

    payload = {
        "searchTerm": args.keywords,
        "location": args.location,
        "state": args.state,
        "sortBy": "ListedDate",
        "dateRange": args.days,
        "workArrangements": work_arrangements,
        "workTypes": ["fulltime"],
        "maxResults": args.max
    }

    print(f'Searching Seek AU for "{args.keywords}" in {args.location}, {args.state}...')
    resp = api(f'{BASE}/acts/websift~seek-job-scraper/runs', data=payload, token=token)
    run_id = resp['data']['id']
    dataset_id = resp['data'].get('defaultDatasetId')
    print(f'  Run: {run_id}')

    for attempt in range(30):
        time.sleep(5)
        data = api(f'{BASE}/actor-runs/{run_id}', token=token)
        status = data['data']['status']
        if attempt % 6 == 0:
            print(f'  [{attempt*5}s] {status}')
        if status in ('SUCCEEDED', 'FAILED', 'ABORTED', 'TIMED-OUT'):
            break

    if status != 'SUCCEEDED' or not dataset_id:
        print(f'Run finished with status: {status}', file=sys.stderr)
        sys.exit(1)

    items = api(f'{BASE}/datasets/{dataset_id}/items', token=token)
    print(f'\nResults: {len(items)}')

    for job in items[:20]:
        loc = job.get('joblocationInfo', {}).get('displayLocation', '')
        company = job.get('companyName', '')
        title = job.get('title', '')
        salary = job.get('salary', '')
        print(f'  {title} | {company} | {loc} | {salary}')

    if len(items) > 20:
        print(f'  ... and {len(items)-20} more')

    ts = int(time.time())
    outfile = os.path.join(outdir, f'{ts}-seek.json')
    with open(outfile, 'w') as f:
        json.dump(items, f, indent=2)
    print(f'\nSaved: {outfile}')

    usage = resp.get('data', {}).get('stats', {}).get('computeUnits', 0)
    print(f'Credits used: {usage:.2f} CU  (${usage*0.0025:.4f})')

if __name__ == '__main__':
    main()
