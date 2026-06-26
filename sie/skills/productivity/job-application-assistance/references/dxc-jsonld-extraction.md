# DXC Careers JSON-LD Extraction & Workday API Patterns

## Context

DXC Technology's career pages (careers.dxc.com) are JavaScript-rendered single-page applications (Workday-hosted). Raw `curl` fetches return New Relic Browser Agent JavaScript stubs, not job content. Two reliable extraction methods:

---

## Method 1: JSON-LD Structured Data (Preferred)

Modern Workday job postings embed a `<script type="application/ld+json">` tag with a `JobPosting` schema containing the full description, requirements, and eligibility.

### Extraction Command

```bash
curl -sL "https://careers.dxc.com/job/23102930/2027-dxc-technology-graduate-program-australia-macquarie-park-au/?source=DXCCompany-CareerSite" | grep -oP '<script type="application/ld\+json">.*?</script>' | sed 's/<script type="application\/ld+json">//;s/<\/script>//' | python3 -c "
import sys, json, re
raw = sys.stdin.read()
# Strip HTML comments and decode entities
raw = re.sub(r'<!--.*?-->', '', raw, flags=re.DOTALL)
data = json.loads(raw)
# Print key fields
print('Title:', data.get('title'))
print('Location:', data.get('jobLocation', {}).get('address', {}).get('addressLocality'))
print('Description:', data.get('description')[:500])
print('Requirements:', data.get('requirements'))
print('Employment Type:', data.get('employmentType'))
"
```

### Parsed Fields from DXC JSON-LD

| Field | Path |
|-------|------|
| Job title | `.title` |
| Location | `.jobLocation.address.addressLocality` |
| Description (HTML) | `.description` |
| Requirements (HTML) | `.requirements` |
| Employment type | `.employmentType` |
| Date posted | `.datePosted` |
| Valid through | `.validThrough` |
| Hiring organization | `.hiringOrganization.name` |

### Description Cleaning

Strip HTML tags from `.description` for plain text:

```python
import re
html = data.get('description', '')
text = re.sub(r'<[^>]+>', ' ', html)
text = re.sub(r'\s+', ' ', text).strip()
```

---

## Method 2: Workday WDAPI Endpoint

Workday-run sites expose an internal API at `/wdapi/job/<numeric_id>`.

### Finding the Job ID

The numeric ID appears in the URL path:
```
https://careers.dxc.com/job/23102930/...
                  ^^^^^^^^
```

### API Call

```bash
curl -sL "https://careers.dxc.com/wdapi/job/23102930"
```

### Response Shape (JSON)

```json
{
  "id": "23102930",
  "title": "2027 DXC Technology Graduate Program Australia",
  "primaryLocation": {"label": "Macquarie Park, New South Wales, AU"},
  "jobFamily": {"label": "Consulting & Advisory"},
  "positionProfile": {
    "businessTitle": "Application 2027 DXC Technology Graduate Program Australia",
    "assignedCategories": [...],
    "positionSegments": [...]
  }
}
```

### Other Tested Endpoints (404 or less useful)

- `/wdapi/apply/jobs/<id>/professional` → 404
- `/wdapi/job/<id>/professional` → partial data, not recommended

---

## General Workday Pattern

This pattern applies to any Workday-hosted career page:

```
https://[company].workday.com/wdapi/job/[numeric_id]
```

Common Workday hosts: workday.com, workday.com (direct), Taleo (oraclecloud.taleo.net), Greenhouse (boards.greenhouse.io), Lever (lever.co), Ashby (ashbyhq.com).

For **LinkedIn** job pages: use `linkedin.com/jobs/view/<id>` — often redirects to an external ATS URL which can then be API-extracted.

---

## Lessons Learned

- JSON-LD is the fastest method when it works — single curl, no JS rendering needed
- The WDAPI endpoint returns structured JSON but may be incomplete or return 404 depending on whether the site exposes it publicly
- If both methods fail: use `tirith` tool or delegate to a subagent with a browser tool
- Page title alone is insufficient — always confirm full job description content before generating application materials
- The `wdapi` endpoint works on DXC, SAP, ServiceNow, and other Workday-hosted career sites