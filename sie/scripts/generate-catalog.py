#!/usr/bin/env python3
"""Generate the repo catalog for seans-reporepo.

Usage: python3 generate-catalog.py /path/to/repo
"""
import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path


def gh(cmd: str) -> str:
    """Run a gh command via SSH and return stdout."""
    result = subprocess.run(
        f"gh {cmd}",
        shell=True,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        print(f"gh error: {result.stderr[:200]}", file=sys.stderr)
        return ""
    return result.stdout


def extract_tags(desc: str, readme: str = "") -> list:
    """Extract utility tags from description and README text."""
    text = (desc or "") + " " + (readme or "")
    tags = set()
    keyword_map = {
        "dashboard": "dashboard",
        "agent": "agent",
        "ai": "ai",
        "llm": "llm",
        "cli": "cli",
        "web": "web-app",
        "api": "api",
        "bot": "bot",
        "monitor": "monitoring",
        "backup": "backup",
        "sync": "sync",
        "docker": "docker",
        "infrastructure": "infrastructure",
        "transmut": "transpilation",
        "circuit breaker": "reliability",
        "energy": "energy",
        "carbon": "sustainability",
        "benchmark": "benchmarking",
        "poker": "gaming",
        "starcraft": "gaming",
        "dotfiles": "dotfiles",
        "landing": "website",
        "mobile": "mobile",
        "voice": "voice",
        "audio": "audio",
        "video": "video",
        "terminal": "terminal",
        "tui": "tui",
        "game": "gaming",
        "sol": "solver",
        "code-server": "remote-dev",
        "ide": "ide",
        "openclaw": "openclaw",
        "nanobot": "agent",
        "hermes": "hermes-agent",
        "aie": "aie",
        "harness": "harness",
        "orchestrat": "orchestration",
        "react": "react",
        "express": "express",
        "postgresql": "database",
        "go": "go",
        "python": "python",
        "typescript": "typescript",
        "rust": "rust",
        "nginx": "nginx",
        "proxy": "proxy",
        "telemetry": "telemetry",
        "logging": "logging",
        "analytics": "analytics",
        "mcp": "mcp",
        "plugin": "plugin",
        "framework": "framework",
        "testing": "testing",
        "automation": "automation",
        "repomix": "code-packing",
        "gitingest": "code-ingestion",
        "openhands": "coding-agent",
        "opencode": "coding-agent",
        "comfyui": "image-gen",
        "stable": "image-gen",
        "langfuse": "observability",
        "opik": "observability",
        "milvus": "vector-db",
        "txtai": "vector-search",
        "temporal": "workflow-engine",
        "dokku": "paas",
        "headscale": "vpn",
        "wireguard": "vpn",
        "netdata": "monitoring",
        "swag": "reverse-proxy",
        "open-webui": "chat-ui",
        "karpathy": "research",
        "deepresearch": "research",
        "autoresearch": "research",
        "awesome": "awesome-list",
        "list": "awesome-list",
        "agent-browser": "browser-automation",
        "browser": "browser-automation",
        "vector": "vector-db",
        "embedding": "embeddings",
        "fine-tun": "fine-tuning",
        "training": "training",
        "rag": "rag",
        "retrieval": "rag",
        "multi-agent": "multi-agent",
        "team": "multi-agent",
    }
    for kw, tag in keyword_map.items():
        if kw.lower() in text.lower():
            tags.add(tag)
    return sorted(tags)


def detect_type(desc: str, fork: bool, readme: str = "") -> str:
    desc_lower = (desc or "").lower()
    readme_lower = (readme or "").lower()
    combined = desc_lower + " " + readme_lower

    if "monorepo" in combined or "dashboard" in combined:
        return "monorepo"
    if "framework" in combined or "library" in combined:
        return "library"
    if "awesome" in combined or "list of" in combined:
        return "awesome-list"
    if "agent" in combined or "bot" in combined or "assistant" in combined:
        return "agent"
    if "cli" in combined or "command line" in combined:
        return "cli"
    if "web app" in combined or "web-based" in combined:
        return "webapp"
    if "docker" in combined or "infrastructure" in combined or "server" in combined:
        return "infrastructure"
    if "backup" in combined or "sync" in combined:
        return "utility"
    if fork:
        return "fork"
    return "unknown"


def detect_status(desc: str, archived: bool, fork: bool, has_readme: bool) -> str:
    desc_lower = (desc or "").lower()
    if archived:
        return "archived"
    if "scaffolded" in desc_lower or "awaiting" in desc_lower:
        return "scaffolded"
    if "suspended" in desc_lower:
        return "suspended"
    if fork and not has_readme:
        return "fork"
    return "active"


def format_frontmatter(data: dict) -> str:
    """Format YAML frontmatter manually to avoid PyYAML dependency."""
    lines = ["---"]
    for key, value in data.items():
        if isinstance(value, list):
            if not value:
                lines.append(f"{key}: []")
            else:
                lines.append(f"{key}:")
                for item in value:
                    lines.append(f"  - {item}")
        elif isinstance(value, bool):
            lines.append(f"{key}: {str(value).lower()}")
        else:
            # Quote strings with special characters
            s = str(value) if value is not None else ""
            if any(c in s for c in [":", "#", "{", "}", "[", "]", ",", "&", "*", "?", "|", "-", "<", ">", "=", "!", "%", "@", "`"]):
                s = f"'{s}'"
            elif s == "":
                s = '""'
            lines.append(f"{key}: {s}")
    lines.append("---")
    return "\n".join(lines)


def generate_repo_markdown(entry: dict, readme_text: str = "") -> str:
    """Generate markdown file content for a repo."""
    fm_data = {
        "repo": entry["name"],
        "url": entry["url"],
        "description": entry["description"],
        "type": entry["type"],
        "status": entry["status"],
        "language": entry.get("language", "other"),
        "size_kb": entry["size_kb"],
        "stars": entry.get("stars", 0),
        "last_pushed": entry.get("last_pushed", ""),
        "license": entry.get("license", "unknown"),
        "tags": entry.get("tags", []),
    }
    if entry.get("fork_of"):
        fm_data["fork_of"] = entry["fork_of"]

    content = format_frontmatter(fm_data)
    content += f"\n\n# {entry['name'].split('/')[-1]}\n\n"
    content += f"> {entry['description']}\n\n"
    content += f"**URL:** [{entry['name']}]({entry['url']})\n"
    if entry.get("fork_of"):
        content += f"**Fork of:** [{entry['fork_of']}](https://github.com/{entry['fork_of']})\n"

    content += f"\n## Metadata\n\n"
    content += f"- **Type:** {entry['type']}\n"
    content += f"- **Status:** {entry['status']}\n"
    content += f"- **Language:** {entry.get('language', 'N/A')}\n"
    content += f"- **Size:** {entry['size_kb']:,} KB\n"
    if not entry.get("fork_of"):
        content += f"- **Stars:** {entry.get('stars', 0):,}\n"
    content += f"- **Last Pushed:** {entry.get('last_pushed', 'N/A')}\n"
    content += f"- **License:** {entry.get('license', 'unknown')}\n"
    if entry.get("tags"):
        content += f"- **Tags:** {', '.join(entry['tags'])}\n"

    if readme_text:
        content += f"\n## README Excerpt\n\n{readme_text[:2000]}...\n"

    return content


def generate_readme(owned: list, starred: list) -> str:
    """Generate the main README.md."""
    total_kb = sum(e.get("size_kb", 0) for e in owned + starred)

    # Build tag index
    tag_index = {}
    for e in owned + starred:
        for tag in e.get("tags", []):
            if tag not in tag_index:
                tag_index[tag] = {"owned": [], "starred": []}
            bucket = "owned" if e["name"].startswith("ChonSong/") else "starred"
            tag_index[tag][bucket].append(e["name"])

    # Language stats
    lang_stats = {}
    for e in owned + starred:
        lang = e.get("language", "other")
        if lang not in lang_stats:
            lang_stats[lang] = {"count": 0, "total_kb": 0}
        lang_stats[lang]["count"] += 1
        lang_stats[lang]["total_kb"] += e.get("size_kb", 0)

    readme = textwrap.dedent(f"""\
    # sean's-reporepo

    > Personal code catalog — owned and starred repositories indexed for ideation, discovery, and combinatorial application design.

    ## Quick Stats

    | | Owned | Starred | Total |
    |---|---|---|---|
    | Repos | {len(owned)} | {len(starred)} | {len(owned) + len(starred)} |
    | Total Size | {sum(e.get('size_kb', 0) for e in owned):,} KB | {sum(e.get('size_kb', 0) for e in starred):,} KB | {total_kb:,} KB ({total_kb//1024:,} MB) |
    | Languages | {len(set(e.get('language') for e in owned))} | {len(set(e.get('language') for e in starred))} | {len(set(e.get('language') for e in owned + starred))} |
    | Tags | — | — | {len(tag_index)} |

    ## Structure

    ```
    ├── owned/           # My repositories ({len(owned)})
    │   ├── agent-os.md
    │   ├── repo-transmute.md
    │   └── ...
    ├── starred/         # Repos I've starred ({len(starred)})
    │   ├── yamadashy_repomix.md
    │   ├── e2b-dev_awesome-ai-agents.md
    │   └── ...
    ├── scripts/         # Utility scripts for catalog management
    └── README.md        # This file
    ```

    ## Owned Repositories

    """)

    # Group owned by type
    type_groups = {}
    for e in owned:
        t = e.get("type", "unknown")
        if t not in type_groups:
            type_groups[t] = []
        type_groups[t].append(e)

    for t in sorted(type_groups.keys()):
        repos = type_groups[t]
        readme += f"### {t.replace('-', ' ').title()} ({len(repos)})\n\n"
        readme += "| Repo | Language | Size | Stars | Tags |\n"
        readme += "|---|---|---|---|---|\n"
        for e in sorted(repos, key=lambda x: x.get("size_kb", 0), reverse=True):
            tags = ", ".join(e.get("tags", [])[:3])
            link = f"[{e['short_name']}](owned/{e['name'].replace('/', '_')}.md)"
            readme += f"| {link} | {e.get('language', '-')} | {e.get('size_kb', 0):,} KB | {e.get('stars', 0):,} | {tags} |\n"
        readme += "\n"

    # Top starred
    top_starred = sorted(starred, key=lambda x: x.get("stars", 0), reverse=True)[:20]
    readme += "## Starred Repositories (Top 20 by Stars)\n\n"
    readme += "| Repo | Type | Language | Stars | Tags |\n"
    readme += "|---|---|---|---|---|\n"
    for e in top_starred:
        tags = ", ".join(e.get("tags", [])[:3])
        link = f"[{e['short_name']}](starred/{e['name'].replace('/', '_')}.md)"
        readme += f"| {link} | {e.get('type', '-')} | {e.get('language', '-')} | {e.get('stars', 0):,} | {tags} |\n"
    readme += f"\n*...and {len(starred) - 20} more in `starred/`*\n\n"

    # Tag index
    readme += "## Tag Index\n\n"
    readme += "| Tag | Count | Repos |\n"
    readme += "|---|---|---|\n"
    for tag in sorted(tag_index.keys()):
        info = tag_index[tag]
        total = len(info["owned"]) + len(info["starred"])
        sample = (info["owned"] + info["starred"])[:3]
        sample_str = ", ".join(s.split("/")[-1] for s in sample)
        if total > 3:
            sample_str += f" +{total-3} more"
        readme += f"| `{tag}` | {total} | {sample_str} |\n"

    # Language breakdown
    readme += "\n## Language Breakdown\n\n"
    readme += "| Language | Count | Total Size |\n"
    readme += "|---|---|---|\n"
    for lang in sorted(lang_stats.keys(), key=lambda x: lang_stats[x]["count"], reverse=True):
        info = lang_stats[lang]
        readme += f"| {lang} | {info['count']} | {info['total_kb']:,} KB |\n"

    # Combinatorial potential
    readme += "\n## Combinatorial Potential\n\n"
    readme += "Repos that share tags are candidates for combination:\n\n"
    combo_tags = {k: v for k, v in tag_index.items() if v["owned"] and v["starred"]}
    for tag in sorted(combo_tags.keys())[:15]:
        info = combo_tags[tag]
        owned_names = [n.split("/")[-1] for n in info["owned"][:3]]
        starred_names = [n.split("/")[-1] for n in info["starred"][:3]]
        readme += f"### `{tag}`\n"
        readme += f"- Owned: {', '.join(owned_names)}\n"
        readme += f"- Starred: {', '.join(starred_names)}\n\n"

    return readme


def safe_name(name: str) -> str:
    return name.replace("/", "_").replace(" ", "-")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 generate-catalog.py <repo-dir>")
        sys.exit(1)

    repo_dir = Path(sys.argv[1])
    print(f"Generating catalog in {repo_dir}")

    # Create directories
    (repo_dir / "owned").mkdir(exist_ok=True)
    (repo_dir / "starred").mkdir(exist_ok=True)

    # Fetch owned repos
    print("Fetching owned repos...")
    owned_json = gh(
        'repo list ChonSong --limit 100 --json nameWithOwner,description,primaryLanguage,stargazerCount,forkCount,diskUsage,pushedAt,isFork,parent,licenseInfo,repositoryTopics'
    )
    if not owned_json:
        print("ERROR: Could not fetch owned repos")
        sys.exit(1)

    owned_data = json.loads(owned_json)
    print(f"  Found {len(owned_data)} owned repos")

    # Fetch starred repos
    print("Fetching starred repos...")
    starred_raw = gh("api user/starred --paginate")
    if not starred_raw:
        print("ERROR: Could not fetch starred repos")
        sys.exit(1)

    starred_raw_data = json.loads(starred_raw)
    # Filter: skip forks whose parent is already in owned
    owned_names = set(r["nameWithOwner"] for r in owned_data)
    starred_filtered = []
    for r in starred_raw_data:
        parent = r.get("parent", {}).get("full_name", "") if r.get("parent") else ""
        if parent not in owned_names:
            starred_filtered.append(r)

    print(f"  Found {len(starred_filtered)} starred repos (after filtering)")

    # Process owned
    owned_entries = []
    for r in owned_data:
        name = r["nameWithOwner"]
        desc = r.get("description") or ""
        lang = r.get("primaryLanguage", {}).get("name") if r.get("primaryLanguage") else None
        size = r.get("diskUsage", 0)
        stars = r.get("stargazerCount", 0)
        pushed = (r.get("pushedAt") or "")[:10]
        fork = r.get("isFork", False)
        parent = r.get("parent", {}).get("nameWithOwner", "") if r.get("parent") else ""
        license_info = r.get("licenseInfo", {}).get("spdxId") if r.get("licenseInfo") else None
        topics = [t["name"] for t in (r.get("repositoryTopics") or [])]

        # Try to get README
        readme_text = ""
        try:
            readme_out = gh(f'api "repos/{name}/readme" --jq ".content"')
            if readme_out:
                import base64
                readme_text = base64.b64decode(readme_out.strip()).decode("utf-8", errors="ignore")[:3000]
        except Exception:
            pass

        tags = extract_tags(desc, readme_text)
        type_ = detect_type(desc, fork, readme_text)
        status = detect_status(desc, False, fork, bool(readme_text))

        entry = {
            "name": name,
            "short_name": name.split("/")[-1],
            "url": f"https://github.com/{name}",
            "description": desc or "No description",
            "type": type_,
            "status": status,
            "language": lang or "other",
            "size_kb": size,
            "stars": stars,
            "last_pushed": pushed,
            "license": license_info or "unknown",
            "tags": tags,
            "fork_of": parent if fork else None,
            "topics": topics,
        }

        md_content = generate_repo_markdown(entry, readme_text[:2000] if readme_text else "")
        fn = safe_name(name)
        (repo_dir / "owned" / f"{fn}.md").write_text(md_content)
        owned_entries.append(entry)

    print(f"  Created {len(owned_entries)} owned files")

    # Process starred
    starred_entries = []
    for r in starred_filtered:
        name = r["full_name"]
        desc = r.get("description") or ""
        lang = r.get("language") or "other"
        size = r.get("size", 0)
        stars = r.get("stargazers_count", 0)
        pushed = (r.get("pushed_at") or "")[:10]
        fork = r.get("is_fork", False)
        parent = r.get("parent", {}).get("full_name", "") if r.get("parent") else ""
        license_info = r.get("license", {}).get("spdx_id") if r.get("license") else None
        topics = r.get("topics", [])
        archived = r.get("archived", False)

        tags = extract_tags(desc)
        # Add tags from API topics
        for t in topics:
            t_lower = t.lower()
            tag_map = {
                "ai": "ai", "llm": "llm", "machine-learning": "ai", "agent": "agent",
                "autonomous-agent": "agent", "docker": "docker", "container": "docker",
                "typescript": "typescript", "javascript": "javascript", "react": "react",
                "go": "go", "golang": "go", "python": "python", "rust": "rust",
            }
            if t_lower in tag_map and tag_map[t_lower] not in tags:
                tags.append(tag_map[t_lower])
        tags = sorted(set(tags))

        type_ = detect_type(desc, fork)
        status = "archived" if archived else "active"

        entry = {
            "name": name,
            "short_name": name.split("/")[-1],
            "url": f"https://github.com/{name}",
            "description": desc or "No description",
            "type": type_,
            "status": status,
            "language": lang,
            "size_kb": size,
            "stars": stars,
            "last_pushed": pushed,
            "license": license_info or "unknown",
            "tags": tags,
            "fork_of": parent if fork else None,
        }

        md_content = generate_repo_markdown(entry)
        fn = safe_name(name)
        (repo_dir / "starred" / f"{fn}.md").write_text(md_content)
        starred_entries.append(entry)

    print(f"  Created {len(starred_entries)} starred files")

    # Generate README
    readme = generate_readme(owned_entries, starred_entries)
    (repo_dir / "README.md").write_text(readme)
    print("  Generated README.md")

    # Remove stale files
    for d in ["owned", "starred"]:
        expected_names = {safe_name(e["name"]) + ".md" for e in (owned_entries if d == "owned" else starred_entries)}
        for f in (repo_dir / d).glob("*.md"):
            if f.name not in expected_names:
                f.unlink()
                print(f"  Removed stale: {d}/{f.name}")

    print("Catalog generation complete.")


if __name__ == "__main__":
    main()
