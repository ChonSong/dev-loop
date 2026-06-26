#!/usr/bin/env python3
"""
Standalone Seek job search via Apify API.
No dependencies beyond stdlib (urllib, json, os, sys, time, argparse).

Usage:
    python3 seek_search.py --positions "Data Scientist,ML Engineer" \\
        --locations "Sydney, NSW" --max 200
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
    parser.add_argument('--positions', required=True, help='Job titles, comma-separated')
    parser.add_argument('--locations', default='', help='Locations, comma-separated')
    parser.add_argument('--max', type=int, default=200, help='Max results per position×location')
    parser.add_argument('--outdir', default='~/.hermes/jobs', help='Output directory')
    args = parser.parse_args()

    token = get_token()
    outdir = os.path.expanduser(args.outdir)
    os.makedirs(outdir, exist_ok=True)

    positions = [p.strip() for p in args.positions.split(',') if p.strip()]
    locations = [l.strip() for l in args.locations.split(',') if l.strip()]

    payload = {
        'positions': positions,
        'locations': locations if locations else None,
        'maxItemsPerSearch': args.max,
        'proxyConfiguration': {
            'useApifyProxy': True,
            'apifyProxyGroups': ['RESIDENTIAL']
        }
    }

    print(f'Searching Seek for {positions} in {locations or "nationwide"}...')

    resp = api(f'{BASE}/acts/scrapersdelight~seek-jobs-scraper/runs', data=payload, token=token)
    run_id = resp['data']['id']
    dataset_id = resp['data'].get('defaultDatasetId')
    print(f'  Run: {run_id}')

    for attempt in range(60):  # Seek tends to take longer than Indeed
        time.sleep(10)
        data = api(f'{BASE}/actor-runs/{run_id}', token=token)
        status = data['data']['status']
        if attempt % 6 == 0:
            print(f'  [{attempt*10}s] {status}')
        if status in ('SUCCEEDED', 'FAILED', 'ABORTED', 'TIMED-OUT'):
            break

    if status != 'SUCCEEDED' or not dataset_id:
        print(f'Run finished with status: {status}', file=sys.stderr)
        sys.exit(1)

    items = api(f'{BASE}/datasets/{dataset_id}/items', token=token)
    print(f'\nResults: {len(items)} total')

    for job in items[:30]:
        title = job.get('title', '')
        company = job.get('company', '')
        location = job.get('location', '')
        url_job = job.get('url', '')
        salary = job.get('salary', '')
        remote = ' [REMOTE]' if job.get('isRemote') else ''
        contact = job.get('contactEmail', '')
        contact_info = f' | {contact}' if contact else ''
        print(f'  {title}{remote} | {company} | {location} | {salary}{contact_info}')
        print(f'    {url_job}')

    if len(items) > 30:
        print(f'  ... and {len(items)-30} more')

    ts = int(time.time())
    outfile = os.path.join(outdir, f'{ts}_seek.json')
    with open(outfile, 'w') as f:
        json.dump(items, f, indent=2)
    print(f'\nSaved: {outfile}')

    # Print credit usage if available
    usage = resp.get('data', {}).get('stats', {}).get('computeUnits', 0)
    print(f'Credits used: {usage:.2f} CU')

if __name__ == '__main__':
    main()