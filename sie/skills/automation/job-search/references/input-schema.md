# Indeed Jobs Scraper — Input Schema & API Reference

**Actor**: `sheshinmcfly/indeed-jobs-scraper`
**Pricing**: $5.00 / 1,000 results
**Last modified**: ~June 2026

## Input Fields

| Field | Type | Required | Details |
|-------|------|----------|---------|
| `positions` | `array<string>` | **Yes** | Job titles/keywords to search. Each runs against each location. |
| `locations` | `array<string>` | No | Cities, regions, or `"Remote"`. Leave empty for a nationwide search. |
| `country` | `string` | No | Indeed regional domain. **Default: `US`**. Options: `US`, `UK`, `CA`, `AU`, `IE`, `IN`, `SG`, `ZA`, `NZ`. **Must set to `AU` for Australia.** |
| `maxItemsPerSearch` | `integer` | No | Target results per position×location. Min 1, **Max 200**, Default 50. Partitions by date to avoid Indeed login-gated pagination. |
| `proxyConfiguration` | `object` | No | **Must use RESIDENTIAL proxies** — Indeed blocks datacenter IPs via Cloudflare. Default config: `{"useApifyProxy": true, "apifyProxyGroups": ["RESIDENTIAL"]}` |

## Example Input

```json
{
  "positions": ["Data Scientist", "Machine Learning Engineer"],
  "locations": ["Sydney, NSW", "Remote"],
  "country": "AU",
  "maxItemsPerSearch": 200,
  "proxyConfiguration": {
    "useApifyProxy": true,
    "apifyProxyGroups": ["RESIDENTIAL"]
  }
}
```

## API Endpoints

| Action | Method | URL |
|--------|--------|-----|
| Run actor | `POST` | `/v2/acts/{actorId}/runs` |
| Poll run status | `GET` | `/v2/actor-runs/{runId}` |
| Fetch results | `GET` | `/v2/datasets/{datasetId}/items` |
| Actor info | `GET` | `/v2/acts/{actorId}` |

**Actor ID**: `sheshinmcfly~indeed-jobs-scraper` (tilde in URL, not slash)

## Authentication

Store token in `~/.hermes/secrets/apify.env`:
```
APIFY_TOKEN=apify_api_xxxxxxxxxxxxxxxxxxxxx
```

Pass as `Authorization: Bearer *** header.

## Output Fields

Per job result item:

- `title` — Job title
- `company` — Company name
- `location` — Physical location
- `isRemote` — Boolean
- `salary` — Salary text (may be "Full-time" if not listed)
- `salaryMin`, `salaryMax` — Structured salary (may be null)
- `url` — Direct Indeed apply link
- `postedDate` — Posting date (may be null)
- `snippet` — Job description snippet (may be null)
- `country` — Search country code
- `searchLocation` — Location string used in search
- `scrapedAt` — ISO timestamp of scrape

---
# Seek Jobs Scraper — Input Schema & API Reference

**Actor**: `scrapersdelight~seek-jobs-scraper` (Recommended - cheapest)
**Alternative Actor**: `blackfalcondata~seek-scraper` (Most popular)
**Pricing**: ~$0.20 / 1,000 results (scrapersdelight)
**Last modified**: ~June 2026

## Input Fields (scrapersdelight/seek-jobs-scraper)

| Field | Type | Required | Details |
|-------|------|----------|---------|
| `positions` | `array<string>` | **Yes** | Job titles/keywords to search. Each runs against each location. |
| `locations` | `array<string>` | No | Cities, regions (AU/NZ), or `"Remote"`. Leave empty for nationwide (AU/NZ). |
| `maxItemsPerSearch` | `integer` | No | Target results per position×location. Min 1, max 500, default 100. |
| `proxyConfiguration` | `object` | No | **Must use RESIDENTIAL proxies** — Seek blocks datacenter IPs. Default: `{"useApifyProxy": true, "apifyProxyGroups": ["RESIDENTIAL"]}` |

## Example Input (scrapersdelight/seek-jobs-scraper)

```json
{
  "positions": ["Data Scientist", "Machine Learning Engineer"],
  "locations": ["Sydney, NSW", "Remote"],
  "maxItemsPerSearch": 200,
  "proxyConfiguration": {
    "useApifyProxy": true,
    "apifyProxyGroups": ["RESIDENTIAL"]
  }
}
```

## Example Input (blackfalcondata/seek-scraper)

```json
{
  "searchTerms": ["Data Scientist", "Machine Learning Engineer"],
  "locations": ["Sydney", "Remote"],
  "rows": 200,
  "sortBy": "date",
  "proxyConfiguration": {
    "useApifyProxy": true,
    "apifyProxyGroups": ["RESIDENTIAL"]
  }
}
```

## API Endpoints (same for both Seek actors)

| Action | Method | URL |
|--------|--------|-----|
| Run actor | `POST` | `/v2/acts/{actorId}/runs` |
| Poll run status | `GET` | `/v2/actor-runs/{runId}` |
| Fetch results | `GET` | `/v2/datasets/{datasetId}/items` |
| Actor info | `GET` | `/v2/acts/{actorId}` |

**Actor ID**: `scrapersdelight~seek-jobs-scraper` or `blackfalcondata~seek-scraper` (tilde in URL, not slash)

## Authentication

Same as Indeed - use token from `~/.hermes/secrets/apify.env`:
```
APIFY_TOKEN=apify_api_xxxxxxxxxxxxxxxxxxxxx
```

Pass as `Authorization: Bearer *** header.

## Output Fields (scrapersdelight/seek-jobs-scraper)

Per job result item:

- `title` — Job title
- `company` — Company name
- `location` — Physical location (e.g., "Sydney NSW 2000")
- `isRemote` — Boolean (true for remote positions)
- `salary` — Salary text (parsed, e.g., "$100,000 - $120,000")
- `salaryMin`, `salaryMax` — Structured salary numbers (may be null)
- `url` — Direct Seek apply link
- `contactEmail` — Recruiter/contact email address (valuable!)
- `excerpt` — Job description snippet
- `teaser` — Short job teaser/summary
- `datePosted` — ISO timestamp when posted
- `jobType` — Employment type (Full-time, Part-time, Contract, etc.)
- `applyCount` — Number of applicants (if available)
- `companyRating` — Company rating out of 5 (if available)
- `scrapedAt` — ISO timestamp of scrape

## Output Fields (blackfalcondata/seek-scraper)

Per job result item:

- `position` — Job title
- `company` — Company name
- `location` — Location string
- `salary` — Salary range text
- `url` — Direct Seek URL
- `excerpt` — Job description
- `teaser` — Short summary
- `datePosted` — Posting date
- `employmentType` — Full-time, Part-time, etc.
- `scrapedAt` — Timestamp

Note: blackfalcondata output is more compact but less structured than scrapersdelight.

## Authentication

Same as Indeed - use token from `~/.hermes/secrets/apify.env`:
```
APIFY_TOKEN=apify_api_xxxxxxxxxxxxxxxxxxxxx
```

Pass as `Authorization: Bearer *** header.