# DOI Verification Log — Crossref API Quirks & Patterns

## Discovered Through Session

### Field Structure (Critical)
- `title`, `author`, `container-title` are **always lists**, even for single-author works.
  ```python
  title = msg.get('title', ['N/A'])[0]  # always index [0]
  ```
  NOT `msg.get('title', 'N/A')` — this will return a list, not a string.

- Same for `author`:
  ```python
  authors = msg.get('author', [])
  # [ {'given': 'Nicole', 'family': 'Mockler'}, ... ]
  ```

### Year Fields
- Check `published-print` first, then `published-online`. Either may be null.
- Both return `{'date-parts': [[YYYY, M, D]]}` — use `[0][0]` for the year integer.
- Some entries have `null` for date-parts; fall back to `'N/A'`.

### Special Character DOIs
Some DOIs contain brackets, colons, semicolons — common in older journal articles:
```
10.1002/1098-2736(200102)38:2<137::aid-tea1001>3.0.co;2-u
```
- urllib handles URL encoding automatically when you use `urllib.parse.quote(doi, safe='')`
- curl to Crossref works fine with these raw DOIs
- Do NOT strip or pre-process — the API accepts them as-is

### Publisher Blocks (Cloudflare)
Taylor & Francis (`tandfonline.com`), SAGE (`sagepub.com`), Elsevier — all return Cloudflare JavaScript challenge pages to curl.

**Solution:** Always extract DOI from URL and query Crossref by DOI instead.
- `https://www.tandfonline.com/doi/full/10.1080/09650792.2013.856771` → DOI = `10.1080/09650792.2013.856771`
- Crossref API works with no blocking.

### SAGE Book Chapter URL Pattern
```
https://methods.sagepub.com/book/mono/quantitative-research-in-education/chpt/concepts-variables-research-problems
                                              └──────────────────────────────────┘
                                              Book DOI suffix: 10.4135/9781446263181
```
Search Crossref by the book ISBN: `9781847873279` → returns Stephen Gorard (2008).

### YouTube Metadata
YouTube embeds JSON-LD in the HTML page. Always use:
```
User-Agent: Mozilla/5.0
```
Fields to extract via grep:
- `"title":"..."` — video title
- `"ownerChannelName":"..."` — channel name
- `"uploadDate":"..."` — ISO date (e.g., `2013-09-11T08:20:43-07:00`)

### Crossref Search (No DOI)
When only a title is available, use:
```
https://api.crossref.org/works?query={encoded_title}&rows=5
```
Filter results by title substring match. Check `container-title` (journal name) as additional filter.

### ISBN Lookup
For books, Crossref search by ISBN works reliably:
```
https://api.crossref.org/works?query=9781847873279
```
Returns the full book record including all authors.

### Author Name Formatting
| Style | APA7 |
|-------|------|
| Single author | `Family, A.` |
| Two authors | `Family1, A., & Family2, B.` |
| 3–20 authors | `Family1, A., Family2, B., & Family3, C.` |
| >20 authors | First 19 + `...` + last |

### Verified YouTube Videos (curl extraction)

| Title | Channel | Upload Date | Notes |
|-------|---------|-------------|-------|
| Demo qualitative interview with mistakes | Joanna Chrzanowska | 2014-07-09 | URL: https://youtu.be/U4UKwd0KExc |
| What makes a good interview? — Advanced qualitative methods | University of Derby | 2013-09-11 | URL: https://youtu.be/LPwO-vOVxD4 |

**YouTube grep fields:**
```
curl -sL "https://youtu.be/{video_id}" -A "Mozilla/5.0" | grep -o '"title":"[^"]*"' | head -1
curl -sL "https://youtu.be/{video_id}" -A "Mozilla/5.0" | grep -o '"ownerChannelName":"[^"]*"' | head -1
curl -sL "https://youtu.be/{video_id}" -A "Mozilla/5.0" | grep -o '"uploadDate":"[^"]*"' | head -1
```
**Duration note:** YouTube oEmbed API does not return `duration`. Accept "duration unknown" for video entries.

### Verified DOIs from Session

| Source | DOI | Notes |
|--------|-----|-------|
| Mockler (2014) Educational Action Research | `10.1080/09650792.2013.856771` | Year 2014 per volume, published online 2013 |
| Gorard (2008) Quantitative Research in Education | `10.4135/9781446263181` | Book; also ISBN `9781847873279` |
| Brown & Melear (2006) JRST | `10.1002/tea.20110` | Volume 43, Issue 9 |
| Friedrichsen et al. (2011) Science Education | `10.1002/sce.20428` | Volume 95, Issue 2 |
| Ford (1992) Motivating Humans | `10.4135/9781483325361` | SAGE book |
| Van Driel et al. (2001) JRST | `10.1002/1098-2736(200102)38:2<137::aid-tea1001>3.0.co;2-u` | Special chars in DOI — use as-is |
| Sickel & Friedrichsen (2015) School Science and Mathematics | `10.1111/ssm.12102` | Volume 115, Issue 2 |