---
name: sydney-pub-poker
description: "Find today's live pub poker games in Sydney from NPL, UPT, Crocent (Crocodile Entertainment), and APL. Covers API endpoints, HTML parsing patterns, region IDs, and distance calculation from a given suburb."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [poker, sydney, npl, upt, crocent, apl, pub-poker, events]
    track: lifestyle
---

# Sydney Pub Poker — Find Tonight's Games

Scrape the four major Sydney pub poker leagues for today's games, compute distances from a given suburb, and present a sorted table.

## The Four Leagues

| League | Website | Status (June 2026) | Data Access |
|--------|---------|---------------------|-------------|
| **NPL** (National Poker League) | https://www.npl.com.au | ✅ Active | Server-rendered HTML via jQuery `$.get()` |
| **UPT** (Ultimate Poker Tour) | https://www.uptpoker.com | ✅ Active | Raw HTML, POST form on `gamesearch.php` |
| **Crocent** (Crocodile Entertainment) | https://www.crocent.com.au | ✅ Active | Raw HTML, `tournylist.php?game=wg` + `tourny-details.php` |
| **APL** (Australian Poker League) | https://www.aplpoker.com.au | ❌ All domains parked/inactive | N/A |

## NPL — Data Extraction

### API Endpoint
```
GET https://www.npl.com.au/Events/ListData?startDate=YYYY-MM-DD&endDate=YYYY-MM-DD&lat=0&lng=0&useLoc=0&state=NSW&regionID=0
```

- Use `useLoc=1` + your lat/lng to get distance-sorted results (distances appear in venue names like `(235.3 Km)`)
- `state=NSW` for Sydney
- `regionID=0` = all regions; see region IDs below

### Region IDs (NSW)
| ID | Region |
|----|--------|
| 0 | All |
| 5 | South Coast |
| 6 | Far North Coast |
| 7 | Mid North Coast |
| 21 | Wollongong |

Sydney-area regions (Inner West, City, South West, Hills, etc.) return few or no Saturday events in winter — most NPL Sydney action is Thu/Fri.

### HTML Structure
- Each event is a `<tr>` with `onclick="window.location='/Events/Detail/{id}/{gameId}'"`
- Venue name in `<h5>` after `NSW<br />{Region}<br />`
- Suburb as plain text right after `</h5>` of venue name
- Key-value pairs: `<b>Entry</b>`, `<b>Start Time</b>`, `<b>Rego Time</b>`, `<b>Rebuy</b>`, `<b>Addon</b>`, `<b>Guarantee</b>`, `<b>Poker Type</b>` each in `<span class="latest-comments-date">`
- Azure CDN at `NPLDataEndpoint-cjg8e4a6ftgkdzba.z03.azurefd.net` (serves logos, images — not event data)

### Parsing Strategy
Strip HTML to text (`re.sub(r'<[^>]+>', ' ', html)`) then match patterns like:
- `NSW | {region} | {venue} {suburb} Entry $XX.XX ... Start Time H:MM PM ...`

## UPT — Data Extraction

### Game Search (POST)
```
POST https://www.uptpoker.com/gamesearch.php
  day=Saturday&region={region}&search=Yes
```

### Sydney Region Values
| Region param | Description |
|-------------|-------------|
| `City/Eastern Suburbs` | Sydney CBD, Darlinghurst, Woolloomooloo |
| `Inner Western Sydney` | Drummoyne, Ashfield, Burwood |
| `North Sydney` | North Shore, Northern Beaches |
| `Outer Western Sydney` | Blacktown, St Marys, Penrith |
| `Sydney City` | CBD |
| `South Western Sydney` | Liverpool, Campbelltown |

### Homepage Sidebar
The homepage (`index.php`) has a sidebar with today's day games:
```html
<div id='sbday'>Saturday Games</div>
<tr class='sidebartr'>
  <td class='sidebarvenue' onclick='gotogame(2775)'>Avondale Hotel</td>
  <td class='sidebartime'><div onclick='gotogame(2775)'>10:30</div></td>
</tr>
```

### Table Structure (search results)
```html
<tr><th>Name</th><th>Prize</th><th>Start Time</th><th>Day</th><th>Entry Cost</th><th>Rebuy</th><th>Addon</th></tr>
```
- Rebuy/Addon columns: `<img src='tick.png'>` or `<img src='cross.png'>`

## Crocent — Data Extraction

### Upcoming Games List
```
GET https://www.crocent.com.au/tournylist.php?game=wg
```

### Table Structure
```html
<tr>
  <td>Date</td>         <!-- "Sun 07 Jun" -->
  <td><a href="tourny-details.php?tournyid=59">Venue Name</a></td>
  <td>Suburb</td>
  <td>Start Time</td>  <!-- "5:00pm" -->
  <td>Buyin</td>        <!-- "$10" -->
</tr>
```

- Sidebar lists weekly recurring games: `Arena Sports Club (Sat)` → `tourny-details.php?tournyid=61`
- Tournament detail pages have full info: address, rego time, buy-in, stack size, chip-up, late rego

### Known Saturday Venues (Crocent)
| Venue | Suburb | Address | Rego | Start | Buy-in |
|-------|--------|---------|------|-------|--------|
| Arena Sports Club | Yagoona | 140 Rookwood Rd, 2199 | 5:30 PM | 6:00 PM | $20 (30k start, $2 chip up, 3k earlybird) |
| Baulkham Hills Sports Club | Baulkham Hills | 11 Renown Rd, 2153 | 5:30 PM | 6:30 PM | $40 (30k stack, $2 20k chip up, $2k GTD, Jackpot Bounty, late rego ~9:10 PM) |

## Distance Calculation

Use haversine from Granville (-33.8314, 151.0027) or the user's requested suburb. Key venue coordinates:

| Venue | Lat | Lng |
|-------|-----|-----|
| Arena Sports Club (Yagoona) | -33.8653 | 151.0231 |
| Baulkham Hills SC | -33.7636 | 150.9992 |
| Blacktown Tavern | -33.7719 | 150.9087 |
| Avondale Hotel (Drummoyne) | -33.8284 | 151.1558 |
| St Marys Diggers | -33.7900 | 150.7725 |
| Nepean Rowing Club (Penrith) | -33.7500 | 150.6833 |
| Windsor Leagues Club | -33.6086 | 150.8198 |
| Ambarvale Hotel | -34.0520 | 150.7970 |
| Albion Park RSL | -34.5667 | 150.7833 |

## Output Format

Present as a Markdown table sorted by distance:

```
| km | League | Time | Venue, Suburb | Entry | Prize/Notes |
|----|--------|------|---------------|-------|-------------|
| 4.2 | Crocent | 6:00 PM | Arena Sports Club, Yagoona | $20 | 30k start, $2 chip up |
```

## Key Findings (June 2026)

- **Saturday is the lightest day** for NPL Sydney — most NPL Sydney pub games run Thu/Fri. Saturday NPL events skew regional (Wollongong, Macarthur, Hawkesbury, Riverina).
- **Crocent** has the closest Saturday games to Granville: Arena Sports Club (4.2 km) and Baulkham Hills SC (7.5 km) — both around 6 PM.
- **UPT** Saturday is mostly Outer Western Sydney: Blacktown, St Marys, Penrith.
- **APL** is offline (all domains parked). Historical only.

## Pitfalls

1. **NPL is JS-heavy** — `curl` the `/Events/ListData` endpoint directly, not the page HTML. The page uses jQuery `$.get()` to fetch ListData.
2. **UPT region values have spaces** — URL-encode them in POST: `region=Outer+Western+Sydney`.
3. **Crocent table dates** don't always show Saturday — the weekly recurring games are only listed in the sidebar links, not in the tournylist table (which shows upcoming one-off dates).
4. **NPL regionID=0 with useLoc=1** sorts by distance but returns ALL NSW — filter in post-processing for Sydney metro (< ~100 km from Granville).
5. **UPT homepage sidebar** shows today's day games but without region info — use `gamesearch.php` POST for full details.

---

*Last updated: 2026-06-07*
