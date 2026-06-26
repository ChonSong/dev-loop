#!/usr/bin/env python3
"""
Daily Indeed job search — cron script (no_agent).
Runs broad entry-level keywords across AU via Apify, saves results, prints summary.
Actor: sheshinmcfly~indeed-jobs-scraper ($5/1k results)
"""
import os, sys, json, time, urllib.request, urllib.error

BASE = 'https://api.apify.com/v2'
TOKEN_PATH = os.path.expanduser('~/.hermes/secrets/apify.env')
OUTDIR = os.path.expanduser('~/.hermes/jobs')

# Broad entry-level keywords
KEYWORDS = [
    "graduate,junior,associate,entry level,analyst",
    "trainee,intern,cadet,undergraduate,new grad",
    "software engineer junior,data analyst entry,IT support",
    "administrative assistant,customer service,operations coordinator",
    "sales associate,marketing coordinator,project support",
]

LOCATIONS = [
    "Sydney, NSW",
    "Melbourne, VIC",
    "Brisbane, QLD",
    "Perth, WA",
    "Adelaide, SA",
]

def get_token():
    if not os.path.exists(TOKEN_PATH):
        print(f'ERROR: Apify token not found at {TOKEN_PATH}', file=sys.stderr)
        sys.exit(1)
    with open(TOKEN_PATH) as f:
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
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

def search_indeed(payload, token):
    resp = api(f'{BASE}/acts/sheshinmcfly~indeed-jobs-scraper/runs', data=payload, token=token)
    run_id = resp['data']['id']
    dataset_id = resp['data'].get('defaultDatasetId')
    for attempt in range(30):
        time.sleep(5)
        data = api(f'{BASE}/actor-runs/{run_id}', token=token)
        status = data['data']['status']
        if status in ('SUCCEEDED', 'FAILED', 'ABORTED', 'TIMED-OUT'):
            break
    if status != 'SUCCEEDED' or not dataset_id:
        return [], run_id, status, 0.0
    items = api(f'{BASE}/datasets/{dataset_id}/items', token=token)
    usage = resp.get('data', {}).get('stats', {}).get('computeUnits', 0)
    return items, run_id, status, usage

def main():
    print("=" * 60)
    print("Daily Indeed Job Search")
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    token = get_token()
    os.makedirs(OUTDIR, exist_ok=True)

    all_jobs = []
    total_cost = 0.0

    for keywords in KEYWORDS:
        positions = [k.strip() for k in keywords.split(',') if k.strip()]
        for location in LOCATIONS:
            payload = {
                'positions': positions,
                'locations': [location],
                'country': 'AU',
                'maxItemsPerSearch': 30,
                'proxyConfiguration': {
                    'useApifyProxy': True,
                    'apifyProxyGroups': ['RESIDENTIAL']
                }
            }
            print(f"\n🔍 {keywords} | {location}")
            try:
                items, run_id, status, usage = search_indeed(payload, token)
                cost = len(items) / 1000 * 5.00
                total_cost += cost
                print(f"   {len(items)} jobs — ${cost:.4f} (CU: {usage})")
                for j in items:
                    j['_source'] = 'indeed'
                    j['_search_keywords'] = keywords
                    j['_search_location'] = location
                all_jobs.extend(items)
            except Exception as e:
                print(f"   ❌ Failed: {e}")

    ts = int(time.time())
    outfile = os.path.join(OUTDIR, f'{ts}-indeed.json')
    with open(outfile, 'w') as f:
        json.dump(all_jobs, f, indent=2)

    print(f"\n{'=' * 60}")
    print(f"TOTAL: {len(all_jobs)} jobs across searches")
    print(f"Estimated cost: ${total_cost:.4f}")
    print(f"Saved: {outfile}")
    print(f"{'=' * 60}")

if __name__ == '__main__':
    main()
