---
name: academic-source-compilation
description: "Collect, verify, and compile academic sources into a structured annotated library with verified APA7 references. Covers Crossref API verification, publisher API patterns, YouTube metadata extraction, and continuous sources document maintenance."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [Research, Academic, Sources, APA7, Citations, Crossref, Bibliography, Education]
    related_skills: [arxiv, research-paper-writing]
    requires_toolsets: [terminal, web]
---

# Academic Source Compilation

Assemble a verified, annotated sources library from mixed sources: journal articles, textbooks, YouTube videos, lecture modules, web documents, and course materials. Every source gets a complete APA7 reference and a live URL where available.

## Core Workflow

1. **Receive source** — URL, pasted content, or reference string
2. **Classify type** — journal article, book/chapter, video, web document, lecture module
3. **Extract metadata** — use the appropriate tool per source type (see Techniques)
4. **Verify** — Crossref for DOIs, page extraction for other types
5. **Format APA7** — full reference with verified live URL
6. **Write to SOURCES.md** — mission statement first, then entries sorted by type
7. **Update Mission Statement** — if scope or workflow changes

## Source Types & Tools

| Source Type | First Tool | Fallback |
|-------------|------------|----------|
| Journal article (DOI known) | Crossref API | curl + page parse |
| Book / Chapter | Crossref API (by ISBN or title search) | publisher page |
| YouTube video | curl + grep on page | YouTube oEmbed API |
| Taylor & Francis / SAGE / paywalled | **Crossref API (by DOI)** — never try to curl directly | note as blocked |
| Web documents (no DOI) | curl + extract | paste directly |
| Lecture module content | paste directly | — |
| **In-text references (citation strings)** | **Crossref search by author + year + title keywords** | manual DOI lookup |
| **Unknown citation (author + year known)** | Crossref search by query | — |

## Techniques

### Crossref API (Primary Verification)

Use when: publisher blocks curl, or DOI is known/guessable.

```bash
# By DOI (most reliable)
curl -sL "https://api.crossref.org/works/{doi}" \
  -H "Accept: application/json" | python3 -c "
import sys, json
data = json.load(sys.stdin)
msg = data['message']
# title is ALWAYS a list — extract the string first
title = msg.get('title', ['N/A'])[0]
# author is always a list of dicts
authors = [f\"{a.get('given','')} {a.get('family','')}\" for a in msg.get('author', [])]
journal = msg.get('container-title', ['N/A'])[0]
year = (msg.get('published-print') or msg.get('published-online') or {}).get('date-parts', [[None]])[0][0]
print('Title:', title)
print('Authors:', authors)
print('Journal:', journal)
print('Year:', year)
print('Volume:', msg.get('volume', 'N/A'), 'Issue:', msg.get('issue', 'N/A'))
print('Pages:', msg.get('page', 'N/A'))
print('DOI:', msg.get('DOI', 'N/A'))
"
```

**Key endpoints:**
- `https://api.crossref.org/works/{doi}` — metadata by DOI
- `https://api.crossref.org/works?query={encoded_title}&rows=5` — search by title

**Critical gotchas (causes AttributeError if missed):**
- `title`, `container-title`, and `author` fields are **always lists** — **always** use `[0]` to extract the string before calling `.get()` or printing
- `published-print` may be null; fall back to `published-online`
- Some DOIs contain special chars (e.g., `10.1002/1098-2736(200102)38:2<137::aid-tea1001>3.0.co;2-u`) — use the raw DOI, url-encode if needed
- Crossref search returns up to millions of results — always add `rows=5` and filter by title substring match
- When looping over search results, each `item` is a dict — `item.get('title', ['N/A'])` returns a list, so `t = item.get('title', ['N/A'])[0]` then work with `t`

### YouTube Metadata Extraction

```bash
# Get title and channel
curl -sL "https://youtu.be/{video_id}" \
  -A "Mozilla/5.0" | grep -o '"title":"[^"]*"' | head -1

curl -sL "https://youtu.be/{video_id}" \
  -A "Mozilla/5.0" | grep -o '"ownerChannelName":"[^"]*"' | head -1

# Get upload date
curl -sL "https://youtu.be/{video_id}" \
  -A "Mozilla/5.0" | grep -o '"uploadDate":"[^"]*"' | head -1
```

YouTube returns JSON-LD blocks in the HTML. Use grep to extract JSON fields.

**Note:** Duration (`lengthSeconds`) requires parsing nested JSON — the simple grep approach does not extract it reliably. For duration, either use the oEmbed API or accept "duration unknown" and note it in the source entry.

### YouTube oEmbed API (Fallback for Duration)

```bash
curl -sL "https://www.youtube.com/oembed?url=https://youtu.be/{video_id}&format=json" \
  -H "Accept: application/json"
```

Returns `{"title": "...", "author_name": "...", "author_url": "...", "thumbnail_url": "..."}` — but **no duration field**. YouTube oEmbed does not expose video length.

### Publisher Sites That Block curl

Taylor & Francis, SAGE, and similar use Cloudflare JavaScript challenges. Never try to curl these directly — it returns a Cloudflare block page.

**Always try Crossref first** if a DOI is in the URL:
```
DOI from: https://www.tandfonline.com/doi/full/10.1080/09650792.2013.856771
                          └─────────────────────────────────────────┘
```

If no DOI, try the Crossref title search. If that fails, note the source as "requires browser" and move on.

## SOURCES.md Structure

Always create `/workspace/SOURCES.md` with this header:

```markdown
# Sources Document — [Topic]

## Mission Statement

**Purpose:** ...
**Scope:** ...
**Workflow:** Numbered steps including "Session interrupted? Read this doc."
**Progress:** X sources total. N new this session. M still pending.

---

## Collected Sources

[Entry per source: title, URL, authors, publisher, year, DOI, status, APA7, summary]

## In-Text References

[Cited sources from lecture modules, with verified DOIs]

## To Add / In Progress

Numbered list. Status icons: ✅ complete, ⚠️ partial, 🔴 pending

## Next Steps

1. ...
```

**Continuity rule:** If session is interrupted, the next agent reads Mission Statement → picks up at first unchecked item in "To Add".

## APA7 Quick Rules

- Journal articles: `Author, A. A., & Author, B. B. (Year). Title. *Journal*, *Volume*(Issue), Pages. https://doi.org/xxx`
- Books: `Author, A. A., & Author, B. B. (Year). *Title of work*. Publisher. URL`
- YouTube: `Channel. (Year, Month Day). *Title* [Video]. YouTube. URL`
- No author? Use institution. No year? Use (n.d.)

## Google Drive Upload (Post-Compilation)

**Three methods, in order of reliability:**

### Method 1: rclone (if already configured)
```bash
# rclone.conf is at ~/.hermes/rclone_config/rclone.conf
# Test access:
/home/hermeswebui/.hermes/rclone --config /home/hermeswebui/.hermes/rclone_config/rclone.conf ls gdrive: --max-depth 1

# Upload:
/home/hermeswebui/.hermes/rclone --config /home/hermeswebui/.hermes/rclone_config/rclone.conf copy /workspace/SOURCES.md "gdrive:/1THOo5il6pawcw5EYcY0t-h1YBXeZjmjk/"
```

**Token expiry problem (401 authError):** If rclone returns `Invalid Credentials`, the OAuth token in rclone.conf is expired. You cannot refresh it programmatically — the refresh_token grant fails with `invalid_grant`. Fix: run `rclone config` on the host machine and re-authorize, then copy the updated `rclone.conf` to `~/.hermes/rclone_config/rclone.conf`.

### Method 2: google-workspace skill (requires OAuth setup)
```bash
HERMES_HOME=${HERMES_HOME:-$HOME/.hermes}
GSETUP="python $HERMES_HOME/skills/productivity/google-workspace/scripts/setup.py"
$GSETUP --check  # AUTHENTICATED or NOT_AUTHENTICATED
```
If not authenticated, run the full OAuth flow: `--client-secret`, `--auth-url`, `--auth-code`.

### Method 3: Browser delegation (⚠️ broken for uploads)
**The browser tool CANNOT upload files to Google Drive.** Attempting to delegate a file upload to the browser tool fails — it returns "no browser tool for uploads." Do NOT promise browser-based upload. Use rclone or google-workspace.

**If all methods fail:** The file is at `/workspace/SOURCES.md`. Instruct the user to download and upload manually. Never leave them waiting for a method that can't work.

## Quality Checklist

Before marking a source ✅:
- [ ] Title extracted and confirmed
- [ ] Authors confirmed (all, in correct order)
- [ ] Year published confirmed
- [ ] DOI verified via Crossref (or noted if unavailable)
- [ ] Live URL confirmed reachable
- [ ] APA7 formatted correctly
- [ ] Summary/annotation written (1-2 sentences)
- [ ] To Add list updated

---

*See `references/crossref-api-patterns.md` for verified API patterns, JSON parsing rules, and APA7 formatting code.*
*See `references/doi-verification-log.md` for Crossref API quirks and patterns.*