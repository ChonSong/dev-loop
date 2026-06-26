#!/usr/bin/env python3
"""
crossref-verify.py — Verify academic source metadata via Crossref REST API.
Usage: python3 crossref-verify.py <doi> [doi2 doi3 ...]
       python3 crossref-verify.py --search "article title"
       python3 crossref-verify.py --isbn 9781847873279
"""

import sys
import json
import urllib.request
import urllib.parse

BASE = "https://api.crossref.org/works"


def fetch_by_doi(doi: str) -> dict:
    url = f"{BASE}/{urllib.parse.quote(doi, safe='')}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())["message"]


def search_by_title(query: str, rows: int = 5) -> list:
    q = urllib.parse.quote(query)
    url = f"{BASE}?query={q}&rows={rows}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())["message"]["items"]


def format_apa7(msg: dict, source_type: str = "article") -> str:
    """Format a Crossref message as APA7 reference string."""
    # Authors
    authors = msg.get("author", [])
    if not authors:
        author_str = "Unknown"
    else:
        parts = []
        for a in authors:
            given = a.get("given", "")
            family = a.get("family", "")
            if given:
                parts.append(f"{family}, {given[0]}.")
            else:
                parts.append(family)
        if len(authors) > 20:
            author_str = ", ".join(parts[:19]) + ", ... " + parts[-1]
        elif len(authors) == 1:
            author_str = parts[0]
        elif len(authors) == 2:
            author_str = f"{parts[0]}, & {parts[1]}"
        else:
            author_str = ", ".join(parts[:-1]) + ", & " + parts[-1]

    # Year
    year_obj = msg.get("published-print", msg.get("published-online", {}))
    year = year_obj.get("date-parts", [["n.d."]])[0][0] if year_obj else "n.d."

    # DOI
    doi = msg.get("DOI", "")

    if source_type == "article":
        title = msg.get("title", ["N/A"])[0] if isinstance(msg.get("title"), list) else msg.get("title", "N/A")
        journal = msg.get("container-title", ["N/A"])
        if isinstance(journal, list):
            journal = journal[0]
        vol = msg.get("volume", "")
        issue = msg.get("issue", "")
        pages = msg.get("page", "")
        vol_issue = f"{vol}({issue})" if issue else vol
        ref = f"{author_str} ({year}). {title}. *{journal}*, {vol_issue}, {pages}. https://doi.org/{doi}"
    
    elif source_type == "book":
        title = msg.get("title", ["N/A"])[0] if isinstance(msg.get("title"), list) else msg.get("title", "N/A")
        publisher = msg.get("publisher", "")
        isbn = msg.get("ISBN", ["N/A"])
        if isinstance(isbn, list):
            isbn = isbn[0]
        ref = f"{author_str} ({year}). *{title}*. {publisher}. https://doi.org/{doi}"
    
    else:
        title = msg.get("title", ["N/A"])[0] if isinstance(msg.get("title"), list) else msg.get("title", "N/A")
        ref = f"{author_str} ({year}). {title}. https://doi.org/{doi}"

    return ref


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)

    if args[0] == "--search":
        query = " ".join(args[1:])
        print(f"Searching: {query}")
        items = search_by_title(query)
        for i, item in enumerate(items):
            print(f"\n[{i+1}] {format_apa7(item)}")
            print(f"    DOI: {item.get('DOI','N/A')}")
        return

    # Batch by DOI
    for doi in args:
        try:
            msg = fetch_by_doi(doi)
            title_list = msg.get("title", [])
            title = title_list[0] if isinstance(title_list, list) else title_list
            is_book = "book" in msg.get("type", "") or bool(msg.get("ISBN"))
            stype = "book" if is_book else "article"
            print(f"\n=== {doi} ===")
            print(f"Title: {title}")
            print(f"Authors: {[f\"{a.get('given','')} {a.get('family','')}\" for a in msg.get('author',[])]}")
            year_obj = msg.get("published-print", msg.get("published-online", {}))
            year = year_obj.get("date-parts", [["N/A"]])[0][0] if year_obj else "N/A"
            print(f"Year: {year}")
            print(f"Journal/Container: {msg.get('container-title',['N/A'])}")
            print(f"Volume: {msg.get('volume','N/A')} Issue: {msg.get('issue','N/A')}")
            print(f"Pages: {msg.get('page','N/A')}")
            print(f"\nAPA7:\n  {format_apa7(msg, stype)}")
        except Exception as e:
            print(f"\n=== {doi} === ERROR: {e}")


if __name__ == "__main__":
    main()