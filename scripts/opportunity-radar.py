#!/usr/bin/env python3
"""
Opportunity Radar — Grand SIE Phase 1.

Weekly scan of the external world for signals worth acting on.
Outputs a Strategic Brief delivered to Discord or stdout.

Usage:
    python3 opportunity-radar.py                     # Run all scans, output brief
    python3 opportunity-radar.py --sources github     # Single source
    python3 opportunity-radar.py --dry-run            # Print brief to stdout
    python3 opportunity-radar.py --deliver discord    # Deliver to Discord (default)

Sources:
    - GitHub trending (per-domain: poker, 3DCP, AI agents, game dev)
    - arXiv papers (keyword-filtered)
    - Competitor activity (defined in CONFIG)
    - Hacker News / product launches

Exit codes:
    0 — brief produced (Discord notified)
    1 — no actionable signals (silent exit for cron)
    2 — error
"""

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

try:
    import requests
except ImportError:
    requests = None  # optional — only needed for Discord delivery


# ── Configuration ──────────────────────────────────────────────────────

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")
DISCORD_CHANNEL_ID = os.environ.get("DISCORD_CHANNEL_ID", "")

CONFIG = {
    "domains": {
        "poker": {
            "keywords": [
                "GTO", "solver", "poker", "pio solver",
                "monker", "poker strategy", "range training",
            ],
            "github_topics": ["poker", "gto-solver"],
            "arxiv_categories": ["cs.GT", "cs.AI"],
            "competitors": [
                "piosolver", "monker", "simplepoker", "luyten",
            ],
            "weight": 1.0,
        },
        "3dcp": {
            "keywords": [
                "3D concrete printing", "additive manufacturing",
                "contour crafting", "construction 3D printing",
            ],
            "github_topics": ["3d-printing", "concrete"],
            "arxiv_categories": ["cs.CE", "cs.RO", "cond-mat.mtrl-sci"],
            "competitors": ["ICON", "COBOD", "Apis Cor", "CyBe"],
            "weight": 0.8,
        },
        "ai-agents": {
            "keywords": [
                "autonomous agent", "LLM agent", "code generation",
                "agentic coding", "SWE-bench", "agent framework",
            ],
            "github_topics": ["ai-agent", "llm-agent", "autonomous-coding"],
            "arxiv_categories": ["cs.SE", "cs.AI", "cs.MA"],
            "competitors": [],
            "weight": 1.0,
        },
        "game-dev": {
            "keywords": [
                "web game", "canvas game", "react game",
                "photon", "hex map", "procedural generation",
            ],
            "github_topics": ["game-development", "web-game"],
            "arxiv_categories": [],
            "competitors": [],
            "weight": 0.6,
        },
    },
    "filters": {
        "min_combined_score": 7,
        "max_signals_per_source": 5,
        "max_total_signals": 20,
    },
}


# ── Data Model ─────────────────────────────────────────────────────────

@dataclass
class Signal:
    title: str
    url: str
    description: str
    source: str
    domain: str
    relevance: int
    novelty: int
    actionability: int
    recommendation: str
    rationale: str = ""
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @property
    def combined_score(self) -> int:
        return self.relevance + self.novelty + self.actionability


@dataclass
class StrategicBrief:
    date: str
    signals: list[Signal]
    recommendation: str = ""
    project_health: dict = field(default_factory=dict)

    def to_markdown(self) -> str:
        lines = [f"# Strategic Brief — {self.date}", ""]
        build = [s for s in self.signals if s.recommendation == "BUILD"]
        watch = [s for s in self.signals if s.recommendation == "WATCH"]
        skip = [s for s in self.signals if s.recommendation == "SKIP"]

        if build:
            lines.append("### :green_circle: Worth Building")
            for s in build:
                lines.append(
                    f"- [**{s.title}**]({s.url}) — {s.domain.upper()}  "
                    f"[R:{s.relevance} N:{s.novelty} A:{s.actionability}]"
                )
                if s.rationale:
                    lines.append(f"  _{s.rationale}_")
            lines.append("")

        if watch:
            lines.append("### :yellow_circle: Worth Watching")
            for s in watch:
                lines.append(f"- [**{s.title}**]({s.url}) — {s.domain.upper()}")
                if s.rationale:
                    lines.append(f"  _{s.rationale}_")
            lines.append("")

        if skip:
            lines.append("### :red_circle: Skip / Out of Scope")
            for s in skip:
                lines.append(f"- [{s.title}]({s.url}) — {s.rationale}")
            lines.append("")

        if self.recommendation:
            lines.append("## Recommendation")
            lines.append(self.recommendation)
            lines.append("")

        if self.project_health:
            lines.append("## Project Health")
            for name, status in self.project_health.items():
                lines.append(f"- {name}: {status}")
            lines.append("")

        return "\n".join(lines)

    def to_discord(self) -> str:
        """Compact single-message format for Discord."""
        lines = [f"## Strategic Brief — {self.date}", ""]
        build = [s for s in self.signals if s.recommendation == "BUILD"]
        watch = [s for s in self.signals if s.recommendation == "WATCH"]
        skip = [s for s in self.signals if s.recommendation == "SKIP"]

        if build:
            lines.append("**Worth Building**")
            for s in build:
                score = s.combined_score
                lines.append(
                    f"• [{s.title}]({s.url}) [{s.domain}] "
                    f"score:{score}/15"
                )
                if s.rationale:
                    lines.append(f"  └ {s.rationale}")
            lines.append("")

        if watch:
            lines.append("**Worth Watching**")
            for s in watch[:3]:  # cap at 3 for Discord message length
                lines.append(f"• [{s.title}]({s.url}) [{s.domain}]")
            if len(watch) > 3:
                lines.append(f"  _...and {len(watch) - 3} more_")
            lines.append("")

        if skip:
            lines.append("**Skipped**")
            for s in skip[:2]:
                lines.append(f"• ~~{s.title}~~ — {s.rationale}")
            lines.append("")

        if self.recommendation:
            lines.append(f"**Recommendation:** {self.recommendation}")

        return "\n".join(lines)


# ── Scanners ────────────────────────────────────────────────────────────

def _gh_search(query: list[str], sort: str = "stars",
               limit: int = 5) -> list[dict]:
    try:
        result = subprocess.run(
            [
                "gh", "search", "repos",
                "--sort", sort,
                "--limit", str(limit),
                "--json", "name,url,description,updatedAt,forksCount",
            ] + query,
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            return []
        return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
        return []


def scan_github_trending(domain_config: dict, domain: str) -> list[Signal]:
    signals = []
    for topic in domain_config.get("github_topics", []):
        repos = _gh_search([f"topic:{topic}"], sort="stars",
                          limit=CONFIG["filters"]["max_signals_per_source"])
        for r in repos:
            forks = r.get("forksCount", 0)
            sig = Signal(
                title=r["name"],
                url=r["url"],
                description=r.get("description", "") or "",
                source="github",
                domain=domain,
                relevance=min(5, max(1, forks // 50 + 1)),
                novelty=4,
                actionability=3,
                recommendation="WATCH",
                rationale=f"GitHub trending: {forks} forks",
            )
            signals.append(sig)
    return signals


def scan_arxiv(domain_config: dict, domain: str) -> list[Signal]:
    signals = []
    categories = domain_config.get("arxiv_categories", [])
    if not categories:
        return signals

    keywords = domain_config.get("keywords", [])[:3]
    keyword_filter = "+AND+".join(f'abs:"{k}"' for k in keywords)
    cats = "+OR+cat:".join(categories)
    url = (
        "http://export.arxiv.org/api/query?"
        f"search_query=cat:{cats}+AND+({keyword_filter})"
        "&sortBy=submittedDate&sortOrder=descending"
        f"&max_results={CONFIG['filters']['max_signals_per_source']}"
    )

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "OpportunityRadar/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            xml_data = resp.read().decode("utf-8")

        ns = {"atom": "http://www.w3.org/2005/Atom"}
        root = ET.fromstring(xml_data)
        for entry in root.findall("atom:entry", ns):
            title_el = entry.find("atom:title", ns)
            id_el = entry.find("atom:id", ns)
            summary_el = entry.find("atom:summary", ns)
            if title_el is None or id_el is None:
                continue
            title = (title_el.text or "").strip().replace("\n", " ")[:120]
            arxiv_url = (id_el.text or "").strip()
            summary = ((summary_el.text or "") if summary_el is not None else "")[:200]

            sig = Signal(
                title=title,
                url=arxiv_url,
                description=summary,
                source="arxiv",
                domain=domain,
                relevance=4,
                novelty=5,
                actionability=3,
                recommendation="WATCH",
                rationale="New academic paper in domain",
            )
            signals.append(sig)
    except Exception:
        pass

    return signals


def scan_competitors(domain_config: dict, domain: str) -> list[Signal]:
    signals = []
    for competitor in domain_config.get("competitors", []):
        repos = _gh_search(
            [competitor], sort="updated",
            limit=2,
        )
        for r in repos:
            sig = Signal(
                title=f"{competitor}: {r['name']}",
                url=r["url"],
                description=r.get("description", "") or "",
                source="competitor",
                domain=domain,
                relevance=4,
                novelty=3,
                actionability=2,
                recommendation="WATCH",
                rationale=f"Competitor activity: {competitor}",
            )
            signals.append(sig)
    return signals


def scan_hacker_news(domain_config: dict, domain: str) -> list[Signal]:
    signals = []
    keywords = domain_config.get("keywords", [])
    if not keywords:
        return signals

    try:
        req = urllib.request.Request(
            "https://hacker-news.firebaseio.com/v0/topstories.json",
            headers={"User-Agent": "OpportunityRadar/1.0"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            story_ids = json.loads(resp.read().decode("utf-8"))[:30]

        for story_id in story_ids:
            item_url = (
                f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
            )
            try:
                req = urllib.request.Request(
                    item_url, headers={"User-Agent": "OpportunityRadar/1.0"}
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    item = json.loads(resp.read().decode("utf-8"))
            except Exception:
                continue

            title = item.get("title", "")
            title_lower = title.lower()
            if not any(k.lower() in title_lower for k in keywords):
                continue

            sig = Signal(
                title=title,
                url=item.get("url", f"https://news.ycombinator.com/item?id={story_id}"),
                description=item.get("text", "")[:200] or "HN discussion",
                source="hackernews",
                domain=domain,
                relevance=4,
                novelty=4,
                actionability=3,
                recommendation="WATCH",
                rationale="HN discussion in domain",
            )
            signals.append(sig)
    except Exception:
        pass

    return signals


# ── Synthesis ──────────────────────────────────────────────────────────

def classify_signal(sig: Signal) -> str:
    score = sig.combined_score
    if score >= 12 and sig.relevance >= 4 and sig.actionability >= 3:
        return "BUILD"
    elif score >= 7:
        return "WATCH"
    return "SKIP"


def generate_recommendation(signals: list[Signal]) -> str:
    build = [s for s in signals if s.recommendation == "BUILD"]
    if not build:
        return "No urgent opportunities this week. Continue current roadmap."
    top = sorted(build, key=lambda s: s.combined_score, reverse=True)[0]
    return (
        f"Highest-impact move: *{top.title}* ({top.domain}). "
        f"Score: {top.combined_score}/15. "
        f"Run Phase 2 (Requirements Engine) to generate a spec."
    )


def synthesize(signals: list[Signal]) -> StrategicBrief:
    for sig in signals:
        sig.recommendation = classify_signal(sig)

    filtered = [
        s for s in signals
        if s.combined_score >= CONFIG["filters"]["min_combined_score"]
    ]
    filtered = sorted(filtered, key=lambda s: s.combined_score, reverse=True)
    filtered = filtered[: CONFIG["filters"]["max_total_signals"]]

    return StrategicBrief(
        date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        signals=filtered,
        recommendation=generate_recommendation(filtered),
    )


# ── Discord Delivery ────────────────────────────────────────────────────

def deliver_discord(brief: StrategicBrief) -> bool:
    """Send brief to Discord via webhook. Returns True on success."""
    webhook_url = DISCORD_WEBHOOK_URL
    if not webhook_url:
        print("[WARN] DISCORD_WEBHOOK_URL not set — skipping Discord delivery")
        return False

    content = brief.to_discord()
    # Discord max message length
    if len(content) > 2000:
        content = content[:1997] + "..."

    payload = {
        "content": content,
        "username": "Grand SIE — Opportunity Radar",
        "avatar_url": "https://i.imgur.com/AfFp7pu.png",
    }

    try:
        if requests is not None:
            r = requests.post(webhook_url, json=payload, timeout=15)
        else:
            import urllib.request
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                webhook_url,
                data=data,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                resp.read()

        print(f"[OK] Strategic Brief delivered to Discord "
              f"({len(brief.signals)} signals)")
        return True
    except Exception as e:
        print(f"[ERROR] Discord delivery failed: {e}", file=sys.stderr)
        return False


# ── Main ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Opportunity Radar")
    parser.add_argument(
        "--sources", nargs="+",
        choices=["github", "arxiv", "competitors", "hn"],
        help="Which sources to scan (default: all)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print brief to stdout instead of delivering",
    )
    parser.add_argument(
        "--deliver", choices=["discord", "stdout", "none"],
        default="discord",
        help="Delivery target (default: discord)",
    )
    args = parser.parse_args()

    scanners = {
        "github": scan_github_trending,
        "arxiv": scan_arxiv,
        "competitors": scan_competitors,
        "hn": scan_hacker_news,
    }

    enabled = (
        {k: v for k, v in scanners.items() if k in (args.sources or [])}
        if args.sources
        else scanners
    )

    all_signals: list[Signal] = []
    for src_key, scanner_fn in enabled.items():
        for domain, domain_config in CONFIG["domains"].items():
            try:
                signals = scanner_fn(domain_config, domain)
                all_signals.extend(signals)
            except Exception as e:
                print(f"[ERROR] {src_key}/{domain}: {e}", file=sys.stderr)

    brief = synthesize(all_signals)

    build_count = len([s for s in brief.signals if s.recommendation == "BUILD"])

    if args.dry_run:
        print(brief.to_markdown())
    elif args.deliver == "discord":
        ok = deliver_discord(brief)
        if not ok:
            # Fall back to stdout so something always surfaces
            print(brief.to_markdown())
    elif args.deliver == "stdout":
        print(brief.to_markdown())

    sys.exit(0 if build_count > 0 else 1)


if __name__ == "__main__":
    main()
