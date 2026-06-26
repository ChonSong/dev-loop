# Cron Pipeline Architecture

## Overview

Three no_agent cron jobs chained daily. All scripts are pure Python, zero LLM cost.

## Cron Scripts (in ~/.hermes/scripts/)

| Script | Purpose | Actor | Rate |
|--------|---------|-------|------|
| `seek-daily-search.py` | Seek AU broad search | `bovi/seek-jobs-scraper` | $0.90/1k |
| `indeed-daily-search.py` | Indeed AU broad search | `sheshinmcfly/indeed-jobs-scraper` | $5/1k |
| `daily-job-pipeline.py` | Dedup + filter + queue | — | $0 |
| `job-tracker.py` | CLI for managing queue + apps | — | $0 |

## Schedule (AEST)

- 07:00 — Seek scraper (5 keyword sets × 5 cities, ~250 jobs)
- 07:30 — Indeed scraper (5 × 5, ~150 jobs)
- 08:00 — Pipeline (reads all today's files, dedups, filters, writes queue)

## Data Flow

```
~/.hermes/jobs/<ts>-seek.json       ← seek-daily-search.py
~/.hermes/jobs/<ts>-indeed.json     ← indeed-daily-search.py
~/.hermes/jobs/registry.json        ← daily-job-pipeline.py (seen URLs)
~/.hermes/jobs/queue/<ts>-queue.json  ← daily-job-pipeline.py (apply queue)
~/.hermes/jobs/applications.json    ← job-tracker.py (app history)
```

## Cost Calculation

- Seek: 250 jobs × 30 days = 7,500 × $0.90/1k = $6.75/month
- Indeed: 150 jobs × 30 days = 4,500 × $5/1k = $22.50/month
- Total: ~$29.25/month

To reduce: swap Indeed to weekly (30/7 × 22.50 = ~$3.20/month → total ~$10).
To minimise: restrict to Sydney+Melbourne only (40% of above).

## Configuration

Edit the KEYWORDS and LOCATIONS lists at the top of each scraper script to change search scope. Both scrapers iterate all combinations.

## Registry Persistence

`registry.json` stores `{seen_urls: {url: date}, seen_ids: {id: date}, last_run: date}`. Once a URL is seen, it's never re-queued. The file is human-editable — you can delete entries to re-fetch specific jobs.
