# OpenRouter Credit Exhaustion Pattern

## Symptoms
- Cron jobs fail with HTTP 402: "Insufficient credits. Add more using https://openrouter.ai/settings/credits"
- Jobs that previously worked suddenly start failing
- The error is consistent across all jobs using the same provider

## Diagnosis
1. Check if the error is 402 (not 400) — 402 means credits, 400 means model/config issue
2. Test with a simple API call:
   ```python
   import urllib.request, json, os
   key = os.environ.get('OPENROUTER_API_KEY', '')
   if not key:
       # Try reading from file
       with open('/opt/data/home/.hermes/.env') as f:
           for line in f:
               if line.startswith('OPENROUTER_API_KEY='):
                   key = line.rstrip().split('=', 1)[1]
   req = urllib.request.Request(
       'https://openrouter.ai/api/v1/chat/completions',
       data=json.dumps({'model': 'openrouter/owl-alpha', 'messages': [{'role': 'user', 'content': 'hi'}]}).encode(),
       headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},
       method='POST'
   )
   try:
       resp = urllib.request.urlopen(req, timeout=30)
       print('OK:', resp.status)
   except Exception as e:
       print('ERROR:', e.code, e.read().decode()[:200])
   ```

## Resolution
1. Add credits at https://openrouter.ai/settings/credits
2. Or switch to a provider that has credits (e.g. MiniMax if MINIMAX_API_KEY is set)
3. Or use a free model tier if available

## Prevention
- Monitor credit balance before switching large numbers of cron jobs to a new provider
- Keep at least one cheap fallback provider configured
- Set up the Morning Briefing to include a credit balance check
