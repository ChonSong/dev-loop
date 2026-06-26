# API Endpoints & Parsing Patterns

## NPL

### Fetch today's events
```bash
curl -sL 'https://www.npl.com.au/Events/ListData?startDate=2026-06-07&endDate=2026-06-07&lat=-33.8314&lng=151.0027&useLoc=1&state=NSW&regionID=0'
```

### Parse (Python)
```python
import re

text = re.sub(r'<br\s*/?>', ' | ', html)
text = re.sub(r'<[^>]+>', ' ', text)
text = re.sub(r'\s+', ' ', text)

# Split by date
sections = text.split('7th | Jun')
for section in sections[1:]:
    # Extract: NSW | {region} | {venue} {suburb} ... Entry $XX ... Start Time H:MM PM ...
    region_match = re.search(r'NSW\s*\|\s*([^|]+?)\s*\|\s*', section[:200])
    venue_match = re.search(r'^([A-Za-z][A-Za-z\s\-\'&]+?(?:RSL|Hotel|Club|Tavern|Workers|Leagues))', section[region_match.end():region_match.end()+200])
```

### Label-value extraction
```python
labels = re.findall(r'<b>([^<]+)</b>.*?<span[^>]*>\s*([^<]+)', block[:4000], re.DOTALL)
# Yields: ('Entry', '$15.00'), ('Start Time', '5:00 PM'), etc.
```

## UPT

### Fetch Saturday Sydney games by region
```bash
curl -sL 'https://www.uptpoker.com/gamesearch.php' -d 'day=Saturday&region=Outer+Western+Sydney&search=Yes'
```

### Parse results table
```python
# Table rows: <tr><td>Name</td><td>Prize</td><td>Start Time</td><td>Day</td><td>Entry Cost</td><td>Rebuy</td><td>Addon</td></tr>
rows = re.findall(r"<tr><td>([^<]+)</td><td>([^<]+)</td><td>([^<]+)</td><td>([^<]+)</td><td>([^<]+)</td>", html)
```

### Homepage sidebar (quick today's games)
```python
sidebar = re.findall(r"sidebarvenue[^>]*>([^<]+)</td>.*?sidebartime[^>]*>([^<]+)<", html, re.DOTALL)
```

## Crocent

### Weekly games list
```bash
curl -sL 'https://www.crocent.com.au/tournylist.php?game=wg'
```

### Tournament detail (full info)
```bash
curl -sL 'https://www.crocent.com.au/tourny-details.php?tournyid=61'  # Arena Sports Sat
curl -sL 'https://www.crocent.com.au/tourny-details.php?tournyid=62'  # Baulkham Hills Sat
```

### Parse upcoming table
```python
# <tr><td>Date</td><td><a href="tourny-details.php?tournyid=X">Venue</a></td><td>Suburb</td><td>Start Time</td><td>Buyin</td></tr>
rows = re.findall(r'<td[^>]*>([^<]+)</td>\s*<td[^>]*><a[^>]+>([^<]+)</a>.*?<td[^>]*>([^<]+)</td>\s*<td[^>]*>([^<]+)</td>\s*<td[^>]*>([^<]+)</td>', html, re.DOTALL)
```

## Haversine Distance
```python
import math

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))
```

Granville coordinates: -33.8314, 151.0027
