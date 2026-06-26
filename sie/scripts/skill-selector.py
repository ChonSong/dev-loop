#!/usr/bin/env python3
"""
skill-selector: Every-turn smart skill scorer.
Loads cached summaries + task classifications, scores skills by:
  1. Task type classification (rule-based) → known skill groups
  2. Workflow stage detection
  3. Summary keyword matching
  4. LLM tiebreaker (only when borderline — 1 LLM call per turn max)
"""
import json, re, sys, os, urllib.request
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
CACHE_DIR    = Path("/home/sc/.hermes/skill-selector-cache")
METADATA_FP  = CACHE_DIR / "skill_metadata.json"
CONTEXT_FP   = CACHE_DIR / "context_scores.json"
SUMMARIES_FP = CACHE_DIR / "skill_summaries.json"
SKILLS_DIR   = Path("/home/sc/.hermes/skills")
MAX_LOAD     = 5
MB_ASK       = 100
API_KEY      = os.environ.get("OPENROUTER_API_KEY", "")
LLM_MODEL    = "openrouter/auto"

# ── Load caches ────────────────────────────────────────────────────────────────
def load_caches():
    metadata    = json.loads(METADATA_FP.read_text())  if METADATA_FP.exists()  else []
    ctx_scores  = json.loads(CONTEXT_FP.read_text())   if CONTEXT_FP.exists()   else {}
    summaries   = json.loads(SUMMARIES_FP.read_text()) if SUMMARIES_FP.exists() else {}
    return metadata, ctx_scores, summaries

# ── Task classification (rule-based, no LLM) ──────────────────────────────────
TASK_TYPE_PATTERNS = [
    ("deployment",     ["deploy", "ship", "release", "production", "staging", "kubernetes", "helm", "rollback", "docker push", "publish"]),
    ("git_operation",  ["git ", "commit", "branch", "merge", "pr ", "pull request", "push", "clone", "fork", "rebase"]),
    ("coding",         ["implement", "write code", "function", "component", "fix bug", "refactor", "add feature", "code", "typescript", "python", "golang", "rust", "react", "svelte", "node"]),
    ("debugging",      ["bug", "crash", "error", "break", "not working", "issue", "failed", "exception", "traceback", "fix the"]),
    ("research",       ["research", "arxiv", "paper", "find", "search for", "look up", "investigate", "explore", "analyze trend"]),
    ("creative",       ["generate image", "create video", "make art", "ascii", "svg", "animation", "music", "song", "design"]),
    ("writing",        ["write", "essay", "document", "report", "summary", "article", "blog post", "draft"]),
    ("planning",       ["plan", "roadmap", "architecture", "design for", "how to build", "blueprint", "spec out"]),
    ("devops",         ["ci/cd", "pipeline", "terraform", "ansible", "nginx", "apache", "config", "setup server", "cron", "backup"]),
    ("data_analysis",  ["analyze", "jupyter", "pandas", "notebook", "visualize", "chart", "graph", "data"]),
    ("autonomous",     ["autonomous", "roadmap", "self-improve", "learn and", "iterate on"]),
    ("configuration",  ["configure", "setup", "install", "enable", "disable", "settings", "config"]),
    ("monitoring",     ["monitor", "watch", "alert", "metrics", "dashboard", "health", "uptime"]),
    ("smart_home",     ["hue", "light", "sonos", "smart home", "home assistant", "philips"]),
    ("media",          ["spotify", "youtube", "gif", "play audio", "video"]),
]

STAGE_PATTERNS = [
    ("understand", ["understand", "what is", "how does", "explain", "find out", "discover", "search for", "investigate"]),
    ("plan",       ["plan", "design", "spec", "architecture", "blueprint", "roadmap", "should i", "approach"]),
    ("implement",  ["implement", "write", "create", "build", "make", "add", "code", "develop"]),
    ("test",       ["test", "verify", "check", "ensure", "validate", "qa", "quality"]),
    ("review",     ["review", "refactor", "improve", "optimize", "clean up", "tidy"]),
    ("deploy",     ["deploy", "ship", "release", "publish", "push to", "go live"]),
    ("monitor",    ["monitor", "watch", "observe", "track", "measure", "alert"]),
]

def classify_task(text: str):
    text_lower = text.lower()
    task_types = set()
    stages     = set()
    for ttype, patterns in TASK_TYPE_PATTERNS:
        if any(p in text_lower for p in patterns):
            task_types.add(ttype)
    for stage, patterns in STAGE_PATTERNS:
        if any(p in text_lower for p in patterns):
            stages.add(stage)
    if not task_types:
        task_types.add("general")
    if not stages:
        stages.add("implement")
    return task_types, stages

# ── Summary-based scoring ─────────────────────────────────────────────────────
def score_by_summary(skill: dict, task_types: set, stages: set, summaries: dict, text: str) -> float:
    s = 0.0
    name = skill["name"]
    cat  = skill.get("category", "")
    sm   = summaries.get("skills", {}).get(name, skill.get("description", ""))

    # Keyword match: score based on overlap between task text and skill description/name
    # This is the PRIMARY signal — make it dominant
    sm_lower = sm.lower()
    text_kws = re.findall(r'[a-zA-Z]{3,}', text.lower())
    sm_words = set(re.findall(r'[a-zA-Z]{3,}', sm_lower))
    matched = sum(1 for kw in text_kws if kw in sm_words)
    # Each match adds 2.0; cap at 8 to prevent one skill flooding
    s += min(matched * 2.0, 8.0)

    # Category match: +2 if category matches task type keywords
    if cat in task_types:
        s += 2.0

    # Name match bonus: exact word match in name gets extra +3
    name_lower = name.lower()
    for kw in text_kws:
        if kw in name_lower:
            s += 3.0
            break

    return round(s, 1)

# ── LLM tiebreaker (only when borderline — max 1 call per turn) ────────────────
_LLM_USED = False

def llm_tiebreak(task_text: str, candidates: list[dict], summaries: dict, top_n: int = 8) -> dict[str, bool]:
    global _LLM_USED
    if _LLM_USED or not API_KEY:
        return {s["name"]: True for s in candidates[:3]}

    sm_map = summaries.get("skills", {})
    skill_lines = []
    for s in candidates[:top_n]:
        summ = sm_map.get(s["name"], s.get("description", ""))[:100]
        skill_lines.append("- " + s["name"] + " (" + s.get("category","?") + "): " + summ)

    skill_list = "\n".join(skill_lines)

    system_prompt = "You are a skill-routing assistant. Output valid JSON only — a dict of {\"skill-name\": true/false}."
    user_prompt = (
        "Task: " + task_text[:500] + "\n\n"
        "Candidate skills:\n" + skill_list + "\n\n"
        'Output JSON like: {"skill-name": true, "other": false}\n'
        "true = load it, false = skip. Be selective — only load if directly useful for this task."
    )

    try:
        payload = json.dumps({
            "model": LLM_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt}
            ],
            "max_tokens": 512,
            "temperature": 0.2
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

        # Strip markdown code fences
        if content.startswith("```"):
            parts = content.split("```")
            for p in parts[1::2]:  # odd indices are code block contents
                p = p.strip()
                if p.startswith("json"):
                    p = p[4:].strip()
                if p.startswith("{"):
                    content = p
                    break

        decision = json.loads(content)
        _LLM_USED = True
        return decision
    except Exception as e:
        print("[skill-selector LLM tiebreak failed: " + str(e) + "]", file=sys.stderr)
        return {s["name"]: True for s in candidates[:3]}

# ── Decide ────────────────────────────────────────────────────────────────────
def decide(skill: dict, score_val: float) -> tuple[str, str]:
    size = skill.get("size_mb", 0.0)
    if size > MB_ASK:
        return "ask", "[?] " + skill["name"] + " is ~" + str(int(size)) + "MB — load? [y/n]"
    if score_val >= 0.5:
        return "load", None
    return "skip", None

# ── Main ───────────────────────────────────────────────────────────────────────
def _load_env():
    """Load .env so API keys are available in cron contexts."""
    env_path = Path("/home/sc/.hermes/.env")
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k, v)

def main():
    _load_env()
    task_text = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("HERMES_TASK_TEXT", "")
    workspace = sys.argv[2] if len(sys.argv) > 2 else os.environ.get("HERMES_WORKSPACE", "")

    if not task_text:
        task_text = sys.stdin.read().strip()

    if not task_text and not workspace:
        sys.exit(0)

    metadata, ctx_scores, summaries = load_caches()
    if not metadata:
        sys.exit(0)

    task_types, stages = classify_task(task_text)
    sm_map = summaries.get("skills", {})

    # Phase 1: Score all skills
    scored = []
    for skill in metadata:
        s = score_by_summary(skill, task_types, stages, summaries, task_text)
        s += ctx_scores.get(skill["name"], 0.0)
        scored.append((round(s, 1), skill))

    scored.sort(key=lambda x: -x[0])

    # Phase 2: Rescore using fresh keyword-based scoring + light context weight
    # Context scores (pre-computed workspace affinity) would otherwise dominate.
    # Keyword match between task text and skill summary/name is the primary signal;
    # context score is a minor tiebreaker (max +1.5).
    scored = [
        (
            score_by_summary(skill, task_types, stages, summaries, task_text)
            + min(ctx_scores.get(skill["name"], 0.0) * 0.15, 1.5),
            skill,
        )
        for _, skill in scored
    ]
    scored.sort(key=lambda x: -x[0])

    # Phase 3: LLM tiebreaker only when borderline (top score < 5.0)
    top_candidates = [s for _, s in scored[:10] if s.get("is_local", False)]
    if top_candidates and scored[0][0] < 5.0 and API_KEY:
        llm_decision = llm_tiebreak(task_text, top_candidates, summaries)
        for i, (score_val, skill) in enumerate(scored):
            if skill["name"] in llm_decision and llm_decision[skill["name"]]:
                scored[i] = (score_val + 2.0, skill)
        scored.sort(key=lambda x: -x[0])

    # Phase 4: Apply decisions, cap at MAX_LOAD
    results = []
    for score_val, skill in scored:
        if len(results) >= MAX_LOAD:
            break
        action, msg = decide(skill, score_val)
        results.append((action, msg, skill, score_val))

    # Phase 5: Format output
    parts = []
    loaded = [(s, sv) for a, m, s, sv in results if a == "load"]
    asked  = [m      for a, m, s, sv in results if a == "ask"]

    if loaded:
        lines = []
        for skill, score_val in loaded:
            name = skill["name"]
            cat  = skill.get("category", "")
            summ = sm_map.get(name, skill.get("description", ""))[:80]
            lines.append(name + " [" + cat + "] - " + summ)
        parts.append("Auto-loaded:\n  " + "\n  ".join(lines))

    if asked:
        parts.append("\n".join(asked))

    if parts:
        print("\n".join(parts))

if __name__ == "__main__":
    main()