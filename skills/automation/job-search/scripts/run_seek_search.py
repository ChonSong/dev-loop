#!/usr/bin/env python3
"""
Seek job search via Apify API.
Uses bovi/seek-jobs-scraper ($0.90/1k results).
"""
import os, sys, json, time, argparse, urllib.request, urllib.error

BASE = 'https://api.apify.com/v2'

def get_token():
    path = os.path.expanduser('~/.hermes/secrets/apify.env')
    if not os.path.exists(path):
        print(f'ERROR: Apify token not found at {path}', file=sys.stderr)
        sys.exit(1)
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
    parser = argparse.ArgumentParser(description='Search Seek via Apify')
    parser.add_argument('--keywords', required=True, help='Job keywords, comma-separated')
    parser.add_argument('--location', default='', help='Location filter (e.g. "Sydney NSW")')
    parser.add_argument('--site', default='AU-Main', help='Site key (AU-Main or NZ-Main)')
    parser.add_argument('--max', type=int, default=200, help='Max results')
    parser.add_argument('--remote', action='store_true', help='Remote-only')
    parser.add_argument('--outdir', default='~/.hermes/jobs', help='Output directory')
    args = parser.parse_args()

    token = get_token()
    outdir = os.path.expanduser(args.outdir)
    os.makedirs(outdir, exist_ok=True)

    search_queries = [q.strip() for q in args.keywords.split(',') if q.strip()]

    payload = {
        'searchQueries': search_queries,
        'siteKey': args.site,
        'maxItems': args.max,
        'includeDescriptions': False,
    }
    if args.location:
        payload['where'] = args.location
    if args.remote:
        payload['remoteOnly'] = True

    site_label = 'NZ' if args.site == 'NZ-Main' else 'AU'
    loc_label = args.location or 'nationwide'
    print(f'Searching Seek {site_label} for {search_queries} in {loc_label}...')

    resp = api(f'{BASE}/acts/bovi~seek-jobs-scraper/runs', data=payload, token=token)
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
    print(f'\nResults: {len(items)} jobs total')

    for job in items[:30]:
        title = job.get('title', '')
        company = job.get('company', '')
        location = job.get('location', '')
        salary = job.get('salary', '')
        remote = {'remote': ' [REMOTE]', 'hybrid': ' [HYBRID]', None: ''}.get(job.get('remote_type'), '')
        seniority = job.get('seniority', '')
        print(f'  {title}{remote} | {company} | {location} | {salary} (seniority: {seniority})')
        url_job = job.get('url', '')
        if url_job:
            print(f'    {url_job}')

    if len(items) > 30:
        print(f'  ... and {len(items)-30} more')

    ts = int(time.time())
    outfile = os.path.join(outdir, f'{ts}-seek.json')
    with open(outfile, 'w') as f:
        json.dump(items, f, indent=2)
    print(f'\nSaved: {outfile}')

    # Print credit usage if available
    usage = resp.get('data', {}).get('stats', {}).get('computeUnits', 0)
    print(f'Credits used: {usage:.2f} CU')
    print(f'Estimated: ${len(items)/1000*0.90:.4f} (at $0.90/1k)')

if __name__ == '__main__':
    main()
