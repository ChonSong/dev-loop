#!/usr/bin/env python3
"""Debug version of generate_skill_summaries to find why it returns 0."""
import os, json, urllib.request, sys
from pathlib import Path

# Load env
env_path = Path("/home/hermeswebui/.hermes/.env")
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ.setdefault(k, v)

API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OR_API_KEY = API_KEY
MODEL = "openrouter/auto"
BATCH = 20

cache_dir = Path("/home/hermeswebui/.hermes/skill-selector-cache")
metadata_fp = cache_dir / "skill_metadata.json"
metadata = json.loads(metadata_fp.read_text()) if metadata_fp.exists() else []

total = len(metadata)
print(f"Metadata count: {total}", file=sys.stderr)

for i in range(0, total, BATCH):
    batch = metadata[i:i+BATCH]
    batch_names = [s["name"] for s in batch]
    print(f"  Batch {i//BATCH + 1}/{(total+BATCH-1)//BATCH}: {batch_names[:3]}...", file=sys.stderr)

    # Build skill_list EXACTLY like generate_summaries does
    lines = []
    for s in batch:
        name = s.get("name", "?")
        cat  = s.get("category", "?")
        existing = s.get("description", "")
        lines.append(f"- {name} [{cat}]: {existing[:80]}")
    skill_list = "\n".join(lines)

    system_prompt = (
        "You are a skill summarizer. For each skill, output a ONE-LINE description (max 60 chars) "
        "that tells the LLM when to use this skill. Be specific and actionable. "
        "Output JSON like: {\"skill-name\": \"use when...\"}"
    )
    user_prompt = (
        "Summarize these skills — one line each (max 60 chars):\n"
        + skill_list
        + "\n\nOutput JSON dict: {\"skill-name\": \"one-line description\"}"
    )

    print(f"    API call start...", file=sys.stderr)
    sys.stderr.flush()

    try:
        payload = json.dumps({
            "model": MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt}
            ],
            "max_tokens": 1024,
            "temperature": 0.3
        }).encode()

        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=payload,
            headers={
                "Authorization": "Bearer " + OR_API_KEY,
                "Content-Type": "application/json",
                "HTTP-Referer": "https://hermes-agent.local",
                "X-Title": "Hermes-Agent"
            }
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.load(resp)
        content = result["choices"][0]["message"]["content"].strip()

        print(f"    Raw content (first 200): {content[:200]}", file=sys.stderr)

        # Parse
        results = {}
        if content.startswith("\`\`\`"):
            parts = content.split("\`\`\`")
            for p in parts[1::2]:
                p = p.strip()
                if p.startswith("json"):
                    p = p[4:].strip()
                if p.startswith("{"):
                    results = json.loads(p)
                    print(f"    PARSED OK: {len(results)} skills", file=sys.stderr)
                    break
        else:
            print(f"    No backticks, trying direct parse", file=sys.stderr)
            results = json.loads(content)

        print(f"    Results: {list(results.keys())[:5]}", file=sys.stderr)

    except Exception as e:
        print(f"    EXCEPTION: {e}", file=sys.stderr)

    print(f"    -> {len(results)}/BATCH done", file=sys.stderr)

print("Done!", file=sys.stderr)