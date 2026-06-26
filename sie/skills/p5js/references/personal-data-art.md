# Personal Data as Generative Art — p5.js Extension

This reference extends the p5.js production pipeline for personal data visualization (browsing history, location history, listening history, app usage, etc.).

## When to Use

Use this reference when the user wants to transform personal data exports (Google Takeout, browser cookies, API exports) into generative art using p5.js. This requires a **data pipeline phase** before any art code.

## Data Pipeline (Python, before any p5.js)

### 1. Source Identification

- **Google Takeout** — `History.json` (browsing), `Location History.json`, YouTube, etc.
  - Download from takeout.google.com → deselect all → Chrome → History (JSON)
- **Browser cookies** — SQLite DB at `Default/Cookies` (domains + last access only, no titles)
- **API exports** — Spotify, GitHub, Strava, etc.
- **Local files** — CSV, JSON, SQLite

### 2. Parse & Normalize

```python
from urllib.parse import urlparse
from datetime import datetime

domain = urlparse(url).netloc.replace("www.", "")
dt = datetime.fromtimestamp(time_usec / 1_000_000)
# Output per record: {domain, url, title, time, hour, weekday, date, transition}
```

### 3. Categorize (regex, first match wins)

| Category | Patterns |
|----------|----------|
| Social | twitter, x.com, facebook, instagram, reddit, discord, tiktok, linkedin, mastodon, bsky, threads |
| Dev | github, gitlab, stackoverflow, npmjs, pypi, docker, localhost, vercel, netlify, heroku, railway, fly.io, supabase |
| News | bbc, cnn, nytimes, theguardian, reuters, washingtonpost, news.ycombinator, huffpost, axios, bloomberg, ft.com, wsj |
| Shopping | amazon, ebay, etsy, aliexpress, shopify, taobao, walmart, target, bestbuy, wayfair |
| Entertainment | youtube, youtu.be, netflix, spotify, twitch, steam, hulu, disneyplus, hbomax, soundcloud, vimeo |
| Finance | coinbase, binance, robinhood, paypal, stripe, chase, wellsfargo, bankofamerica, wise, revolut, crypto, etherscan |
| Education | coursera, edx, khanacademy, wikipedia, scholar.google, udemy, skillshare, brilliant, mit.edu, ocw.mit |
| Travel | booking.com, airbnb, expedia, tripadvisor, google.com/maps, rome2rio, kayak, skyscanner, hostelworld |
| Search | google.com/search, bing, duckduckgo, ecosia, yahoo.com/search |
| Other | everything else |

### 4. Enrich

For each unique domain:
- Visit frequency, first_seen, last_seen, hour distribution
- Favicon color: fetch `https://www.google.com/s2/favicons?domain=X&sz=64`, extract dominant color via Pillow
- Session clustering: group visits with <30-min gap
- Co-occurrence links: domains appearing in same session

### 5. Output Unified JSON

All art scripts consume this single file:

```json
{
  "nodes": [
    {
      "id": "github.com",
      "category": "dev",
      "count": 342,
      "color": "#24292e",
      "first": "2024-01-15",
      "titles": ["my-repo", "issue #42"]
    }
  ],
  "links": [
    {"source": "github.com", "target": "stackoverflow.com", "weight": 12}
  ],
  "meta": {
    "total_visits": 50000,
    "domain_count": 847,
    "date_range": ["2024-01-01", "2025-06-07"]
  }
}
```

## Art Generation (p5.js, consuming the JSON)

### Layout Patterns

**Temporal Rings:**
- Center = oldest visits, edge = newest
- Categories as angular segments (2π / N_categories)
- Radius = time, Node size = log(visit_count)
- Bezier connections between related domains
- Offscreen layers: bg (gradient+noise), connections, nodes, labels

**Flow Field Particles:**
- Each visit = a particle
- Curl noise for organic orbital drift
- Category = color, Visit count = size
- Trail history fades
- Use pixel buffer for 10k+ particles

**Pixel Mosaic:**
- Each domain = a tile
- Bin-pack by visit count (shelf algorithm)
- Color from favicon dominant color
- Grid with 1px dark gaps

**Force-directed Graph (D3.js):**
- Domains as nodes, co-occurrence as links
- Cluster by category
- Hover tooltip: domain, count, top pages, time range

## Multi-Style Planning Pattern

1. One shared DESIGN.md (use `design-md` skill format)
2. Output matrix: each style × each format (static PNG + MP4 animation + interactive HTML)
3. Build data pipeline once, all styles consume same JSON
4. Iterate on primary style first
5. Quality gate: first-render excellence, structure, resolution, color, performance

## Pitfalls

- **Don't skip the data pipeline** — Raw Takeout JSON is messy. Parse, clean, enrich first.
- **Don't hardcode domain lists** — Data drives everything. Every person's art looks different.
- **Don't show everything** — Top 50-200 domains. 5000+ = noise.
- **Don't forget seeded randomness** — `randomSeed()` + `noiseSeed()` always.
- **Don't ignore performance** — 100k+ visits needs pixel buffers, not `ellipse()`.
- **Don't use Math.random() for visual elements** — Only `random()` for visual content.

## Category Color Mapping

| Category | Color | Hex |
|----------|-------|-----|
| Social | Coral | #f87171 |
| Dev | Emerald | #34d399 |
| News | Amber | #fbbf24 |
| Shopping | Sky Blue | #38bdf8 |
| Entertainment | Fuchsia | #e879f9 |
| Finance | Green | #4ade80 |
| Education | Blue | #60a5fa |
| Travel | Orange | #fb923c |
| Search | Violet | #a78bfa |
| Other | Gray | #9ca3af |
