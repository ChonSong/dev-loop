#!/usr/bin/env python3
"""Summarize skill batches via OpenRouter free tier using stdin pipe."""
import json, subprocess, time, re

BATCH_SIZE = 20
SLEEP = 2.5
PAYLOAD = {
    "model": "openrouter/free",
    "messages": [{"role": "user", "content": "PLACEHOLDER"}],
    "max_tokens": 600,
    "temperature": 0.3
}

def call_llm(prompt):
    payload = json.dumps(PAYLOAD).replace('"PLACEHOLDER"', json.dumps(prompt))
    r = subprocess.run(
        ['ssh', '-i', '/home/hermeswebui/.hermes/container_key', '-o', 'StrictHostKeyChecking=no',
         'sean@172.19.0.1',
         f'source ~/.hermes/.env 2>/dev/null; '
         f'echo \'{payload}\' | curl -s "https://openrouter.ai/api/v1/chat/completions" '
         f'-H "Authorization: Bearer $OPENROUTER_API_KEY" '
         f'-H "Content-Type: application/json" -d @-'],
        capture_output=True, text=True, timeout=45
    )
    return r.stdout.strip()

def parse_batch(raw, names):
    results = {}
    try:
        data = json.loads(raw)
        content = data.get('choices', [{}])[0].get('message', {}).get('content', '') or \
                 data.get('choices', [{}])[0].get('message', {}).get('reasoning', '') or ''
        # Extract JSON from content
        m = re.search(r'\{[\s\S]+?\}', content)
        if m:
            d = json.loads(m.group())
            for k, v in d.items():
                if k in names and isinstance(v, str) and len(v) > 3:
                    results[k] = v[:55]
    except:
        pass
    return results

def main():
    with open('/home/hermeswebui/.hermes/skill-selector-cache/batches.json') as f:
        batches = json.load(f)
    with open('/home/hermeswebui/.hermes/skill-selector-cache/skill_summaries.json') as f:
        summaries = json.load(f)

    existing = set(summaries.get('skills', {}).keys())
    count = 0
    err = 0

    for i, batch in enumerate(batches):
        names = [b['name'] for b in batch]
        need = [n for n in names if n not in existing]
        if not need:
            continue

        prompt = (f'For each skill below, write a one-line description (max 55 chars) starting with "use when". '
                 f'Output JSON only as plain text (no markdown). Skills: {", ".join(need)}')
        raw = call_llm(prompt)
        results = parse_batch(raw, need)

        if results:
            for k, v in results.items():
                summaries['skills'][k] = v
                existing.add(k)
                count += 1
            with open('/home/hermeswebui/.hermes/skill-selector-cache/skill_summaries.json', 'w') as f:
                json.dump(summaries, f)
            print(f'B{i}: +{len(results)} ({count} total)')
        else:
            err += 1
            print(f'B{i}: ERR (err={err}, raw={raw[:80]})')
            if err >= 5:
                print('Too many failures')
                break
        time.sleep(SLEEP)

    print(f'\nTotal: {count} new, {err} failures, {len(summaries["skills"])} skills cached')

if __name__ == '__main__':
    main()