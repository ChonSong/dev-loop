# Staticice AU Price Research

Staticice (staticice.com.au) is an Australian price comparison engine that aggregates across major retailers: MSY, PLE, Scorptec, Computer Alliance, Zip & Link, CCPU, Austin Computers, Maco Technology, Mwave, I-Tech, CentreCom.

## Why Staticice Works

- Returns complete HTML via plain HTTP (no JS rendering needed)
- No login or API key required
- Updated daily (timestamps in page: "updated: DD-MM-YYYY")
- Covers the full AU retail market in one query

## Known Retailers on Staticice

| Store | Region | Notes |
|-------|--------|-------|
| MSY | ACT, NSW, QLD, SA, TAS, VIC, WA | National |
| PLE Computers | WA | Perth-based |
| Scorptec | VIC, NSW | Melbourne/Sydney |
| Computer Alliance | VIC | Brisbane-based |
| Zip & Link | NSW | Often cheapest |
| CCPU Computers | NSW | |
| Austin Computers | WA | |
| Maco Technology | NSW | |
| Mwave | National | |
| I-Tech | NSW | |
| CentreCom | VIC | |
| JB Hi-Fi | National | |

## URL Pattern

```
https://www.staticice.com.au/cgi-bin/search.cgi?q={search_query}&spos=1
```

## Extraction Strategy

The HTML uses `<tr>` rows with store names in `<td>` elements. Clean the HTML by removing `<script>` blocks and stripping all tags, then scan line-by-line for `$price` patterns with surrounding context (2-3 lines above for store name and product description).

## Sample: DDR4 3200 2x16GB (32GB Kit) — May 2026

**Cheapest options:**
- $299 — Kingston 32GB Kit (16x2) DDR4 3200 @ Zip & Link
- $379 — Crucial 32GB (2x16GB) 3200 CL22 UDIMM @ MSY
- $399 — Corsair Vengeance LPX 32GB (2x16GB) 3200 C16 @ CCPU
- $399 — Crucial Pro 32GB (2x16GB) DDR4 3200 @ Computer Alliance
- $399 — G.Skill Trident Z RGB 32GB (2x16GB) DDR4 3200 @ PLE / I-Tech
- $419 — G.Skill Aegis 32GB (2x16GB) DDR4 3200 @ PLE / CPL
- $419 — Corsair Vengeance LPX 32GB (2x16) 3200 @ MSY
- $429 — Corsair Vengeance LPX 32GB (2x16) 3200 @ PLE
- $449–459 — G.Skill Trident Z RGB / Neo 32GB DDR4 @ PLE
- $471 — Crucial Pro Series 32GB (2x16) 3200 @ Scorptec
- $509 — Kingston Fury 32GB 3200 CL16 @ Maco Tech

**Single 16GB stick:**
- $169–239 depending on brand/speed

## Sites That DON'T Work With Plain Curl

- Amazon AU (returns JS-dependent page)
- Scorptec (thin client-side rendered)
- PCCaseGear (thin)
- Mwave (returns empty)
- CentreCom (thin)
