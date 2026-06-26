#!/usr/bin/env python3
"""
Retry missing skill summaries - processes only skills not yet summarized.
"""
import json, os, urllib.request, sys, time
from pathlib import Path

def _load_env():
    env_path = Path("/home/hermeswebui/.hermes/.env")
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k, v)

_load_env()

API_KEY  = os.environ.get("OPENROUTER_API_KEY", "")
MODEL    = "openrouter/auto"
BATCH    = 20
BT       = chr(96) * 3

def generate_summaries_batch(skills: list[dict]) -> dict[str, str]:
    if not API_KEY:
        return {}

    lines = []
    for s in skills:
        name = s.get("name", "?")
        cat  = s.get("category", "?")
        desc = s.get("description", "") or s.get("name", "")
        lines.append(f"- {name} [{cat}]: {desc[:120]}")

    skill_list = "\n".join(lines)

    system_prompt = (
        "You are a skill summarizer. For each skill, output a ONE-LINE description (max 60 chars) "
        "that tells the LLM when to use this skill. Be specific and actionable. "
        'Output JSON like: {"skill-name": "use when..."}'
    )
    user_prompt = (
        "Summarize these skills — one line each (max 60 chars):\n"
        + skill_list
        + '\n\nOutput JSON dict: {"skill-name": "one-line description"}'
    )

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
                "Authorization": "Bearer " + API_KEY,
                "Content-Type": "application/json",
                "HTTP-Referer": "https://hermes-agent.local",
                "X-Title": "Hermes-Agent"
            }
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.load(resp)
        
        # Handle different response structures safely
        choices = result.get("choices")
        if not choices or len(choices) == 0:
            print(f"WARNING: No choices in response", file=sys.stderr)
            return {}
        
        message = choices[0].get("message")
        if not message:
            print(f"WARNING: No message in choice", file=sys.stderr)
            return {}
        
        content = message.get("content")
        if not content:
            print(f"WARNING: No content in message", file=sys.stderr)
            return {}
        
        content = content.strip()

        if content.startswith(BT):
            parts = content.split(BT)
            for p in parts[1::2]:
                p = p.strip()
                if p.startswith("json"):
                    p = p[4:].strip()
                if p.startswith("{"):
                    return json.loads(p)

        return json.loads(content)
    except Exception as e:
        print(f"[FAILED: {e}]", file=sys.stderr)
        return {}

if __name__ == "__main__":
    start_time = time.time()
    
    cache_dir = Path("/home/hermeswebui/.hermes/skill-selector-cache")
    metadata = json.loads((cache_dir / "skill_metadata.json").read_text())
    summaries_data = json.loads((cache_dir / "skill_summaries.json").read_text())
    existing = summaries_data.get("skills", {})

    # Find missing
    missing = [s for s in metadata if s["name"] not in existing]
    print(f"Missing: {len(missing)}", file=sys.stderr)

    total_batches = (len(missing) + BATCH - 1) // BATCH
    new_summaries = {}
    
    for i in range(0, len(missing), BATCH):
        batch_num = i // BATCH + 1
        batch = missing[i:i+BATCH]
        batch_names = [s["name"] for s in batch]
        
        print(f"Batch {batch_num}/{total_batches}: {batch_names[0]}...", file=sys.stderr)
        
        results = generate_summaries_batch(batch)
        new_summaries.update(results)
        
        elapsed = time.time() - start_time
        print(f"  -> {len(new_summaries)}/{len(missing)} (elapsed: {elapsed:.1f}s)", file=sys.stderr)
        
        if batch_num < total_batches:
            time.sleep(0.5)

    # Merge
    existing.update(new_summaries)
    summaries_data["skills"] = existing
    summaries_data["generated_at"] = __import__("datetime").datetime.now().isoformat()
    
    (cache_dir / "skill_summaries.json").write_text(json.dumps(summaries_data, indent=2))
    
    total_time = time.time() - start_time
    print(f"\n=== DONE ===", file=sys.stderr)
    print(f"New summaries: {len(new_summaries)}", file=sys.stderr)
    print(f"Total in file: {len(existing)}", file=sys.stderr)
    print(f"Time: {total_time:.1f}s", file=sys.stderr)