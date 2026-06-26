#!/usr/bin/env python3
"""
Stream-summarize remaining unsummarized skills.
poolside/laguna-xs.2:free embeds the response in the `reasoning` field, not `content`.
Uses streaming JSON parsing for robustness against truncated responses.
"""
import json, os, urllib.request, sys, re
from pathlib import Path

env_path = Path("/home/hermeswebui/.hermes/.env")
if env_path.exists():
    for line in open(env_path):
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ.setdefault(k, v)

API_KEY = os.environ.get("POOLSIDE_API_KEY", os.environ.get("OPENROUTER_API_KEY", ""))
MODEL   = "iqp/small-eagle-2505:free"  # free, fast
BATCH   = 15
BT      = chr(96) * 3

CACHE_DIR = Path("/home/hermeswebui/.hermes/skill-selector-cache")
META_FILE  = CACHE_DIR / "skill_metadata.json"
SUMM_FILE  = CACHE_DIR / "skill_summaries.json"

def load_json(path):
    try:
        return json.loads(open(path).read()) if path.exists() else {}
    except: return {}

metadata = load_json(META_FILE)
summaries = load_json(SUMM_FILE)

# Determine unsummarized
done = set(summaries.get('skills', {}).keys())
need = [s for s in metadata if s['name'] not in done]
print(f"Need: {len(need)}")

if not need:
    print("All done.")
    sys.exit(0)

# Build context for each unsummarized skill
items = []
for s in need:
    cat = s.get('category', '?')
    desc = s.get('description', s.get('tags', []))
    if isinstance(desc, list):
        desc = ', '.join(desc)
    items.append((s['name'], cat, str(desc)[:120]))

print(f"Total to summarize: {len(items)}")

def call_llm(batch):
    if not API_KEY:
        print("No API key found.")
        return {}
    lines = []
    for name, cat, desc in batch:
        lines.append(f"- {name} [{cat}]: {desc}")
    skill_list = "\n".join(lines)
    system = (
        "You are a skill summarizer. For each skill output a ONE-LINE description (max 55 chars) "
        'describing when to use it. Output ONLY valid JSON: {"skill-name": "use when..."}.'
    )
    user = f"Summarize:\n{skill_list}\n\nJSON only:"
    payload = json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ],
        "max_tokens": 800,
        "temperature": 0.3
    }).encode()

    try:
        req = urllib.request.Request(
            "https://api.openrouter.ai/api/v1/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://hermes-agent",
                "X-Title": "skill-summarizer"
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode()
        data = json.loads(raw)
        # poolside embeds in reasoning; most models use content
        content = (data.get("choices", [{}])[0]
                   .get("message", {})
                   .get("content", "") or
                   data.get("choices", [{}])[0]
                   .get("message", {})
                   .get("reasoning", ""))
        return parse_json_flexible(content)
    except Exception as e:
        print(f"  API error: {e}")
        return {}

def parse_json_flexible(text: str) -> dict:
    """Extract JSON from potentially truncated response."""
    text = text.strip()
    # Try direct parse
    try:
        return json.loads(text)
    except:
        pass
    # Try finding JSON object in text
    m = re.search(r'\{["\w\-\s,\.:]+\}', text)
    if m:
        try:
            return json.loads(m.group())
        except:
            pass
    # Try extracting all key:"value" pairs
    pairs = re.findall(r'"([^"]+)"\s*:\s*"([^"]{5,200})"', text)
    if pairs:
        return {k: v for k, v in pairs}
    return {}

results = {}
total_batches = (len(items) + BATCH - 1) // BATCH

for i in range(0, len(items), BATCH):
    batch = items[i:i+BATCH]
    batch_num = i // BATCH + 1
    names = [b[0] for b in batch]
    print(f"  Batch {batch_num}/{total_batches}: {names[:3]}...")
    batch_results = call_llm(batch)
    results.update(batch_results)
    # Small delay between calls to avoid rate limits
    import time; time.sleep(1.2)

# Merge into existing summaries
all_skills = summaries.get('skills', {})
for name, summary in results.items():
    if summary and len(summary) > 5:
        all_skills[name] = summary.strip()[:200]

summaries['skills'] = all_skills
SUMM_FILE.write_text(json.dumps(summaries, indent=2))
print(f"\nWrote {len(results)} summaries. Total skills with summaries: {len(all_skills)}")