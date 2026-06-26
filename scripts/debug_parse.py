#!/usr/bin/env python3
import os, json, urllib.request, sys
from pathlib import Path

env_path = '/home/hermeswebui/.hermes/.env'
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ.setdefault(k, v)

OR_API_KEY = os.environ.get('OPENROUTER_API_KEY', '')
MODEL = 'openrouter/auto'
BATCH = 20

metadata_fp = Path('/home/hermeswebui/.hermes/skill-selector-cache/skill_metadata.json')
metadata = json.loads(metadata_fp.read_text())
batch = metadata[0:3]

lines = []
for s in batch:
    name = s.get('name', '?')
    cat  = s.get('category', '?')
    existing = s.get('description', '')
    lines.append(f'- {name} [{cat}]: {existing[:80]}')
skill_list = '\n'.join(lines)

system_prompt = (
    'You are a skill summarizer. For each skill, output a ONE-LINE description (max 60 chars) '
    'that tells the LLM when to use this skill. Be specific and actionable. '
    'Output JSON like: {"skill-name": "use when..."}'
)
user_prompt = (
    'Summarize these skills — one line each (max 60 chars):\n'
    + skill_list
    + '\n\nOutput JSON dict: {"skill-name": "one-line description"}'
)

print('=== Calling API ===')
sys.stdout.flush()

payload = json.dumps({
    'model': MODEL,
    'messages': [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user',   'content': user_prompt}
    ],
    'max_tokens': 1024,
    'temperature': 0.3
}).encode()

req = urllib.request.Request(
    'https://openrouter.ai/api/v1/chat/completions',
    data=payload,
    headers={
        'Authorization': 'Bearer ' + OR_API_KEY,
        'Content-Type': 'application/json',
        'HTTP-Referer': 'https://hermes-agent.local',
        'X-Title': 'Hermes-Agent'
    }
)
with urllib.request.urlopen(req, timeout=60) as resp:
    result = json.load(resp)
content = result['choices'][0]['message']['content'].strip()

print('Content repr:', ascii(content[:300]))
sys.stdout.flush()

print()
print('=== Parse logic ===')
starts_with_backtick = content.startswith(chr(96) + chr(96) + chr(96))
print('starts_with_backtick:', starts_with_backtick)

if starts_with_backtick:
    parts = content.split(chr(96) + chr(96) + chr(96))
    print('len(parts):', len(parts))

    for idx, p in enumerate(parts):
        print(f'  part[{idx}] len={len(p)}: {ascii(p[:60])}')

    for p in parts[1::2]:
        p_stripped = p.strip()
        print('stripped p[:60]:', ascii(p_stripped[:60]))
        print('startswith(json):', p_stripped.startswith('json'))
        if p_stripped.startswith('json'):
            p_stripped = p_stripped[4:].strip()
            print('after json strip[:60]:', ascii(p_stripped[:60]))
        print('startswith({):', p_stripped.startswith('{'))
        if p_stripped.startswith('{'):
            try:
                parsed = json.loads(p_stripped)
                print('SUCCESS! Keys:', list(parsed.keys()))
            except Exception as e:
                print('FAIL:', e)
        else:
            print('Not JSON, skipping')
else:
    print('No backtick prefix')
    try:
        parsed = json.loads(content)
        print('Direct parse OK:', list(parsed.keys()))
    except Exception as e:
        print('Direct parse FAIL:', e)