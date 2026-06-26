#!/usr/bin/env python3
"""
generate-skill-summaries.py
Called by skill-selector-prep after syncing repos.
Uses batch LLM calls to generate concise one-line summaries for every skill
and group/category descriptions.
"""
import json, os, urllib.request, sys
from pathlib import Path

# Load .env FIRST so API keys are available at module load time
_env_loaded = False
def _load_env():
    global _env_loaded
    if _env_loaded:
        return
    env_path = Path("/home/hermeswebui/.hermes/.env")
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k, v)
    _env_loaded = True

_load_env()

API_KEY      = os.environ.get("OPENROUTER_API_KEY", "")
OR_API_KEY   = os.environ.get("OPENROUTER_API_KEY", "")
MODEL      = "poolside/laguna-xs.2:free"
BATCH        = 20  # skills per LLM call
BT           = chr(96) * 3  # triple backtick

def _load_env():
    env_path = Path("/home/hermeswebui/.hermes/.env")
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k, v)

def generate_summaries(skills: list[dict]) -> dict[str, str]:
    """Call LLM to generate one-line summaries for a batch of skills."""
    if not API_KEY:
        return {}

    lines = []
    for s in skills:
        name = s.get("name", "?")
        cat  = s.get("category", "?")
        existing = s.get("description", "")
        lines.append(f"- {name} [{cat}]: {existing[:80]}")

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
                "Authorization": "Bearer " + OR_API_KEY,
                "Content-Type": "application/json",
                "HTTP-Referer": "https://hermes-agent.local",
                "X-Title": "Hermes-Agent"
            }
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.load(resp)
        content = result["choices"][0]["message"]["content"].strip()

        # Strip code fences using chr(96)*3 for reliable triple backtick detection
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
        print("[generate-skill-summaries failed: " + str(e) + "]", file=sys.stderr)
        return {}

def generate_group_descriptions(summaries: dict, task_types: list[str]) -> dict[str, str]:
    """Generate a one-line description for each skill group/category."""
    if not API_KEY or not task_types:
        return {}

    grouped = {}
    for name, summ in summaries.items():
        for tt in task_types:
            if tt not in grouped:
                grouped[tt] = []
            grouped[tt].append(name)

    lines = [f"- {tt}: {', '.join(groups[:5])}" for tt, groups in list(grouped.items())[:15]]
    if not lines:
        return {}

    prompt_text = (
        "For each group below, write ONE LINE (max 80 chars) describing what those skills do collectively.\n"
        + "\n".join(lines)
        + '\n\nOutput JSON like: {"coding": "skills for writing, testing, and reviewing code", ...}'
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
                "Authorization": "Bearer " + OR_API_KEY,
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
        print("[generate_group_descriptions failed: " + str(e) + "]", file=sys.stderr)
        return {}

if __name__ == "__main__":
    cache_dir = Path("/home/hermeswebui/.hermes/skill-selector-cache")
    metadata_fp = cache_dir / "skill_metadata.json"

    metadata = json.loads(metadata_fp.read_text()) if metadata_fp.exists() else []

    total = len(metadata)
    print(f"Generating summaries for {total} skills...", file=sys.stderr)

    all_summaries = {}
    for i in range(0, total, BATCH):
        batch = metadata[i:i+BATCH]
        batch_names = [s["name"] for s in batch]
        print(f"  Batch {i//BATCH + 1}/{(total+BATCH-1)//BATCH}: {batch_names[:3]}...", file=sys.stderr)
        results = generate_summaries(batch)
        all_summaries.update(results)
        if i + BATCH < total:
            print(f"    -> {len(all_summaries)}/{total} done", file=sys.stderr)

    print(f"Generated {len(all_summaries)} summaries", file=sys.stderr)

    # Generate group descriptions
    task_types = ["coding", "deployment", "git_operation", "research", "creative",
                  "writing", "devops", "planning", "data_analysis", "autonomous", "configuration"]
    group_descs = generate_group_descriptions(all_summaries, task_types)
    print(f"Generated {len(group_descs)} group descriptions", file=sys.stderr)

    output = {
        "skills": all_summaries,
        "groups": group_descs,
        "generated_at": __import__("datetime").datetime.now().isoformat()
    }

    out_fp = cache_dir / "skill_summaries.json"
    out_fp.write_text(json.dumps(output, indent=2))
    print(f"Wrote {len(all_summaries)} summaries + {len(group_descs)} group descriptions to {out_fp}", file=sys.stderr)