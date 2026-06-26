---
name: job-search
description: Search Indeed and LinkedIn jobs via Apify actors, track free-tier credit usage, and persist results.
category: automation
tags: [job, apify, mcp, free-tier, integration]
---

# Job-search Integration

## Quick Start

```bash
# Fastest: invoke the search script directly
python3 ~/.hermes/skills/automation/job-search/scripts/run_search.py \\
  --positions "Data Scientist" \\
  --locations "Sydney, NSW" \\
  --country "AU"
```

Or via chat (one-shot):
```bash
hermes -z "Search Indeed for Data Scientist jobs in Sydney, AU, max 200" -s job-search
```

## 🔍 Seek AU (Broaden Your Search)

For comprehensive Australian coverage, run both Indeed AND Seek:

### Option 1: Dedicated run_seek_search.py script (Recommended)
```bash
python3 ~/.hermes/skills/automation/job-search/scripts/run_seek_search.py \
  --keywords "Data Scientist" \
  --location "Sydney NSW" \
  --site AU-Main \
  --max 200
```

### Options
- `--site AU-Main` — Seek.com.au (AU). Use `NZ-Main` for Seek.co.nz.
- `--location` — Location filter. Omit for nationwide.
- `--remote` — Remote-only jobs.
- `--keywords` — Comma-separated keywords. Multiple search queries in one run.
- `--outdir` — Save location (default: `~/.hermes/jobs/`).
- `--max` — Max total results (default: 200).

Uses `bovi/seek-jobs-scraper` ($0.90/1k) — structured seniority, salary, remote_type, bullet_points, classification. Richer output than Indeed for AU.

## 🔄 Ongoing Monitoring: NexGenData Jobs MCP

For continuous job market monitoring, set up the NexGenData Jobs MCP server:

```bash
# Install the NexGenData Jobs MCP server
hermes mcp install nexgendata/job-market-mcp-server

# Configure in ~/.hermes/config.yaml (if not auto-configured):
# mcp:
#   servers:
#     nexgendata:
#       url: https://api.nexgendata.com/mcp
#       auth_header: "Bearer <YOUR_NEXGENDATA_TOKEN>"
```

The NexGenData MCP provides:
- Unified access to Indeed, LinkedIn, and salary data
- Real-time updates via MCP protocol
- Free tier available
- Single endpoint for multiple job boards

## Key Input Fields (Apify Indeed Scraper)

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `positions` | `array<string>` | Yes | Job titles/keywords. Each runs against each location. |
| `locations` | `array<string>` | No | Cities, regions, or `"Remote"`. Leave empty for nationwide. |
| `country` | `string` | No | Indeed domain. **Default: `US`** — must set `"AU"` for Australia. Options: `US`, `UK`, `CA`, `AU`, `IE`, `IN`, `SG`, `ZA`, `NZ`. |
| `maxItemsPerSearch` | `integer` | No | Target results per position×location (min 1, max 200, default 50). |
| `proxyConfiguration` | `object` | No | **Must use RESIDENTIAL proxies** — Indeed blocks datacenter IPs. |

All parameters documented in `references/input-schema.md`.

## How It Works

1. **Read credentials** from `~/.hermes/secrets/apify.env`.  
2. **Call Indeed actor** `sheshinmcfly/indeed-jobs-scraper` via `POST /v2/acts/{actorId}/runs`.  
3. **Poll** status at `GET /v2/actor-runs/{runId}` until SUCCEEDED.  
4. **Fetch** dataset at `GET /v2/datasets/{datasetId}/items`.  
5. **Merge** results, write JSON to `~/.hermes/jobs/<timestamp>.json`.  
6. **Report** credit usage and remaining balance.

## 🔁 Continuous Application Pipeline

The pipeline runs daily via cron, auto-chained 07:00→07:30→08:00 AEST. All three cron jobs are `no_agent` (pure Python scripts, zero LLM cost).

### Architecture

```
┌─────────────────────────────────────────────────┐
│   07:00  seek-daily-search.py                   │
│   bovi/seek-jobs-scraper  ~250 jobs  ~$0.23/d  │
├─────────────────────────────────────────────────┤
│   07:30  indeed-daily-search.py                 │
│   sheshinmcfly~indeed-jobs-scraper  ~$0.75/d   │
├─────────────────────────────────────────────────┤
│   08:00  daily-job-pipeline.py                  │
│   dedup → filter → registry → queue            │
├─────────────────────────────────────────────────┤
│         track [status|queue|apply|skip|history] │
│         CLI alias at ~/.local/bin/track         │
└─────────────────────────────────────────────────┘
```

### Cron Jobs (all script-only, no LLM)

| Job | Script | Schedule | Est. cost/day |
|-----|--------|----------|--------------|
| Seek Daily | `seek-daily-search.py` | 07:00 AEST | ~$0.23 |
| Indeed Daily | `indeed-daily-search.py` | 07:30 AEST | ~$0.75 |
| Pipeline | `daily-job-pipeline.py` | 08:00 AEST | $0 |

Scripts live in `~/.hermes/scripts/` (cron resolution path). The pipeline reads *all* today's job JSON files, deduplicates against `~/.hermes/jobs/registry.json`, filters for entry-level suitability, and writes the queue to `~/.hermes/jobs/queue/<ts>-queue.json`.

### Entry-Level Filtering Heuristics

The pipeline classifies each job into three buckets:

| Verdict | Criteria |
|---------|----------|
| `yes` (entry) | Title contains: graduate, junior, associate, entry, intern, trainee, cadet, undergraduate, new grad, analyst; OR seniority field is intern/entry/junior/graduate/trainee |
| `maybe` | Seniority is mid/associate; OR salary ≤$80k; OR generic entry title (customer service, admin, data entry, support officer) |
| `no` (skipped) | Title contains: senior, lead, principal, director, head of, manager (unless negated by assistant/associate/junior/graduate), staff, architect, VP/CTO/CEO/CFO/chief |

Conservative by design — `maybe` jobs are included in the queue (flagged) for human review.

### Job Tracker CLI

```bash
track status          # queue stats + applied count today
track queue [N]       # list top N from latest queue
track apply <N>       # mark queue item #N as applied
track skip <N> [reason]  # skip with optional reason
track history [days]  # full application log
```

Tracks writes to `~/.hermes/jobs/applications.json`. All apps logged with date, title, company, URL, source, and optional note.

### Keyword Configuration (daily cron)

Both scraper scripts iterate 5 keyword sets × 5 cities:

```python
KEYWORDS = [
    "graduate,junior,associate,entry level,analyst",
    "trainee,intern,cadet,undergraduate,new grad",
    "software engineer junior,data analyst entry,IT support",
    "administrative assistant,customer service,operations coordinator",
    "sales associate,marketing coordinator,project support",
]
LOCATIONS = [
    "Sydney NSW" / "Sydney, NSW",
    "Melbourne VIC" / "Melbourne, VIC",
    "Brisbane QLD" / "Brisbane, QLD",
    "Perth WA" / "Perth, WA",
    "Adelaide SA" / "Adelaide, SA",
]
```

Cost $29/month full blast. To trim: reduce Indeed to weekly-only, or cap to Sydney/Melbourne only ($12-15/mo).

### Registration & Dedup

`registry.json` tracks seen URLs by their canonical job link. Once a URL enters the registry, it's never fetched again — even across different keyword sets or scrapers. Registry persists across days so a job from Monday doesn't reappear on Tuesday.

## Support Files

- `scripts/run_search.py` — standalone Indeed search script (Python, no apify-client needed).  
- `scripts/run_seek_search.py` — standalone Seek search script via `bovi/seek-jobs-scraper` (Python, no apify-client needed).  
- `scripts/check_credit.py` — prints remaining Apify credits.  
- `scripts/seek_search.py` — alternative Seek search.  
- `references/input-schema.md` — full Indeed scraper input fields + endpoint reference.  
- `references/quickstart.md` — step-by-step setup.  
- `references/cron-pipeline-architecture.md` — deployed continuous pipeline architecture.  

**Cron scripts** (in `~/.hermes/scripts/` — cron system path):
- `seek-daily-search.py` — daily cron Seek scraper (5×5 keywords×cities)
- `indeed-daily-search.py` — daily cron Indeed scraper (5×5)
- `daily-job-pipeline.py` — dedup + filter + queue pipeline
- `job-tracker.py` — CLI via `track` alias  

## User Preferences (embedded)

- **Execute, don't explain.** The goal is to produce results, not narrate the process. Show JSON path and credit summary; skip verbose play-by-play.  
- **Get it done.** If CLI command fails, script the API directly rather than iterating through dead-end CLI incantations.  
- **Evidence-backed.** Always report credit consumption and remaining free tier balance.  

## Recommended Scrapers for Australia

| Scraper | Actor ID | Site | Price/1k | Notes |
|---------|----------|------|----------|-------|
| Indeed AU | `sheshinmcfly/indeed-jobs-scraper` | Indeed | ~$0.06 | Residential proxies required. Good for remote/nationwide. |
| Seek AU+NZ | `bovi/seek-jobs-scraper` | Seek | **$0.90** | Structured seniority, salary, remote_type, bullet_points, classification, parse_confidence. Best structured output. |
| Seek AU+NZ | `scrapersdelight/seek-jobs-scraper` | Seek | **$0.20** | Cheapest Seek option. Parsed salary, remote flag, contact email. |
| Seek AU+NZ | `blackfalcondata/seek-scraper` | Seek | ~$0.70 | ⭐5.0, 556 users. Incremental mode, compact output, most popular. |
| Seek NZ | `bovi/seek-jobs-scraper` | Seek NZ | $0.90 | Same actor, use `siteKey: NZ-Main`. |
| Jobs MCP | `nexgendata/job-market-mcp-server` | Indeed+LinkedIn+Salary | Free tier | MCP server. Single endpoint for multiple boards + salary data. |

**Seek is the #1 AU job board** (160k+ live listings). For comprehensive coverage, run both Indeed AND Seek. Prefer `bovi/seek-jobs-scraper` ($0.90/1k) when you need structured fields (seniority, remote_type, salary parsing, bullet_points); use `scrapersdelight/seek-jobs-scraper` ($0.20/1k) for cheap bulk.

### Seek Actor Comparison

| Feature | bovi ($0.90) | scrapersdelight ($0.20) | blackfalcondata ($0.70) |
|---------|:---:|:---:|:---:|
| Structured salary | ✅ | ✅ | ✅ |
| Seniority level | ✅ 11 levels | ❌ | ❌ |
| Remote type | ✅ hybrid/remote/onsite | ❌ | ❌ |
| Bullet points | ✅ up to 3 | ❌ | ❌ |
| Classification | ✅ 2-level | ✅ | ❌ |
| Parse confidence | ✅ 0.0–1.0 | ❌ | ❌ |
| Incremental mode | ❌ | ❌ | ✅ |
| NZ support | ✅ NZ-Main | ❌ | ✅ |

## Reliable Execution Pattern

The most reliable approach is a **background Python script with explicit polling**:

```python
# Write search script to /tmp/indeed_search.py (or /tmp/seek_search.py)
# Key: use -u for unbuffered output, poll with 10s intervals, max 60 attempts
python3 -u /tmp/indeed_search.py 2>&1
```

**Why not `hermes -z`?** One-shot mode (`hermes -z -s job-search \"prompt\"`) silently fails with \"no final response was produced\" when the model doesn't invoke Apify tools. The direct script approach bypasses the model entirely and calls the Apify API directly.

**Why not `hermes skill run`?** This subcommand does not exist in Hermes v0.16.0.

**Why not `hermes chat -p`?** The `-p` flag is not a valid argument.

## Apify Account (Confirmed)

- Account: `limpid-condor` (seanos1a@gmail.com)  
- Plan: FREE — $5/month usage credits  
- Residential proxies: enabled (0 available in RESIDENTIAL group, but actor defaults work)  
- Datacenter proxies: 5 available in `BUYPROXIES94952` group  

## Pitfalls

- **Country defaults to US** – The Indeed scraper uses `"US"` as default country. For Australian searches, you MUST pass `"country": "AU"` in the input. Without it, results will be US listings even if `locations` contains Australian cities.  
- **Overrunning free-tier credits** – The script aborts if credits would exceed the $5 free-tier allowance. Adjust `--max` or verify remaining credits before running.  
- **Residential proxies required** – Indeed blocks datacenter IPs via Cloudflare. The actor requires RESIDENTIAL proxies; this is the default, do not change the proxy config unless testing.  
- **Hermes v0.16.0 has no `hermes skill run`** – The `skill run` subcommand does not exist. Use the run_search.py script directly.  
- **`hermes chat -p` doesn't work** – The `-p` flag is not a valid argument. Use `-z` (oneshot) or start interactive chat.  
- **One-shot mode can produce no output** – `hermes -z -s job-search \"prompt\"` may return \"no final response was produced\" if the model doesn't invoke Apify tools. Fall back to the direct script in that case.  
- **Python stdout buffering** – When running inline Python via `python3 -c`, output is buffered and invisible until the process exits. Always use `-u` flag or write to a file and `tail -f`.  
- **Actor run takes 2-5 minutes** — Indeed scraper with multiple position×location combos takes time. Poll at 10s intervals, expect 60-300s total.  
- **Seek timing** – `bovi/seek-jobs-scraper` is fast (~30-60s) — uses the public Seek v5 API directly, no proxy needed. Poll at 5s intervals, expect 30-120s. Unlike `scrapersdelight`, this actor finishes quickly even for 200 results.  
- **Seek siteKey matters** – Always set `siteKey: "AU-Main"` or `"NZ-Main"`. Default may vary by actor. `bovi/seek-jobs-scraper` defaults to AU-Main.  