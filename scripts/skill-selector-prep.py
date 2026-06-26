#!/usr/bin/env python3
"""
skill-selector-prep.py — Daily skills cache builder.
Reads all local SKILL.md files from ~/.hermes/skills/ (2726 files),
syncs remote README-style skill repos via git clone/pull,
computes context scores against active workspace keywords,
writes cache to ~/.hermes/skill-selector-cache/.
"""

import json, subprocess, re, time
from pathlib import Path
from datetime import datetime, timezone

# ── Paths ──────────────────────────────────────────────────────────────────────
HERMES_HOME    = Path.home() / ".hermes"
CACHE_DIR      = HERMES_HOME / "skill-selector-cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Actual local skills directory
HERMES_SKILLS  = HERMES_HOME / "skills"

# Workspace contexts for scoring
WORKSPACE_CONTEXTS = {
    "hermes-web-computer": {
        "path": str(HERMES_HOME / ".." / "repos" / "hermes-web-computer"),
        "keywords": ["go", "svelte", "tile", "component", "backend", "docker",
                     "hermes-computer", "dock", "panel", "layout", "waybar",
                     "shell", "x11", "xpra", "hermes-ui", "wasm"],
        "weight": 1.5,
    },
    "agent-os": {
        "path": str(HERMES_HOME / ".." / "repos" / "agent-os"),
        "keywords": ["node", "react", "express", "postgres", "api", "docker",
                     "agent", "page", "spa"],
        "weight": 1.2,
    },
    "seans-reporepo": {
        "path": str(HERMES_HOME / ".." / "repos" / "seans-reporepo"),
        "keywords": ["repo", "catalog", "star", "github", "readme",
                     "combinatorial"],
        "weight": 1.0,
    },
    "repo-transmute-v2": {
        "path": str(HERMES_HOME / ".." / "repos" / "repo-transmute-v2"),
        "keywords": ["migrate", "ast", "component", "vision", "llm",
                     "screenshot", "transpile", "react", "svelte", "extract"],
        "weight": 1.3,
    },
}

# Remote README-style skill repos — cloned directly since we're on the host
REMOTE_REPOS = [
    ("0xNyk",             "awesome-hermes-agent",  "0xNyk"),
    ("Awesome-Agent-Skills","awesome-agent-skills",  "Awesome-Agent-Skills"),
    ("mattpocock",        "mattpocock-skills",     "Matt Pocock"),
    ("expo",              "expo-skills",           "Expo"),
    ("TactionAI",         "vercel-labs-skills",    "Vercel Labs"),
    # indranilbanerjee skipped — GH host-key not auto-added yet
]

TMP_DIR = Path("/tmp/skill-selector-swarm")
TMP_DIR.mkdir(exist_ok=True)

# ── Helpers ────────────────────────────────────────────────────────────────

def run(cmd, **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True,
                          timeout=kw.pop("timeout", 60), **kw)


# ── Direct git sync (no SSH needed — we're on the host) ──────────────────

def sync_remote_direct(org: str, name: str) -> bool:
    """Clone (one-time) or pull (update) the remote skill repo directly."""
    dest = TMP_DIR / name
    repo_url = f"https://github.com/{org}/{name}.git"

    print(f"  Syncing {org}/{name}...")

    if dest.exists():
        r = run(["git", "-C", str(dest), "pull", "--ff-only"], timeout=60)
        if r.returncode != 0:
            print(f"    pull failed: {r.stderr[:150].strip()}")
            return False
        r_sha = run(["git", "-C", str(dest), "log", "-1", "--format=%H"], timeout=10)
        print(f"    Pulled (sha={r_sha.stdout.strip()[:8]})")
    else:
        r = run(["git", "clone", "--depth", "1", repo_url, str(dest)], timeout=90)
        if r.returncode != 0:
            print(f"    clone failed: {r.stderr[:150].strip()}")
            return False
        print(f"    Cloned {org}/{name}")

    return True


# ── README parser ──────────────────────────────────────────────────────────

def extract_readme_skills(src_dir: Path) -> list[dict]:
    """
    Parse README.md files for skill list entries.
    VoltAgent/Awesome format: - **[name](url)** — description
    Awesome format: - [name](url) — description
    """
    readme = src_dir / "README.md"
    if not readme.exists():
        return []

    text    = readme.read_text(errors="ignore")
    skills  = []
    seen    = set()
    lines  = text.split("\n")

    # Try VoltAgent format first
    for line in lines:
        line = line.strip()
        if not line.startswith("-"):
            continue
        # - **[name](url)** — description  OR  - [name](url) — description
        m = re.search(r'\[([^\]]+)\]\([^\)]+\)', line)
        if not m:
            continue
        name = m.group(1).strip()
        # Strip maturity badges: **[beta]** [name](url)
        name = re.sub(r'\*\*\[[^\]]+\]\([^\)]+\)\s*', "", name).strip()
        if not name or name in seen:
            continue
        seen.add(name)

        # Description after " — " or " - "
        desc = ""
        for delim in (" — ", " - ", " —", " - "):
            if delim in line:
                parts = line.split(delim, 1)
                desc = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1',
                              parts[1].strip())[:280]
                break

        # Guess tags from name/org heuristics
        tags = []
        if any(x in name.lower() for x in ["gemini", "openai", "claude", "gpt"]):
            tags.append("llm")
        if any(x in name.lower() for x in ["web", "frontend", "react", "svelte"]):
            tags.append("frontend")
        if any(x in name.lower() for x in ["docker", "ci", "deploy", "cloud"]):
            tags.append("devops")
        if any(x in name.lower() for x in ["api", "rest", "http"]):
            tags.append("api")

        skills.append({
            "name":        name,
            "description": desc,
            "tags":       tags,
            "source":     src_dir.name,
            "is_local":   False,
        })

# 4. Walk plugin-dir structure (expo, awesome-agent-skills) and import all SKILL.md
    for pattern in ["plugins/*/skills/*/SKILL.md", "plugins/*/skills/*/*/SKILL.md"]:
        for sk in src_dir.glob(pattern):
            sub = sk.parent
            try:
                content = sk.read_text(errors="ignore")
                frontmatter, body = {}, ""
                if content.startswith("---"):
                    end = content.find("---", 3)
                    if end > 0:
                        for fl in content[3:end].strip().split("\n"):
                            if ":" in fl:
                                k, v = fl.split(":", 1)
                                frontmatter[k.strip()] = v.strip().strip('"').strip("'")
                        body = content[end+3:].strip()
                    else:
                        body = content
                else:
                    body = content
                sname = frontmatter.get("name", sub.name.replace("-"," ").replace("_"," ").title())
                desc  = frontmatter.get("description", body[:200].strip())
                tags_str = frontmatter.get("tags", "")
                tags = [t.strip().strip("'\"") for t in tags_str.strip("[]").split(",") if t.strip()] if tags_str else []
                skills.append({
                    "name":        sname,
                    "description": desc[:280],
                    "tags":       tags,
                    "source":     src_dir.name + "/plugins",
                    "is_local":   False,
                })
            except Exception:
                pass

    return skills


# ── Local skills loader ─────────────────────────────────────────────────────

def load_local_skills() -> list[dict]:
    """Walk HERMES_SKILLS and load name/description/tags from every SKILL.md."""
    skills  = []
    result  = run(["find", "-L", str(HERMES_SKILLS), "-name", "SKILL.md", "-type", "f"])
    if result.returncode != 0:
        print(f"  find failed: {result.stderr}")
        return skills

    for skill_md in result.stdout.strip().split("\n"):
        if not skill_md:
            continue
        p = Path(skill_md)
        try:
            content = p.read_text(errors="ignore")
        except Exception:
            continue

        rel  = p.parent.relative_to(HERMES_SKILLS)
        parts = rel.parts
        name  = "-".join(parts).lower().replace(" ", "-").replace("_", "-")

        frontmatter = {}
        body        = ""
        if content.startswith("---"):
            end = content.find("---", 3)
            if end > 0:
                for fl in content[3:end].strip().split("\n"):
                    if ":" in fl:
                        k, v = fl.split(":", 1)
                        frontmatter[k.strip()] = v.strip().strip('"').strip("'")
                body = content[end+3:].strip()
            else:
                body = content
        else:
            body = content

        tags_str = frontmatter.get("tags", "")
        tags = [t.strip().strip("'\"" ) for t in tags_str.strip("[]").split(",") if t.strip()] if tags_str else []
        desc = frontmatter.get("description", "")[:300]
        if not desc and body:
            for bline in body.split("\n")[:20]:
                bline = bline.strip()
                if bline and not bline.startswith("#") and len(bline) > 20:
                    desc = bline[:300]
                    break

        skills.append({
            "name":        name,
            "path":        str(p.parent),
            "description": desc,
            "tags":       tags,
            "size_mb":    0.0,
            "is_local":   True,
            "source":     "hermes-agent",
        })

    return skills


# ── Context scoring ────────────────────────────────────────────────────────

def compute_context_scores(skills: list[dict]) -> dict[str, float]:
    scores = {}
    for skill in skills:
        score  = 0.0
        s_text = f"{skill['name']} {skill.get('description','')} {' '.join(skill.get('tags',[]))}".lower()
        for ws_name, ctx in WORKSPACE_CONTEXTS.items():
            matches = sum(1 for kw in ctx["keywords"] if kw in s_text)
            if matches:
                score += matches * ctx["weight"]
        scores[skill["name"]] = round(score, 3)
    return scores


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    t0  = time.time()
    now = datetime.now(timezone.utc)

    print(f"[skill-selector-prep] {now.isoformat()}")
    local_count = run(["find", "-L", str(HERMES_SKILLS), "-name", "SKILL.md", "-type", "f"]).stdout.count("\n")
    print(f"  hermes skills: {HERMES_SKILLS} ({local_count} SKILL.md files)")

    all_skills = []
    changed   = []

    # 1. Sync remote repos directly (we're on the host)
    for org, name, _ in REMOTE_REPOS:
        ok = sync_remote_direct(org, name)
        if ok:
            src_dir = TMP_DIR / name
            rem_skills = extract_readme_skills(src_dir)
            print(f"    {name}: {len(rem_skills)} skills from README")
            all_skills.extend(rem_skills)
            changed.append(name)

    # 2. Load local hermes-agent skills
    local_skills = load_local_skills()
    local_names  = {s["name"] for s in local_skills}
    print(f"  Local: {len(local_skills)} hermes-agent skills")

    # 3. Merge (local authoritative; remote fills gaps)
    merged = list(local_skills)
    total_new = 0
    for rs in all_skills:
        if rs["name"] not in local_names:
            merged.append(rs)
            total_new += 1

    print(f"  Total merged: {len(merged)} ({len(local_skills)} local + {total_new} remote)")

    # 4. Context scores
    context_scores = compute_context_scores(merged)
    print(f"  Context scores: {len(context_scores)} computed")

    # 5. Write cache
    metadata = [{
        "name":        s["name"],
        "path":        s.get("path", ""),
        "description": s.get("description", ""),
        "tags":       s.get("tags", []),
        "size_mb":    s.get("size_mb", 0.0),
        "is_local":   s.get("is_local", False),
        "source":     s.get("source", "unknown"),
    } for s in merged]

    with open(CACHE_DIR / "skill_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    with open(CACHE_DIR / "context_scores.json", "w") as f:
        json.dump(context_scores, f, indent=2)
    with open(CACHE_DIR / "last_refresh.txt", "w") as f:
        f.write(now.isoformat() + "\n")

    # ── Summary ──────────────────────────────────────────────────────────
    elapsed = time.time() - t0
    total_local  = sum(1 for s in metadata if s.get("is_local"))
    total_remote = len(metadata) - total_local
    top5        = sorted(context_scores.items(), key=lambda x: -x[1])[:5]
    updated_str = f"Updated: {', '.join(changed)}" if changed else "No repo changes detected"

    print(f"\nDone in {elapsed:.1f}s — {len(metadata)} skills ({total_local} local, {total_remote} remote)")
    print(f"  {updated_str}")
    if top5:
        print(f"  Top workspace matches: {[(n, f'{s:.1f}') for n, s in top5]}")
    print(f"  Cache → {CACHE_DIR}")

    # Verify cache
    verify = json.load(open(CACHE_DIR / "skill_metadata.json"))
    print(f"  [VERIFY] metadata.json: {len(verify)} records, {(sum(1 for v in verify if v.get('is_local')), sum(1 for v in verify if not v.get('is_local')))}")

if __name__ == "__main__":
    main()
