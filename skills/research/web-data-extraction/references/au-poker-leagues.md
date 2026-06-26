# Australian Pub Poker League — Data Sources

Scraping live poker game schedules from the four major NSW pub poker leagues.

## Leagues & Websites

| League | Website | Tech | Key Endpoint |
|--------|---------|------|-------------|
| APL | playapl.com | React SPA + legacy ASP | `legacy.playapl.com/Events.asp?Action=Search&StateID=3&TID=2` |
| NPL | npl.com.au | Server-rendered + jQuery | `npl.com.au/Events/ListData?startDate=...&endDate=...&lat=0&lng=0&useLoc=0&state=NSW&regionID=0` |
| UPT | uptpoker.com | Classic PHP | Post to `uptpoker.com/gamesearch.php` with `day=Saturday&region=<region>&search=Yes` |
| Crocent | crocent.com.au | Classic PHP | `crocent.com.au/tournylist.php?game=wg` (weekly games) or `crocent.com.au/tourny-details.php?tournyid=<id>` |

## APL (Australian Poker League)

**New site** (playapl.com) is a React SPA — all content loaded client-side, no useful data in curl. React bundle at `/assets/js/bundle.<hash>.js` contains route hints (`/event/searchevents`, `/venues/list`, `/region/list`) but the API base URL is not exposed in the minified bundle.

**Legacy site** (legacy.playapl.com) is the working data source:
- `Events.asp?Action=Search&StateID=3&TID=2` — NSW events for the current week
- `StateID=3` = NSW, `TID=2` = league poker
- Returns server-rendered HTML with event rows in `<tr class="EventsRow_Even/Odd">`
- Events are inside a **scrollable div** (`height: 250px; overflow-y: auto`) — curl gets all rows
- Week selector: `nWeek=0` (this week), `nWeek=1` (next week), etc.
- Day filter: `nDay=0` (Sun) through `nDay=6` (Sat) — **but this limits to 2 events max, don't use it**
- Default view (no nDay) returns ALL events for the week — parse client-side

### Parsing APL events
```python
# Split HTML by date pattern, then extract per-event:
# Date:   >Sat 6 Jun<
# Event:  EventDetails.asp?Action=Detail&ID=...>Event Name
# Venue:  VenueDetails.asp?Action=Detail&ID=...>Venue Name
# Entry:  <div style="width:70px;">$XX.XX</div>
# Rego:   <div style="width:70px;">HH:MM</div>
```

### APL Saturday Sydney events (June 2026 sample)
- **Mounties** (Mt Pritchard) — APL Million satellite, $60 entry, rego 17:00
- **Club Italia Sporting Club** — Saturday Day Game Satellite, $40 entry, rego 14:30
- **Central Coast Leagues Club** — $10,000 GTD June Long Weekend, $100 entry

## NPL (National Poker League)

Best data quality — returns structured HTML with labeled fields (Entry, Rebuy, Addon, Rego Time, Start Time, Guarantee, Poker Type).

**API endpoint:** `/Events/ListData`
```
GET /Events/ListData?startDate=2026-06-06&endDate=2026-06-06&lat=0&lng=0&useLoc=0&state=NSW&regionID=0
```

**Parameters:**
- `startDate` / `endDate` — YYYY-MM-DD format, query range
- `lat` / `lng` — user coordinates (use 0 for no location)
- `useLoc` — 1 to sort by distance from lat/lng, 0 for default sort
- `state` — NSW, QLD, VIC, SA, etc.
- `regionID` — 0 = all regions, specific IDs for sub-regions

**With `useLoc=1`**, events include distance in Km: `(XX.X Km)` after suburb name.

**Data extraction pattern:**
```python
# Split response by date marker: "6th | Jun" (note: ordinal + pipe + month)
# Each event block contains:
#   NSW | <Region> | <VenueName> <Suburb> Entry $XX Rebuy $XX ... Start Time HH:MM
# Parse label-value pairs from <b>Label</b>...<span>value</span> pattern
```

**Azure CDN:** `NPLDataEndpoint-cjg8e4a6ftgkdzba.z03.azurefd.net` — serves logos/images, not API data.

### NPL Saturday Sydney events (sample)
- **Ambarvale Hotel**, Ambarvale — $1,000 GTD Bounty Hunter, $40 entry, rego 6:00 PM, start 7:00 PM
- **Windsor Leagues Club**, South Windsor — $35 entry, rego 4:30 PM, start 5:30 PM

## UPT (Ultimate Poker Tour)

Classic PHP site with form-based search.

**Homepage sidebar** shows current Saturday games as a static list — good for quick lookup:
```html
<div id='sbday'>Saturday Games</div>
<td class='sidebarvenue' onclick='gotogame(ID)'>Venue Name</td>
<td class='sidebartime'>HH:MM</td>
```

**Search endpoint:** POST to `gamesearch.php`
```
POST day=Saturday&region=<Region>&search=Yes
```

**Sydney regions:**
| Region value | Display name |
|-------------|-------------|
| City/Eastern Suburbs | Sydney - City/Eastern Suburbs |
| Inner Western Sydney | Sydney - Inner Western Sydney |
| North Sydney | Sydney - North |
| Outer Western Sydney | Sydney - Outer Western Sydney |
| Sydney City | Sydney City |
| South Western Sydney | Sydney - South West |

**Response:** HTML table with columns: Name, Prize, Start Time, Day, Entry Cost, Rebuy (img tick/cross), Addon (img tick/cross).

### UPT Saturday Sydney events (sample)
- **Avondale Hotel**, Drummoyne — $1,000, 10:30 AM, $35, freezeout
- **Blacktown Tavern**, Blacktown — $1,000, 7:00 PM, $25, addon
- **St Marys Diggers & Band Club**, St Marys — $800, 7:00 PM, $20, addon
- **Nepean Rowing Club**, Penrith — $300, 2:00 PM, $15, freezeout

## Crocent (Crocodile Entertainment)

Classic PHP site. Limited to western Sydney venues.

**Weekly games list:** `tournylist.php?game=wg` — returns upcoming game table with Date, Venue, Suburb, Start Time, Buyin

**Tournament details:** `tourny-details.php?tournyid=<id>` — full info including address, rego/game start, buy-in, chips, add-ons

**Known Saturday tournament IDs:**
- tournyid=61 — Arena Sports Club (Sat), 140 Rookwood Rd Yagoona NSW 2199
- tournyid=62 — Baulkham Hills Sports Club (Sat), 11 Renown Rd Baulkham Hills NSW 2153

### Crocent Saturday events
- **Arena Sports Club**, Yagoona — $20 buy-in, rego 5:30 PM, start 6:00 PM, 30k start, $2 chip up, 3k earlybird
- **Baulkham Hills SC**, Baulkham Hills — $40 entry, rego 5:30 PM, start 6:30 PM, $2,000 GTD, Jackpot Bounty

## Distance Calculation

Granville NSW coordinates: **-33.8314, 151.0027**

Use haversine formula for great-circle distance. Key reference distances from Granville:

| Venue | Suburb | km |
|-------|--------|-----|
| Arena Sports Club | Yagoona | 4.2 |
| Baulkham Hills SC | Baulkham Hills | 7.5 |
| Blacktown Tavern | Blacktown | 10.9 |
| Avondale Hotel | Drummoyne | 14.1 |
| Mounties | Mt Pritchard | 16.3 |
| St Marys Diggers | St Marys | 21.8 |
| Nepean Rowing Club | Penrith | 30.9 |
| Ambarvale Hotel | Ambarvale | 31.0 |
| Windsor Leagues Club | S. Windsor | 34.7 |
| Central Coast LC | Gosford | 54.7 |

## Common Pitfall: Timezone/Date Confusion

**Australian dates in API responses use AEST (UTC+10).** When querying from UTC-based systems:
- The conversation timestamp "Saturday, June 06, 2026 02:08 AM" is UTC
- In AEST this is **Saturday June 6 at 12:08 PM** — so "today" for a Sydney user is Saturday June 6
- Calendar verification: `datetime.date(2026, 6, 6).strftime('%A')` = **Saturday** ✓
- NPL API dates are in YYYY-MM-DD — use the **AEST date**, not UTC date
- APL legacy page shows local dates (Sat 6 Jun = Saturday in AEST)
- **Always verify the day-of-week** with Python `datetime` before querying APIs — don't assume the system timestamp's date matches the user's local date

## Non-Sydney Venues to Filter Out

APL and NPL return events across all NSW. Filter out these distant regions:
- Riverina (Griffith, Temora, Lake Mulwala) — 400+ km
- Far North Coast (Ocean Shores) — 600+ km
- Mid North Coast (Narrabri) — 400+ km
- Far South Coast (Batemans Bay, Moruya) — 250+ km
- Wollongong/Albion Park — 80+ km (borderline, include only if user wants wide range)
- South Coast (Nowra, Shoalhaven) — 100+ km
