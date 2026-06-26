# Academic Source Research for Essays

This file documents how to find real scholarly sources (books, journal articles) for university essays using the Crossref API and web research. Captured from the CULT1001 Japan essay session (May 2026).

## The Problem

Students often cite Wikipedia or course materials when "scholarly sources" are required. Finding real academic sources requires targeted research, not generic Google searches.

## Crossref API (Primary Method)

Use the Crossref API to find academic sources by topic. No auth required, just a User-Agent header.

```python
import urllib.request, json

queries = [
    "Japan cultural borrowing China Korea",
    "Heian Japan selective adoption Chinese culture",
    "Tokugawa isolation Japan scholarly book",
    "Meiji Japan cultural transformation borrowing"
]

for q in queries:
    url = f"https://api.crossref.org/works?query={q.replace(' ','+')}&filter=type:book,type:journal-article&rows=3&mailto=hermes@example.com"
    req = urllib.request.Request(url, headers={"User-Agent": "hermes-research/1.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
        for item in data.get('message', {}).get('items', [])[:3]:
            authors = [f"{a.get('family','')}" for a in item.get('author', [])]
            year = item.get('published-print',{}).get('date-parts',[['']])[0][0] or item.get('published-online',{}).get('date-parts',[['']])[0][0]
            title = item.get('title', [''])[0]
            doi = item.get('DOI', '')
            venue = item.get('container-title', [''])[0] if item.get('container-title') else (item.get('publisher','') or 'book')
            print(f"{', '.join(authors)} ({year}). \"{title}\". {venue}. DOI: {doi}")
```

**Filter options:**
- `type:book` — for monographs and edited volumes
- `type:journal-article` — for peer-reviewed articles
- `has-full-text:true` — only sources with accessible PDFs

## What Makes a Source "Scholarly"

| OK | Not OK |
|----|--------|
| Academic book (university press or specialist publisher) | Wikipedia |
| Peer-reviewed journal article | Course lecture slides / module PDFs |
| Edited volume chapter with DOI | Course discourse analysis |
| Working paper with DOI | General interest magazine |
| Primary source anthology (e.g., Kublin, Ebrey) | Generic website |

## Citation Format for Essay

For a university essay with in-text superscript citations:

**In the Notes section:**
```
1. Rhoads Murphey, *A History of Asia* (Routledge, 2019), Ch. 9.
2. Robert Borgen, "Chinese Literary Forms in Heian Japan: Poetics and Practice," *Monumenta Nipponica* 72, no. 2 (2018): 181-210. DOI: 10.1353/mni.2018.0003.
```

**Inline (superscript numeral after the specific claim):**
```
The mechanism was the same everywhere.¹
```

## Replacing Course Materials with Scholarly Sources

When the user says "don't use course materials for sources — do research":
1. Run Crossref API queries for the essay's key themes
2. Pull 4-5 real academic sources with DOIs
3. Remove WSU module citations from references
4. Keep human experience sources (Module 08, Module 10) only if the user specifically wants them — ask if unsure
5. Note in the essay that "course materials were not used as sources; scholarly sources were used instead"

## Essay Title Naming

Make the title informative and argumentative, not just descriptive:
- **Good:** "Japan_Borrowed_as_Asia_Did_CULT1001.docx" — states the thesis
- **Bad:** "cult1001_essay_v7.docx" — no information

If the user suggests a title, use theirs. If not, craft one that reflects the essay's argument.