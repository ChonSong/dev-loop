---
name: facebook-marketplace
title: Facebook Marketplace Search
description: >-
  Search Facebook Marketplace for live listings by query, city slug, category,
  price range, condition, radius, delivery method, sort order, plus
  vehicle/apparel/rental sub-filters — and resolve single
  /marketplace/item/<id>/ URLs — returning normalized JSON. Read-only.
source: browserbase/browse.sh
updated: '2026-05-18'
---

# Facebook Marketplace Search

## Purpose

Search Facebook Marketplace for live listings matching a query, category, location, and the full Marketplace filter surface (price, condition, radius, date listed, delivery method, sort order, plus vehicle / apparel / rental sub-filters), and return them as structured JSON. Also resolves a single `/marketplace/item/<id>/` URL to a normalized listing record. **Read-only — never clicks Message, Make Offer, Save, Share, Report, or any other mutation control.**

## Prerequisites

- `browse` CLI: `npm install -g browse` (binary at `~/.hermes/node/bin/browse` — add to PATH)
- `bb` (Browserbase CLI) installed and authenticated
- `BROWSERBASE_API_KEY` set in `~/.hermes/.env` (see `hermes-credential-setup` skill for how to add it)
- `jq` installed

**Note**: The `browse` binary installs to `~/.hermes/node/bin/browse`. Always use `export PATH="/home/hermeswebui/.hermes/node/bin:$PATH"` before running `browse` commands, or use the full path.

## When to Use

- Local-buying agents ("find me a used Peloton under $500 within 20mi of Austin, listed in the last 7 days").
- Cross-region price comparison ("median asking price for a 2018-2022 Ford F-150 across NYC, Chicago, LA").
- Inventory monitoring against a saved search (poll for new listings matching a query + filter set).
- Resolving a single `/marketplace/item/<id>/` URL pasted by a user into a normalized listing object.
- Bulk extraction across multiple metros.

## Workflow

### 1. Create a Verified + residential-proxy session

```bash
export PATH="/home/hermeswebui/.hermes/node/bin:$PATH"
SID=$(bb sessions create --keep-alive --verified --proxies | jq -r '.id')
export BROWSE_SESSION="$SID"
```

Both `--verified` and `--proxies` are mandatory. A bare session gets a logged-out splash or empty results.

### 2. Resolve the input shape

| Input | Action |
|---|---|
| Full `/marketplace/<loc>/search/?...` URL | Use as-is. Skip to step 4. |
| Direct `/marketplace/item/<id>/` URL | Skip search; jump to step 8 (single-item resolver). |
| Free-form "Q in {City, ST}" or "Q near {ZIP}" | Resolve city slug (step 3), then build search URL (step 4). |
| Category browse ("Vehicles in Boston") | Resolve city slug, then build search URL. |

### 3. Resolve the city slug

The URL accepts **only Facebook's canonical city slug** — not ZIP, not numeric ID, not free-form names.

Known-good slugs:

| Metro | Slug |
|---|---|
| New York City | `nyc` |
| Los Angeles | `la` |
| San Francisco / Bay Area | `sanfrancisco` |
| Chicago | `chicago` |
| Austin | `austin` |
| Boston | `boston` |
| Seattle | `seattle` |
| Atlanta | `atlanta` |
| Miami | `miami` |
| Portland | `portland` |

**Invalid slugs** (302 to IP-geo default): `newyork`, `losangeles`, `bayarea`, `sf`, `san-francisco`, `new-york`, ZIPs, numeric IDs.

### 4. Build the search URL

Base: `https://www.facebook.com/marketplace/<slug>/search/?query=<urlenc-query>`

Filter params:

| Filter | URL param | Values |
|---|---|---|
| Min price | `minPrice` | integer |
| Max price | `maxPrice` | integer |
| Days since listed | `daysSinceListed` | `1`, `7`, `30` |
| Condition | `itemCondition` | `new`, `used_like_new`, `used_good`, `used_fair` |
| Availability | `availability` | `in stock`, `out of stock`, `all` |
| Delivery | `deliveryMethod` | `local_pick_up`, `shipping` |
| Radius (miles) | `radius` | `1`, `2`, `5`, `10`, `20`, `40`, `60`, `80`, `100`, `250`, `500` (default 40mi) |
| Sort | `sortBy` | `creation_time_descend`, `distance_ascend`, `price_ascend`, `price_descend` |
| Category | `category` | `vehicles`, `propertyrentals`, `apparel`, `electronics`, `family`, `free`, `garden`, `hobbies`, `home`, `homeimprovement`, `musicalinstruments`, `officesupplies`, `petsupplies`, `sportinggoods`, `toys`, `bookmoviesmusic` |

Vehicle sub-filters: `make`, `model`, `carType`, `transmissionType`, `minYear`, `maxYear`, `minMileage`, `maxMileage`, `vehicleExteriorColors`, `vehicleInteriorColors`, `titleStatus`

Rental sub-filters: `minBedrooms`, `maxBedrooms`, `minBathrooms`, `maxBathrooms`, `minAreaSize`, `maxAreaSize`, `propertyType`, `privateRoomBathroomType`

### 5. Navigate + extract first-page SSR payload

```bash
browse --connect "$SID" open "$URL"
browse --connect "$SID" wait load
browse --connect "$SID" wait timeout 2000
HTML=$(browse --connect "$SID" get html body)
```

Extract the SSR JSON from the `<script>` tag containing `"marketplace_search":{"feed_units":{"edges":[...]}}`. First page = ~15 listings.

Key fields: `listing.id`, `listing.marketplace_listing_title`, `listing.listing_price`, `listing.location.reverse_geocode`, `listing.primary_listing_photo.image.uri`, `listing.delivery_types`, `listing.is_sold`, `listing.is_pending`.

### 6. Paginate (pages 2+)

```bash
browse --connect "$SID" eval "window.scrollTo(0, document.body.scrollHeight)"
browse --connect "$SID" wait timeout 1500
```

Each scroll adds ~24 more edges. Read appended cards from DOM (`<div role="article">` with `/marketplace/item/<id>/` anchors).

### 7. Login interstitial detection

After ~5–10 cursor pages, FB may show a login wall. Detect via `"login_form"` in HTML or "Log in to see more" text. Return partial results with `partial: true, partial_reason: "login_required_after_page_N"`.

### 8. Single-item resolver

```bash
browse --connect "$SID" open "https://www.facebook.com/marketplace/item/<id>/"
browse --connect "$SID" wait load
browse --connect "$SID" wait timeout 2500
HTML=$(browse --connect "$SID" get html body)
```

Parse `marketplace_listing_renderable` from SSR JSON for full details: description, photos, seller, location, condition, custom_attributes.

### 9. Release session

```bash
bb sessions update "$SID" --status REQUEST_RELEASE
```

## Gotchas

- `--verified --proxies` is mandatory — bare sessions get empty results
- City slugs only — ZIPs and numeric IDs silently redirect to IP-geo default
- `/marketplace/category/search/` is NOT location-locked
- `radius` is in miles in URL, km internally
- GraphQL cursors are session-bound — can't replay across sessions
- Login wall after ~5-10 pages on non-authed sessions
- Image CDN URLs are signed and expire (~24h)
- `delivery_types` may omit SHIPPING in search results — verify on item-detail
- No public Marketplace API exists
- Marketplace unavailable in CN, KP, IR, RU

## Expected Output

Returns JSON with `query`, `city_slug`, `applied_filters`, `result_count`, `partial`, `listings[]` (each with `listing_id`, `title`, `price`, `location`, `primary_photo_url`, `delivery_methods`, `is_sold`, `url`, and optionally `vehicle`, `apparel`, `rental` sub-objects). Single-item mode returns `{"single_item": true, "listing": {...}}`. Errors return `{"error": "...", "reason": "..."}`.
