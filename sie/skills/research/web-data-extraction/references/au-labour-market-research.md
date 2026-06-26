# Australian Labour Market Research — Sources & Patterns

Sources and extraction techniques for researching the Australian job market, hiring trends, and industry data.

## Reliable Sources (Server-Rendered HTML — Work with Plain curl)

| Source | URL Pattern | Content | Extraction |
|--------|-------------|---------|------------|
| **Indeed Hiring Lab** | `hiringlab.org/au/blog/...` | Article body in JSON-LD or `<p>` tags | JSON-LD `articleBody` field, or paragraph extraction |
| **Deloitte Employment Forecasts** | `deloitte.com/au/en/.../employment-forecasts.html` | Article text in page body after script/style removal | Strip scripts+styles, extract lines >60 chars |
| **People2People / Frog Recruitment** | `people2people.com.au/regional-market-update/nsw` | Content in base64-encoded JS variable | `base64JsonRowData` → urldecode → b64decode → strip tags |
| **Jobs and Skills Australia** | `jobsandskills.gov.au/publications` | Server-rendered publication listings | Strip scripts+styles, filter to meaningful lines |
| **Hays Jobs Report** | `hays.com.au/industry-insights/jobs-report` | Partial server-rendered content | Extract paragraphs, filter sentences mentioning "demand" |
| **Miller Leith Salary Guide** | `millerleith.com.au/marketing/2026-salary-guide/` | Salary benchmarks and trends | Standard HTML text extraction |
| **WCO Search** | `wcosearch.com/insights/...` | Market update articles | Standard HTML text extraction |
| **Jora** | `au.jora.com/jobs?sp=entry+level&r=sydney` | Job listings in plain HTML; no bot blocking | Filter lines for job titles (capitalised short lines), salary ranges, and duty descriptions |
| **GradAustralia** (partial) | `gradaustralia.com.au/graduate-programs-in-sydney` | Employer names leak through in HTML even though main content is JS-rendered | Extract visible text elements — employer names (Accenture, Capgemini, BHP, CBA, Deloitte, EY, Optiver) appear in `Search Employers` elements |

## Known Limitations (June 2026)

### Job Boards
- **SEEK search pages** (`seek.com.au/...jobs/in-All-Sydney-NSW`) — first curl request may return job count (~1,422 for admin/office in Sydney); subsequent requests trigger bot block with "confirm you are human" interstitial. Use Jora as fallback.
- **SEEK employer/hiring pages** (`seek.com.au/employer/hiring-advice`) — JS-rendered, curl returns no article content
- **GradAustralia** — main listing content is JS-rendered; only partial data (employer names) visible in HTML source. Employer names appear in elements text like "Search Employers" — extract via `re.findall(r'employer[^>]*>([^<]+)', content)`.
- **Jora** — returns plain HTML but search filtering is loose; results mix entry-level with unrelated senior roles. Must filter in Python by keywords and exclude known noise (forklift, warehouse, pick pack).

### Job Boards That Are Fully Blocked
- **SEEK search** — bot-blocked after first request per session
- **APS Jobs** (`apsjobs.gov.au`) — empty/redirect, no content via curl
- **I Work for NSW** (`iworkfor.nsw.gov.au`) — "Enable JavaScript and cookies" interstitial
- **Job Outlook** (`joboutlook.gov.au`) — empty/JS-only

### Search Engines
- **Bing search** — JS-rendered, no useful text in raw HTML
- **DuckDuckGo HTML** — returns CAPTCHA challenge, not usable

### Other
- **Talent International** (`talentinternational.com/blog/...`) — JS-rendered WordPress, curl returns only nav/footer
- **Fair Work Ombudsman** (`fairwork.gov.au/pay-and-wages/pay-guides`) — site restructured, old URLs return 404
- **Robert Half salary guide** (`roberthalf.com/au/en/salary-guide`) — redirects to US site, not usable from AU server

## Market Data Fields to Extract

When researching the job market, these fields commonly appear across sources:

| Field | Sources | Notes |
|-------|---------|-------|
| **Unemployment rate** | ABS via Indeed, Deloitte, JSA | Usually 4.1-4.4% range for 2026 |
| **Employment growth (YoY)** | Indeed, Deloitte | ~1.2% for 2025; forecast ~1.3% for FY25-26 |
| **Job ads / vacancies** | Indeed, ABS, People2People | NSW ~62,900 (highest nationally) |
| **Vacancy rate by sector** | Indeed, ABS | Mining 3.8%, Utilities 2.9%, Finance below historical avg |
| **Wage growth vs inflation** | Indeed, RBA | Wages +3.4%, inflation 3.7% (real wages -6.3% from peak) |
| **Participation rate** | ABS | ~67%, down 0.5pp from peak |
| **AI disruption categories** | Deloitte | 82 AI-disrupted white-collar occupations identified |
| **White-collar growth forecast** | Deloitte | Office-based +1.3% (FY25-26), +1.0% (FY26-27) |
| **Sector-specific vacancy rates** | Indeed | Healthcare, Education, Finance, Mining, Utilities |
| **Recruiter sentiment** | People2People, Frog | % active/passive/hiring/hesitant |

## Multi-Phase Research Workflow (Proven Pattern)

This workflow was validated in June 2026 for researching the Sydney "seated employment" (desk jobs) market from a blank canvas. It generalises to any labour market topic.

### Phase 1 — Discover Sources (3 parallel calls)
```
curl -sL indeed.hiringlab.org/au/blog/...           → USABLE (JSON-LD articleBody)
curl -sL people2people.com.au/regional-market-update/nsw → USABLE (base64-encoded)
curl -sL deloitte.com/au/en/.../employment-forecasts  → USABLE (HTML stripping)
```
DuckDuckGo → CAPTCHA (drop). Bing → JS-only (drop). Always have fallbacks ready.

### Phase 2 — Extract Key Data
Source-by-source in `execute_code`:
- **Indeed**: JSON-LD `articleBody` — full article text, key metrics embedded
- **People2People**: base64 decode via `base64JsonRowData` → UK decode → b64 decode → strip tags
- **Deloitte**: script/style stripping → filter lines >60 chars → extract forecasts

### Phase 3 — Follow-Up
From Phase 2 gaps, spawn additional extraction:
- Hays jobs report (sector-level demand data)
- Miller Leith salary guide (benchmarks)
- WCO Search market update (broader national context)
- Jobs and Skills Australia publications (official projections)

### Phase 4 — Synthesize
Cross-reference and compile into structured document with source attribution and confidence levels.

### Known-Working Data Fields (June 2026)

When extracting from the sources below, these specific metrics are available and have been verified:

| Metric | Value | Source | Extraction |
|--------|-------|--------|------------|
| NSW unemployment | 4.3% | People2People/Frog | `Pariticipation rate` and `Unemployment` in base64 payload |
| NSW job ads | ~62,900 | People2People | `job ad` field in base64 payload (-6% MoM, +2.2% YoY) |
| Active job seekers (NSW) | 58% | People2People | `job seeker` field |
| Passive workers (NSW) | 62% | People2People | `Passive` field |
| Employers hiring (NSW) | 48% | People2People | `hiring` field |
| Hesitant employers | 14% | People2People | `Hesitant` field |
| National vacancy rate | 2.0% (45% above 2010-19 avg) | Indeed (via ABS) | Article body or paragraph extraction |
| Real wages vs peak | -6.3% | Indeed | Article body |
| White-collar growth (FY25-26) | +1.3% (67,300 jobs) | Deloitte | HTML stripping, filter "white" or "office" |
| Gov white-collar (FY25-26) | -1.0% (-37,100) | Deloitte | HTML stripping, filter "government" / "public sector" |
| AI-disrupted occupations growth | 0.5% annual (next 5 yrs) | Deloitte | HTML stripping, filter "AI-disrupted" |
| Job-seeker activity (NSW) | 6% applications-heavy | People2People | `Application` field in base64 payload |
| Job seeker engagement (NSW) | 36% active, 27% inactive | People2People | `Active`, `Inactive` fields in base64 payload |

## Entry-Level Research — Extraction Notes

When researching entry-level / graduate / junior roles, adjust extraction to focus on different signals:

### What to Extract for Entry-Level
- **Salary ranges** — typically $50-80k for Sydney entry-level; capture the lower end of ranges
- **Experience requirements** — look for "no experience required", "training provided", "entry level"
- **Employer names** — for grad programs, extract from GradAustralia elements; for direct entry, extract from Jora listings
- **Skills demanded** — "MS Office" is universal; specific mentions of Salesforce, PowerBI, Canva indicate premium employers

### Entry-Level Signals in Job Listings
```python
# When extracting from Jora or similar, look for:
entry_signals = ['no experience', 'training provided', 'entry level', 'graduate',
                 'junior', 'trainee', 'starting', 'learn on the job']

# Filter out non-desk roles with:
exclude_signals = ['forklift', 'pick pack', 'warehouse', 'driver', 'labourer',
                   'hospitality', 'barista', 'cleaner']
```

### Entry-Level Salary Ranges (Sydney, 2026 — Verified from Hays + Jora)
| Role | Range | Source |
|------|-------|--------|
| Entry admin / reception | $50-65k | Hays + Jora listings |
| Junior accounts / assistant accountant | $60-80k | Hays + Jora |
| Graduate program | $60-80k | GradAustralia + Hays |
| Service desk L1 | $55-65k | Hays |
| Junior project coordinator | $60-75k | Hays |
| Customer service (corporate) | $55-70k | Jora listings |

## Example: End-to-End Research Pipeline

```python
import subprocess, re, html, json, urllib.parse, base64

sources = [
    ("Indeed", "https://www.hiringlab.org/au/blog/2026/01/30/indeed-2026-au-jobs-hiring-trends-report/"),
    ("People2People", "https://www.people2people.com.au/regional-market-update/nsw"),
    ("Deliotte", "https://www.deloitte.com/au/en/about/press-room/deloitte-access-economics-employment-forecasts.html"),
]

for name, url in sources:
    result = subprocess.run(
        ["curl", "-sL", "--max-time", "10", url,
         "-H", "User-Agent: Mozilla/5.0"],
        capture_output=True, text=True, timeout=15
    )
    content = result.stdout

    # Try JSON-LD first
    jsonld = re.findall(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', content, re.DOTALL)
    for block in jsonld:
        try:
            data = json.loads(block)
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and 'articleBody' in item:
                        print(f"[{name}] Found article body via JSON-LD")
                        print(item['articleBody'][:2000])
        except: pass

    # Try base64
    b64 = re.findall(r'base64JsonRowData\s*:\s*[\'"]([^\'"]+)[\'"]', content)
    for m in b64:
        try:
            decoded = base64.b64decode(urllib.parse.unquote(m)).decode()
            text = re.sub(r'<[^>]+>', ' ', decoded)
            text = html.unescape(re.sub(r'\s+', ' ', text)).strip()
            if len(text) > 100:
                print(f"[{name}] Found base64-embedded content")
                print(text[:2000])
        except: pass

    # Fallback: paragraph extraction
    paras = re.findall(r'<p[^>]*>(.*?)</p>', content, re.DOTALL)
    texts = []
    for p in paras:
        t = re.sub(r'<[^>]+>', ' ', p)
        t = html.unescape(re.sub(r'\s+', ' ', t)).strip()
        if len(t) > 80:
            texts.append(t)
    if texts:
        print(f"[{name}] Extracted {len(texts)} paragraphs")
        print('\n'.join(texts[:10]))
```
