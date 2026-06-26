#!/usr/bin/env python3
"""
Generate LLM summaries for all 1429 skills in the catalog.
Batch of 20 per LLM call, skip already-summarized ones.
"""
import json, os, urllib.request, sys, time
from pathlib import Path

# Load .env FIRST so API keys are available
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
BT       = chr(96) * 3  # triple backtick

def generate_summaries_batch(skills: list[dict]) -> dict[str, str]:
    """Call LLM to generate one-line summaries for a batch of skills."""
    if not API_KEY:
        print("ERROR: No API key found", file=sys.stderr)
        return {}

    lines = []
    for s in skills:
        name = s.get("name", "?")
        cat  = s.get("category", "?")
        desc = s.get("description", "") or s.get("name", "")
        # Truncate description but include it for context
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
        content = result["choices"][0]["message"]["content"].strip()

        # Strip code fences
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
        print(f"[generate_summaries_batch failed: {e}]", file=sys.stderr)
        return {}

def generate_group_descriptions(top_categories: list[tuple[str, int]]) -> dict[str, str]:
    """Generate a one-line description for each top category."""
    if not API_KEY or not top_categories:
        return {}

    lines = [f"- {cat} ({count} skills)" for cat, count in top_categories[:20]]

    prompt_text = (
        "For each category below, write ONE LINE (max 80 chars) describing what those skills do collectively.\n"
        + "\n".join(lines)
        + '\n\nOutput JSON like: {"nvidia": "skills for working with NVIDIA GPUs, CUDA, and GPU computing", ...}'
    )

    try:
        payload = json.dumps({
            "model": MODEL,
            "messages": [
                {"role": "system", "content": "You are a skill grouping assistant. Output valid JSON only."},
                {"role": "user",   "content": prompt_text}
            ],
            "max_tokens": 512,
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
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.load(resp)
        content = result["choices"][0]["message"]["content"].strip()

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
        print(f"[generate_group_descriptions failed: {e}]", file=sys.stderr)
        return {}

if __name__ == "__main__":
    start_time = time.time()
    
    cache_dir = Path("/home/hermeswebui/.hermes/skill-selector-cache")
    metadata_fp = cache_dir / "skill_metadata.json"
    summaries_fp = cache_dir / "skill_summaries.json"

    # Load metadata
    metadata = json.loads(metadata_fp.read_text()) if metadata_fp.exists() else []
    total_skills = len(metadata)
    print(f"Total skills in metadata: {total_skills}", file=sys.stderr)

    # Load existing summaries
    existing = {}
    if summaries_fp.exists():
        existing_data = json.loads(summaries_fp.read_text())
        existing = existing_data.get("skills", {})
    existing_count = len(existing)
    print(f"Already summarized: {existing_count}", file=sys.stderr)

    # Find skills not yet summarized
    skills_to_summarize = []
    for s in metadata:
        if s["name"] not in existing:
            skills_to_summarize.append(s)
    
    remaining = len(skills_to_summarize)
    print(f"Skills needing summaries: {remaining}", file=sys.stderr)
    
    if remaining > 0:
        # Process in batches of 20
        total_batches = (remaining + BATCH - 1) // BATCH
        all_new_summaries = {}
        
        for i in range(0, remaining, BATCH):
            batch_num = i // BATCH + 1
            batch = skills_to_summarize[i:i+BATCH]
            batch_names = [s["name"] for s in batch]
            
            print(f"Batch {batch_num}/{total_batches}: processing {len(batch)} skills (first: {batch_names[0]})...", file=sys.stderr)
            
            results = generate_summaries_batch(batch)
            all_new_summaries.update(results)
            
            elapsed = time.time() - start_time
            processed = i + len(batch)
            rate = processed / elapsed if elapsed > 0 else 0
            eta = (remaining - processed) / rate if rate > 0 else 0
            print(f"  -> {len(all_new_summaries)} new summaries so far (elapsed: {elapsed:.1f}s, ETA: {eta:.1f}s)", file=sys.stderr)
            
            # Small delay to avoid rate limiting
            if batch_num < total_batches:
                time.sleep(0.5)

        # Merge existing and new summaries
        merged_summaries = {**existing, **all_new_summaries}
    else:
        merged_summaries = existing
        all_new_summaries = {}

    # Calculate categories for group descriptions
    categories = {}
    for s in metadata:
        c = s.get("category", "unknown")
        categories[c] = categories.get(c, 0) + 1
    sorted_categories = sorted(categories.items(), key=lambda x: -x[1])

    print(f"\nTop 20 categories by skill count:", file=sys.stderr)
    for cat, count in sorted_categories[:20]:
        print(f"  {cat}: {count}", file=sys.stderr)

    # Generate group descriptions for top 20 categories
    print("\nGenerating group descriptions for top 20 categories...", file=sys.stderr)
    group_descs = generate_group_descriptions(sorted_categories[:20])
    print(f"Generated {len(group_descs)} group descriptions", file=sys.stderr)

    # Build final output
    output = {
        "skills": merged_summaries,
        "groups": group_descs,
        "generated_at": __import__("datetime").datetime.now().isoformat()
    }

    # Write output
    out_fp = cache_dir / "skill_summaries.json"
    out_fp.write_text(json.dumps(output, indent=2))

    total_time = time.time() - start_time
    
    print(f"\n=== SUMMARY ===", file=sys.stderr)
    print(f"Total skills in catalog: {total_skills}", file=sys.stderr)
    print(f"Previously summarized: {existing_count}", file=sys.stderr)
    print(f"Newly summarized: {len(all_new_summaries)}", file=sys.stderr)
    print(f"Total in final file: {len(merged_summaries)}", file=sys.stderr)
    print(f"Skills missing summaries: {total_skills - len(merged_summaries)}", file=sys.stderr)
    print(f"Total batches needed: {total_batches if remaining > 0 else 0}", file=sys.stderr)
    print(f"Group descriptions: {len(group_descs)}", file=sys.stderr)
    print(f"Total time: {total_time:.1f} seconds", file=sys.stderr)
    print(f"Wrote to: {out_fp}", file=sys.stderr)