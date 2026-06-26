# AU Company Research — URL Patterns & Extraction Recipes

## Google News (article discovery)
```
https://news.google.com/search?q={query}&hl=en-AU&gl=AU&ceid=AU:en
```
- Article titles embedded in raw HTML, extractable via regex
- JS-heavy page but titles are in the initial HTML response
- Use `>([^<]*{keyword}[^<]*)<` pattern to extract relevant lines

## ASX Announcements (official filings)
```
https://www.asx.com.au/asx/v2/statistics/announcements.do?by=asxCode&asxCode={CODE}&timeframe=D&period=M
```
- Server-rendered HTML table
- Columns: Date, Time, Headline, Pages, File size
- Replace `{CODE}` with 3-letter ASX ticker (e.g., MTS, COL, WOW)
- `timeframe=D&period=M` = past month; `period=Y` = past year

## Wikipedia (company overview)
```
https://en.wikipedia.org/wiki/{CompanyName}
```
- Extract from `<div id="mw-content-text">` div
- Strip HTML tags → clean text
- Best for: history, operations, key people, financials summary

## Known-Broken Sources (don't waste time)
| Source | Issue |
|--------|-------|
| DuckDuckGo HTML | Returns CAPTCHA challenge |
| Bing search | JS-rendered, no useful text in raw HTML |
| Most .com.au corporate sites | JS-rendered SPAs, curl returns empty body |
| WordPress REST API | Often disabled or returns empty |

## Metcash-Specific
- Website: JS-rendered WordPress, no content via curl
- Wikipedia: Full article with history, operations, ALM details
- ASX code: MTS
- Google News: Rich coverage of FY25/FY26 results, ALM growth, acquisitions
- Key search terms: "Metcash", "Australian Liquor Marketers", "ALM", "ASX:MTS"
