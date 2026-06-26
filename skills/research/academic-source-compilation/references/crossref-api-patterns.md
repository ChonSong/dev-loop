# Crossref API Patterns

Verified patterns for bibliographic metadata retrieval from Crossref's public API.

## Core Function

```python
import urllib.request, json

def crossref_get(url):
    req = urllib.request.Request(url, headers={
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (research; mailto:research@example.com)"
    })
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())
```

## By DOI

```python
data = crossref_get("https://api.crossref.org/works/10.1080/09650792.2013.856771")
msg = data["message"]
# title and container-title are ALWAYS lists — always [0]
title = msg["title"][0]
journal = msg["container-title"][0]
# authors — each is a dict with given/family
authors = [f"{a['given']} {a['family']}" for a in msg["author"]]
year_obj = msg.get("published-print") or msg.get("published-online") or {}
year = year_obj.get("date-parts", [[None]])[0][0]
volume = msg.get("volume", "N/A")
issue = msg.get("issue", "N/A")
pages = msg.get("page", "N/A")
doi = msg["DOI"]
```

## By ISBN

```python
data = crossref_get("https://api.crossref.org/works?filter=isbn:9781315456539&rows=3")
# Returns list of items — extract first match
items = data["message"]["items"]
```

## By Title Query

```python
data = crossref_get(
    "https://api.crossref.org/works?query-title=Research+Methods+Education+Cohen&rows=5"
)
items = data["message"]["items"]
for item in items:
    t = item["title"][0]  # ALWAYS list
    authors = [f"{a['given']} {a['family']}" for a in item["author"]]
```

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `HTTP 400` | Invalid query format | URL-encode spaces as `+`; use `query-title=` not `query=` |
| Empty result | Crossref doesn't have it | Try ISBN search; fallback to manual |
| `title` is list | Crossref always wraps in list | Always `msg["title"][0]`, never `msg["title"]` directly |

## APA7 Field Mapping

From Crossref response to APA7 fields:
- `msg["title"][0]` → title
- `msg["author"]` → list of `{given, family}` → `Family, G.` format
- `msg.get("published-print") or msg.get("published-online")` → year
- `msg["container-title"][0]` → journal name
- `msg["volume"]` + `msg["issue"]` → volume(issue)
- `msg["page"]` → pages
- `msg["DOI"]` → DOI (clean, no URL encoding needed)

## Special Characters in DOIs

Some DOIs contain angle brackets and special chars:
```
10.1002/1098-2736(200102)38:2<137::aid-tea1001>3.0.co;2-u
```
Use raw (unencoded) DOI in URL — Crossref handles it fine.
For display/linking, URL-encode only the query string portion: `https://doi.org/10.1002/1098-2736%28200102%2938%3A2%3C137%3A%3Aaid-tea1001%3E3.0.co%3B2-u`