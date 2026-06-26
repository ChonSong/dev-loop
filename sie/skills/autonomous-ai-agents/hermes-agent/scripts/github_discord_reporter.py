#!/usr/bin/env python3
"""
GitHub Repo → Discord Reporter

Fetches repo stats, open PRs, recently merged PRs, open issues, and CI runs
from a GitHub repository and posts a formatted Discord embed.

Usage:
    python3 github_discord_reporter.py --repo HKUDS/ClawTeam --channel 1486920272547151922 --token $DISCORD_BOT_TOKEN

Requires:
    DISCORD_BOT_TOKEN env var (or --token flag)
    No external dependencies (uses stdlib only)

Notes on GitHub API:
    - Unauthenticated: 60 req/hr, works for public repos
    - Add GITHUB_TOKEN env var for 5000 req/hr
    - recently_merged uses per_page=100 + date filter client-side (GitHub API
      doesn't support merged-at date filtering directly)
"""

import urllib.request
import json
import argparse
from datetime import datetime, timezone
from typing import Any


def gh_get(url: str, token: str | None = None) -> list[dict]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "GitHub-Discord-Reporter/1.0",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def fetch_repo_stats(repo: str, token: str | None = None) -> dict:
    data = gh_get(f"https://api.github.com/repos/{repo}", token)
    return {
        "name": data["name"],
        "description": data.get("description") or "—",
        "stars": data["stargazers_count"],
        "forks": data["forks_count"],
        "url": data["html_url"],
    }


def fetch_open_prs(repo: str, token: str | None = None, limit: int = 20) -> list[dict]:
    prs = gh_get(f"https://api.github.com/repos/{repo}/pulls?state=open&per_page={limit}", token)
    return [
        {
            "number": p["number"],
            "title": p["title"],
            "author": p["user"]["login"],
            "created_at": p["created_at"][:10],
            "url": p["html_url"],
        }
        for p in prs
    ]


def fetch_recently_merged(repo: str, days: int = 7, token: str | None = None) -> list[dict]:
    cutoff = datetime.now(timezone.utc).timestamp() - (days * 86400)
    all_prs = gh_get(f"https://api.github.com/repos/{repo}/pulls?state=closed&per_page=100", token)
    merged = []
    for p in all_prs:
        if not p.get("merged_at"):
            continue
        merged_ts = datetime.fromisoformat(p["merged_at"][:19].replace("Z", "+00:00")).timestamp()
        if merged_ts >= cutoff:
            merged.append({
                "number": p["number"],
                "title": p["title"],
                "author": p["user"]["login"],
                "merged_at": p["merged_at"][:10],
                "url": p["html_url"],
            })
    return merged


def fetch_open_issues(repo: str, token: str | None = None) -> list[dict]:
    issues = gh_get(f"https://api.github.com/repos/{repo}/issues?state=open&per_page=50", token)
    return [
        {
            "number": i["number"],
            "title": i["title"],
            "author": i["user"]["login"],
            "created_at": i["created_at"][:10],
            "url": i["html_url"],
        }
        for i in issues if i.get("pull_request") is None  # exclude PRs
    ]


def fetch_ci_runs(repo: str, limit: int = 10, token: str | None = None) -> list[dict]:
    runs = gh_get(f"https://api.github.com/repos/{repo}/actions/runs?per_page={limit}", token)
    return [
        {
            "name": r["name"],
            "status": r["status"],
            "conclusion": r["conclusion"] or r["status"],
            "created_at": r["created_at"][:10],
            "url": r["html_url"],
            "branch": r["head_branch"],
        }
        for r in runs["workflow_runs"][:limit]
    ]


CI_ICON = {
    "success": "✅", "failure": "❌", "action_required": "⚠️",
    "cancelled": "🚫", "skipped": "⏭️", "in_progress": "⏳", "queued": "⏳",
}


def build_discord_embed(
    stats: dict,
    open_prs: list[dict],
    merged: list[dict],
    issues: list[dict],
    ci_runs: list[dict],
    channel_id: str,
    bot_token: str,
) -> dict:
    fields = []

    if open_prs:
        preview = open_prs[:5]
        lines = [f"[#{p['number']}]({p['url']}) **{p['title']}** — @{p['author']} ({p['created_at']})" for p in preview]
        if len(open_prs) > 5:
            lines.append(f"_...and {len(open_prs) - 5} more_")
        fields.append({"name": ":red_circle: Open PRs", "value": "\n".join(lines), "inline": False})

    if merged:
        lines = [f"[#{m['number']}]({m['url']}) **{m['title']}** — @{m['author']} (merged {m['merged_at']})" for m in merged]
        fields.append({"name": ":green_circle: Recently Merged (7 days)", "value": "\n".join(lines), "inline": False})

    if issues:
        lines = [f"[#{i['number']}]({i['url']}) **{i['title']}** — @{i['author']} ({i['created_at']})" for i in issues]
        fields.append({"name": ":clipboard: Open Issues", "value": "\n".join(lines), "inline": False})

    if ci_runs:
        lines = [
            f"{CI_ICON.get(r['conclusion'], '⚙️')} **{r['name']}** — `{r['conclusion']}` on `{r['branch']}` [{r['created_at']}]({r['url']})"
            for r in ci_runs
        ]
        fields.append({"name": ":gear: Recent CI Runs", "value": "\n".join(lines), "inline": False})

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    embed = {
        "title": f"{stats['name']} Daily Summary",
        "url": stats["url"],
        "color": 5814783,  # HKUDS green-ish
        "fields": fields,
        "footer": {"text": f"⭐ {stats['stars']}  |  🍴 {stats['forks']}  |  {today}"},
        "thumbnail": {"url": "https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png"},
    }
    return embed


def post_to_discord(channel_id: str, embed: dict, bot_token: str) -> dict:
    payload = json.dumps({"embeds": [embed]}).encode()
    req = urllib.request.Request(
        f"https://discord.com/api/v10/channels/{channel_id}/messages",
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bot {bot_token}",
            "Content-Type": "application/json",
            "User-Agent": "GitHub-Discord-Reporter/1.0",
        },
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def main():
    parser = argparse.ArgumentParser(description="Post GitHub repo summary to Discord")
    parser.add_argument("--repo", required=True, help="e.g. HKUDS/ClawTeam")
    parser.add_argument("--channel", required=True, help="Discord channel ID")
    parser.add_argument("--token", default=os.environ.get("DISCORD_BOT_TOKEN"), help="Discord bot token (or DISCORD_BOT_TOKEN env var)")
    parser.add_argument("--github-token", default=os.environ.get("GITHUB_TOKEN"), help="GitHub token (optional, for higher rate limits)")
    parser.add_argument("--days", type=int, default=7, help="Days for merged PRs (default: 7)")
    parser.add_argument("--pr-limit", type=int, default=20, help="Max open PRs (default: 20)")
    parser.add_argument("--ci-limit", type=int, default=10, help="Max CI runs (default: 10)")
    args = parser.parse_args()

    import os

    token = args.token or os.environ.get("DISCORD_BOT_TOKEN")
    if not token:
        raise SystemExit("DISCORD_BOT_TOKEN is required. Set env var or --token.")

    gh_token = args.github_token or os.environ.get("GITHUB_TOKEN")

    stats = fetch_repo_stats(args.repo, gh_token)
    open_prs = fetch_open_prs(args.repo, gh_token, args.pr_limit)
    merged = fetch_recently_merged(args.repo, args.days, gh_token)
    issues = fetch_open_issues(args.repo, gh_token)
    ci_runs = fetch_ci_runs(args.repo, args.ci_limit, gh_token)

    embed = build_discord_embed(stats, open_prs, merged, issues, ci_runs, args.channel, token)
    result = post_to_discord(args.channel, embed, token)
    print(f"Posted message ID: {result.get('id')}")


if __name__ == "__main__":
    import os
    main()
