# B2B Data APIs for Job Hunting — Supplementary Playbook

> Company intelligence APIs (Explorium AgentSource, etc.) are not job boards — they won't list
> open roles. But they fill a gap: you can discover companies that *are hiring*, get their
> tech stack, and find relevant people for outreach, all from inside the container (bypassing
> the live-listing scrape problem).

## What These APIs Do Well

| Purpose | Useful? | Notes |
|---|---|---|
| Discover companies hiring in your field | ✅ | Filter by hiring events + industry + tech stack |
| Company intel for interview prep | ✅ | Description, size, revenue, funding, tech stack |
| Find people for outreach | ✅ | Prospects API — find hiring managers / team leads |
| Contact enrichment | ✅ | Get emails/phones for outreach |
| Get actual job listings | ❌ | Not a job board — no role titles, salary, apply links |
| Replace SEEK/LinkedIn | ❌ | Supplement, not substitute |

## API Endpoint Reference (Explorium AgentSource)

Base: `https://api.explorium.ai/v1/`
Auth: Header `API_KEY: <key>`

### Credit Management — Check Before You Spend

```
GET /v1/credits
```
Response: `{"allocated_credits": 100, "remaining_credits": 0, "account_type": "trial"}`

**Always call this first** before any paid operation. Free trial = 100 credits. Once they hit 0, paid endpoints return `"insufficient credits"` with 402 semantics. Simple stats calls (country + size only) are cheap; complex filter combos (adding `google_category`, `events`, `industry`) burn credits per call.

### Stats — Market sizing before fetching

```
POST /v1/businesses/stats
{"filters": {"country_code": {"values": ["au"]}, "company_size": {"values": ["51-200", ...]}}}
```
Returns counts by location, revenue, employee range. **Credit cost scales with filter complexity** — country + size alone is minimal; adding 3+ filter dimensions can consume credits quickly.

### Fetch Businesses — Company discovery

```
POST /v1/businesses
{"filters": {<filters>}, "mode": "preview"|"full", "page_size": 100}
```
- **mode=preview**: minimal fields (name, domain, logo, country). Cheap.
- **mode=full**: description, revenue range, size range, LinkedIn URL, technologies array. Costs more credits.

### Events Fetch Endpoint (separate from the fetch filter)

```
POST /v1/businesses/events
{"event_types": ["hiring_in_engineering_department"], "business_ids": ["<32-char-hex>"], "timestamp_from": "2026-03-01T00:00:00Z"}
```

**Known limitation**: returned 0 events for tested business IDs, likely because AU-specific records are sparse and coverage is shallow outside US/UK. The events fetch is less useful for AU-targeted job hunting than the `events` filter on the main fetch endpoint.

### Prospect Contact Enrichment

```json
POST /v1/prospects/contacts_information/enrich
{"prospect_id": "<40-char-hex-prospect-id>"}
```

**Note**: `prospect_id` is singular, not `prospect_ids`. Returns `request_status: "success"` or `"miss"`. On the free tier / base credits, this returns no actual email or phone data even with `has_email: true` filter.

### Prospect Boolean Filters

- `has_email: {"value": true}` — filter to only prospects with emails (useful before enrichment)
- `has_phone_number: {"value": true}` — similar for phone

### Useful Filters

| Filter | Format | Notes |
|---|---|---|
| `country_code` | `{"values": ["au"]}` | Alpha-2. Works reliably. |
| `city_region_country` | `{"values": ["Sydney, NSW, AU"]}` | **Often returns 0 results** — country-level filtering is more reliable |
| `company_size` | `{"values": ["51-200", "201-500", ...]}` | Use ranges: 1-10, 11-50, 51-200, 201-500, 501-1000, 1001-5000, 5001-10000, 10001+ |
| `company_tech_stack_tech` | `{"values": ["Python", "AWS"]}` | Matches companies using specific technologies |
| `events` | `{"values": ["hiring_in_engineering_department"], "last_occurrence": 90}` | **Must include `last_occurrence` (30-120 days) inside the events object**. Valid event types include: `hiring_in_engineering_department`, `hiring_in_sales_department`, `hiring_in_finance_department`, `new_funding_round`, `new_office`, `new_product`, `employee_joined_company`, `increase_in_engineering_department`, `merger_and_acquisitions` |
| `google_category` | `{"values": ["Computer Software"]}` | Use for industry filtering. Also try `linkedin_category` and `naics_category` (one category type per request). |
| `company_revenue` | `{"values": ["10M-25M", "25M-75M"]}` | Ranges: 0-500K, 500K-1M, 1M-5M, 5M-10M, 10M-25M, 25M-75M, 75M-200M, 200M-500M, 500M-1B, 1B-10B |

### Autocomplete (quirky)

```
GET /v1/businesses/autocomplete?field=city_region_country&prefix=syd
```
**Known issue**: returns default suggestions (Paris, Tel Aviv, New York, Tokyo) regardless of prefix. Don't rely on it for fine-grained location discovery — use country-level filters instead.

### Autocomplete fields available: `city_region_country`, `google_category`, `linkedin_category`, `company_name`, `company_tech_stack_tech`, `job_title`, `company_tech_stack_category`

### Fetch a Known Company (Full Profile) — Best Credit Value

Once you have a `business_id` from the Match endpoint, fetch its full profile with mode=full and a business_id filter:

```
POST /v1/businesses
{"filters": {"business_id": {"values": ["1920a10ce55b09a327f4f1a433385185"]}}, "mode": "full", "page": 1, "page_size": 5}
```
Returns: logo, country, city, employee_range, revenue_range, description, NAICS plus description, SIC, LinkedIn URL, region/state.

**Best credit-to-value ratio** — targeted full fetches on matched companies give you rich data for minimal credits compared to broad stats calls.

### Prospect Search

```
POST /v1/prospects
{"filters": {"job_title": {"values": ["data scientist"]}, "country_code": {"values": ["au"]}}, "mode": "full"}
```
Returns: full_name, job_title, company_name, linkedin_url, email (if enrichment purchased).
Useful for finding hiring managers / team members at target companies.

### Enrichment (costs credits per record)

- **Business enrichments**: funding history, competitive landscape, website traffic, Bombora intent topics, workforce trends, social media
- **Prospect enrichments**: professional emails, phone numbers, LinkedIn posts, social media presence

## Pitfalls (things we hit so you don't have to)

- **`POST /v1/businesses` not `/v1/businesses/fetch`** — the fetch endpoint has no `/fetch` suffix. Adding it gives 404.
- **`businesses_to_match`, not `businesses`** — the match endpoint body key is `businesses_to_match`.
- **`last_occurrence` goes inside `events`** — structure: `"events": {"values": ["hiring_in_engineering_department"], "last_occurrence": 60}`. Putting it alongside events gives a 422.
- **Invalid event type = 422** — check the permitted event types list before querying. `hiring_in_data_analytics_department` does not exist.
- **Autocomplete is GET** — most other endpoints are POST. Using POST on autocomplete gives "Method Not Allowed".
- **Preview mode is sparse** — no description or tech stack. Use full mode for meaningful company intelligence.
- **Autocomplete doesn't prefix-match** — returns hardcoded defaults. Build filters by known values.
- **`google_category` filter can silently zero out results** — combining it with other filters (especially `events`) may return 0 results even when un-filtered data exists. Safer to omit it and use `company_tech_stack_tech` for relevance filtering.
- **City/region filters often return 0** — prefer `country_code` or `region_country_code` when possible.
- **`company_tech_stack_tech` returns global + local** — a US company with a Sydney office matches because it has AU operations, but shows US as country_name. The employee count filter also covers AU headcount. You'll see many global brands; filter further by checking if they have an AU careers page.
- **Events filter requires `last_occurrence`** within the `events` object, not alongside it.
- **Country_name in results = HQ** — a company headquartered in the US but with Sydney operations will show "united states" as country_name. The filter matched their AU operations.
- **Free credits won't yield contact data** — the prospect contact enrichment endpoint (`/v1/prospects/contacts_information/enrich`) returns `"miss"` or `"success"` with null data on free tier. You need a paid plan for actual emails/phones.
- **Rate limit**: 200 queries per minute. Burst safely.

## Workflow for Job Hunting (Credit-Aware Sequence)

0. **Check credits first**: `GET /v1/credits` — if `remaining_credits` is 0, all paid endpoints will fail. Plan accordingly.

1. **Stats call (simple)** — gauge how many companies match country + size filters (minimal credit cost with 1-2 filter dimensions). *Do not add google_category or events to stats — that burns credits fast.*

2. **Business match** — use known company names/domains to get `business_id` values for your target list. Cheap, reliable.

3. **Business fetch (full, by business_id)** — narrow to 10-20 most relevant IDs, get full intelligence. Best credit-to-value ratio.

4. **Business fetch (preview, filtered)** — only if you have remaining credits and need broad discovery. Use simple filters (country + size + tech stack).

5. **Events fetch** — most expensive. Skip unless you have paid credits. Use `POST /v1/businesses/events` with known `business_ids`.

6. **Prospect search / enrichment** — paid tier only. Free tier returns no contact data.
