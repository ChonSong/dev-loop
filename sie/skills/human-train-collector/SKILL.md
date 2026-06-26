---
name: human-train-collector
description: Scrape human-written text from free public APIs (Hacker News, Reddit, blogs) for AI detection training data. Uses Scrapling. Outputs JSONL.
category: writing
---

# Human Training Data Collector

Scrape human-written text from free public APIs for training data to beat AI detection.

## Location

Script: `~/workspace/human-train-collector.py`

## When to Use This

**Prefer existing datasets first.** Large human-written text datasets are available on HuggingFace (OpenWebText, WikiText, TinyStories, C4) and can be loaded instantly with `datasets.load_dataset()`. Only use this scraper when you need domain-specific text not covered by existing datasets.

## Quick Start

```bash
cd ~/workspace && source .venv/bin/activate

# Collect from Hacker News
python3 human-train-collector.py --sources hackernews --limit 500 -o training.jsonl

# Multiple sources
python3 human-train-collector.py --sources hackernews,reddit --limit 1000 -o bigset.jsonl

# All sources  
python3 human-train-collector.py --sources all --limit 2000
```

## Auto-collection (cron) — REMOVED

Cron was removed. Existing datasets (OpenWebText, etc.) on HuggingFace are preferred over scraping. If you re-enable, use `cronjob action=create` with the prompt from the skill's history or references.

## Output Format

JSONL — one JSON object per line with keys: text, source, url, subsource.

## Sources

| Source | API | Auth | Notes |
|--------|-----|------|-------|
| **hackernews** | Firebase API | None | Top stories + comments. Simple, fast, reliable. |
| **reddit** | old.reddit.com JSON | None | Hot posts + comments. Rate limits apply (~1-2s delay). |
| **blogs** | Curated list | None | Paul Graham, Dan Luu, Julia Evans, etc. Lightweight HTML scraping. |

## Scrapling 0.4.x API

Version 0.4.9 installed in `.venv/`. Breaking changes from 0.2.x:

| v0.2.x (old) | v0.4.x (current) |
|-------------|-------------------|
| `fetcher.get(url, stealth=False)` | `fetcher.get(url)` — no `stealth=` param |
| `resp.text()` | `resp.text` (property, not method) |
| `resp.content()` | `resp.body` (property) |
| `fetcher._session = None` | No cleanup needed — goes out of scope |

Import: `from scrapling.fetchers import AsyncFetcher`
Use: `fetcher = AsyncFetcher()` then `resp = await fetcher.get(url)`

## Pitfalls

- **Activate .venv first.** The Hermes venv (`python3` at `/home/sc/.hermes/hermes-agent/venv/bin/python3`) doesn't have scrapling. Always `source .venv/bin/activate`.
- **Respect rate limits.** HN Firebase is fast but Reddit needs 0.5-1.5s between requests.
- **HTML entities.** HN comments come with HTML (`<p>`, `<i>`) and entities (`&#x27;`). The collector now strips both via `html.unescape()` + regex.
- **Minimum sample length.** Comments <40 chars or >2000 chars are filtered. Averages around 370 chars per sample.
- **AI text filter.** The collector skips text matching `_is_likely_ai()` — common AI phrases, disclaimer patterns, "[deleted]", etc.