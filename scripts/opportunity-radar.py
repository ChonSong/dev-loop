#!/usr/bin/env python3
"""
Opportunity Radar — Grand SIE Phase 1.

Weekly scan of the external world for signals worth acting on.
Outputs a Strategic Brief delivered to the morning briefing or a dedicated channel.

Usage:
    python3 opportunity-radar.py                     # Run all scans, output brief
    python3 opportunity-radar.py --sources github    # Single source
    python3 opportunity-radar.py --dry-run            # Print brief to stdout
    python3 opportunity-radar.py --deliver morning    # Deliver to morning briefing

Sources:
    - GitHub trending (per-domain: poker, 3DCP, AI agents, game dev)
    - arXiv papers (keyword-filtered)
    - Competitor activity (defined in CONFIG)
    - Hacker News / product launches

Exit codes:
    0 — brief produced
    1 — no actionable signals (quiet exit — cron stays silent)
    2 — error
"""

import argparse
import json
import math
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ── Configuration ──────────────────────────────────────────────────────

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
        "min_combined_score": 7,    # (relevance + novelty + actionability)
        "max_signals_per_source": 5,
        "time_window_days": 7,
        "max_total_signals": 20,    # cap total brief size
    },
    "report": {
        "header": "# Strategic Brief — {date}",
        "sections": {
            "worth_building": "### 🟢 Worth Building",
            "worth_watching": "### 🟡 Worth Watching",
            "skip": "### 🔴 Skip / Out of Scope",
        },
    },
}


# ── Data Model ─────────────────────────────────────────────────────────

@dataclass
class Signal:
    title: str
    url: str
    description: str
    source: str                # "github", "arxiv", "competitor", "hackernews"
    domain: str                # "poker", "3dcp", "ai-agents", "game-dev"
    relevance: int             # 1-5
    novelty: int               # 1-5
    actionability: int         # 1-5
    recommendation: str        # "BUILD", "WATCH", "SKIP"
    rationale: str = ""        # Why this matters for our work
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def combined_score(self) -> int:
        return self.relevance + self.novelty + self.actionability


@dataclass
class StrategicBrief:
    date: str
    signals: list[Signal]
    recommendation: str = ""
    project_health: dict[str, str] = field(default_factory=dict)

    def to_markdown(self) -> str:
        lines = [f"# Strategic Brief — {self.date}", ""]
        build = [s for s in self.signals if s.recommendation == "BUILD"]
        watch = [s for s in self.signals if s.recommendation == "WATCH"]
        skip = [s for s in self.signals if s.recommendation == "SKIP"]

        if build:
            lines.append("### 🟢 Worth Building")
            for s in build:
                lines.append(f"- **[{s.title}]({s.url})** — {s.domain.upper()}")
                lines.append(f"  Relevance: {s.relevance}/5, Novelty: {s.novelty}/5")
                if s.rationale:
                    lines.append(f"  _{s.rationale}_")
            lines.append("")

        if watch:
            lines.append("### 🟡 Worth Watching")
            for s in watch:
                lines.append(f"- **[{s.title}]({s.url})** — {s.domain.upper()}")
                if s.rationale:
                    lines.append(f"  _{s.rationale}_")
            lines.append("")

        if skip:
            lines.append("### 🔴 Skip / Out of Scope")
            for s in skip:
                lines.append(f"- **[{s.title}]({s.url})** — {s.rationale}")
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


# ── Scanners ────────────────────────────────────────────────────────────

def scan_github_trending(domain_config: dict, domain: str) -> list[Signal]:
    """Scan GitHub trending repos by topic. Returns up to 5 signals."""
    signals = []
    for topic in domain_config.get("github_topics", []):
        try:
            # gh CLI: search repos by topic, sort by stars, limit 5
            result = subprocess.run(
                [
                    "gh", "search", "repos",
                    f"topic:{topic}",
                    "--sort", "stars",
                    "--limit", str(CONFIG["filters"]["max_signals_per_source"]),
                    "--json", "name,url,description,updatedAt,stargazersCount",
                ],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode != 0:
                continue
            repos = json.loads(result.stdout)
            for r in repos:
                sig = Signal(
                    title=r["name"],
                    url=r["url"],
                    description=r.get("description", "") or "",
                    source="github",
                    domain=domain,
                    relevance=min(5, max(1, round(math.log(r.get("stargazersCount", 0) + 1, 10000) * 5))),
                    novelty=3,  # trending repos are rarely surprises
                    actionability=2,  # needs evaluation before actionable
                    recommendation="WATCH",
                    rationale="GitHub trending — worth evaluating",
                )
                signals.append(sig)
        except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
            continue
    return signals


def scan_arxiv(domain_config: dict, domain: str) -> list[Signal]:
    """Scan arXiv for new papers matching domain keywords."""
    signals = []
    categories = domain_config.get("arxiv_categories", [])
    if not categories:
        return signals

    keywords = domain_config.get("keywords", [])
    keyword_filter = "+AND+".join(
        f'abs:"{k}"' for k in keywords[:3]
    )

    # arXiv API: search abstracts from the last 7 days
    now = datetime.now(timezone.utc)
    date_from = now.strftime("%Y%m%d")
    # We search with a reasonable time window
    url = (
        f"http://export.arxiv.org/api/query?"
        f"search_query=cat:{'+OR+cat:'.join(categories)}"
        f"+AND+({keyword_filter})"
        f"&sortBy=submittedDate&sortOrder=descending"
        f"&max_results={CONFIG['filters']['max_signals_per_source']}"
    )

    try:
        import urllib.request
        import xml.etree.ElementTree as ET

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
            title = (title_el.text or "").strip().replace("\n", " ")
            arxiv_url = (id_el.text or "").strip()
            summary = ((summary_el.text or "") if summary_el is not None else "")[:200]

            sig = Signal(
                title=title[:120],
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
        pass  # arXiv API flakiness is expected

    return signals


def scan_competitors(domain_config: dict, domain: str) -> list[Signal]:
    """Check competitor repos for recent activity."""
    signals = []
    for competitor in domain_config.get("competitors", []):
        try:
            # Search GitHub for competitor repos
            result = subprocess.run(
                [
                    "gh", "search", "repos",
                    competitor,
                    "--limit", "3",
                    "--sort", "updated",
                    "--json", "name,url,description,updatedAt",
                ],
                capture_output=True, text=True, timeout=15,
            )
            if result.returncode != 0:
                continue
            repos = json.loads(result.stdout)
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
                    rationale=f"Competitor activity in {domain}",
                )
                signals.append(sig)
        except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
            continue
    return signals


def scan_hacker_news(domain_config: dict, domain: str) -> list[Signal]:
    """Scan Hacker News for relevant posts."""
    signals = []
    keywords = domain_config.get("keywords", [])
    if not keywords:
        return signals

    try:
        import urllib.request
        import json

        # Get top stories from HN API
        req = urllib.request.Request(
            "https://hacker-news.firebaseio.com/v0/topstories.json",
            headers={"User-Agent": "OpportunityRadar/1.0"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            story_ids = json.loads(resp.read().decode("utf-8"))[:30]

        for story_id in story_ids:
            item_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
            req = urllib.request.Request(item_url, headers={"User-Agent": "OpportunityRadar/1.0"})
            try:
                with urllib.request.urlopen(req, timeout=10) as resp:
                    item = json.loads(resp.read().decode("utf-8"))
            except Exception:
                continue

            title = item.get("title", "")
            title_lower = title.lower()

            # Check if any keyword matches (word boundary, not substring)
            words = title_lower.split()
            keywords_lower = [k.lower() for k in keywords]
            if not any(kw in words for kw in keywords_lower):
                # Also check multi-word keywords
                if not any(kw in title_lower for kw in keywords_lower if ' ' in kw):
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
                rationale="Hacker News discussion in domain",
            )
            signals.append(sig)
    except Exception:
        pass

    return signals


# ── Synthesis ──────────────────────────────────────────────────────────

def classify_signal(sig: Signal) -> str:
    """Classify a signal as BUILD / WATCH / SKIP based on score and context."""
    score = sig.combined_score
    if score >= 12 and sig.relevance >= 4 and sig.actionability >= 3:
        return "BUILD"
    elif score >= 7:
        return "WATCH"
    else:
        return "SKIP"


def generate_recommendation(signals: list[Signal]) -> str:
    """Produce a single actionable recommendation from all signals."""
    build = [s for s in signals if s.recommendation == "BUILD"]
    if not build:
        return "No urgent opportunities this week. Continue current roadmap."

    top = sorted(build, key=lambda s: s.combined_score, reverse=True)[0]
    return (
        f"**Highest-impact move**: Build something related to "
        f"_{top.title}_ ({top.domain}). "
        f"Combined score: {top.combined_score}/15. "
        f"See the Requirements Engine (Phase 2) to generate a spec."
    )


def synthesize(signals: list[Signal]) -> StrategicBrief:
    """Score, filter, classify, and produce a StrategicBrief."""
    # Score and filter
    filtered = []
    for sig in signals:
        sig.recommendation = classify_signal(sig)
        if sig.combined_score >= CONFIG["filters"]["min_combined_score"]:
            filtered.append(sig)

    # Cap total
    filtered = sorted(filtered, key=lambda s: s.combined_score, reverse=True)
    filtered = filtered[: CONFIG["filters"]["max_total_signals"]]

    brief = StrategicBrief(
        date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        signals=filtered,
        recommendation=generate_recommendation(filtered),
    )
    return brief


# ── Delivery ───────────────────────────────────────────────────────────

def deliver_morning_briefing(brief: StrategicBrief) -> None:
    """Append the strategic brief to the morning briefing report."""
    morning_dir = Path(os.environ.get("HERMES_HOME", "/home/sc/.hermes"))
    morning_file = morning_dir / "cron" / "output" / "morning-briefing-latest.md"
    morning_file.parent.mkdir(parents=True, exist_ok=True)

    # Read existing or create
    existing = ""
    if morning_file.exists():
        existing = morning_file.read_text()

    with open(morning_file, "w") as f:
        f.write(existing.strip() + "\n\n" + brief.to_markdown() + "\n")


def deliver_stdout(brief: StrategicBrief) -> None:
    """Print to stdout for cron delivery."""
    print(brief.to_markdown())


# ── Main ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Opportunity Radar")
    parser.add_argument("--sources", nargs="+",
                        choices=["github", "arxiv", "competitors", "hn"],
                        help="Which sources to scan (default: all)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print brief to stdout (no delivery)")
    parser.add_argument("--deliver", choices=["morning", "stdout", "none"],
                        default="stdout",
                        help="Delivery target")
    args = parser.parse_args()

    # Determine which sources to run
    source_map = {
        "github": ("github", scan_github_trending),
        "arxiv": ("arxiv", scan_arxiv),
        "competitors": ("competitors", scan_competitors),
        "hn": ("hn", scan_hacker_news),
    }

    if args.sources:
        enabled_sources = {k: v for k, v in source_map.items() if k in args.sources}
    else:
        enabled_sources = source_map

    # Collect signals from all domains × enabled sources
    all_signals: list[Signal] = []
    for source_key, (src_label, scanner_fn) in enabled_sources.items():
        for domain, domain_config in CONFIG["domains"].items():
            try:
                signals = scanner_fn(domain_config, domain)
                all_signals.extend(signals)
            except Exception as e:
                print(f"[ERROR] {src_label}/{domain}: {e}", file=sys.stderr)

    # Synthesise
    brief = synthesize(all_signals)

    # Deliver
    actionable = len([s for s in brief.signals if s.recommendation == "BUILD"])
    total = len(brief.signals)

    if args.dry_run or args.deliver == "stdout":
        deliver_stdout(brief)
    elif args.deliver == "morning":
        deliver_morning_briefing(brief)
        print(f"[OK] Strategic Brief delivered to morning briefing "
              f"({total} signals, {actionable} actionable)")

    # Exit code: 0 if actionable, 1 if none (silent for cron)
    sys.exit(0 if actionable > 0 else 1)


if __name__ == "__main__":
    main()
