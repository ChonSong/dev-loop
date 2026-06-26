#!/usr/bin/env python3
"""
Structural QA Template — Customize for each UI replication project.

Usage:
  1. Define PAGE_REFERENCES and STRUCTURAL_CHECKLIST for your project
  2. Run: python3 structure-qa-template.py all
  3. Fix all issues before proceeding to visual polish
"""

import sys
import json
from pathlib import Path

# ── CONFIGURE THESE ─────────────────────────────────────
PROJECT = "your-project-name"
PAGES_DIR = Path(f"/workspace/{PROJECT}")
REFERENCES_DIR = Path(f"/workspace/{PROJECT}-references")

PAGE_REFERENCES = {
    "home": ["homepage_screenshot.jpg"],
    "settings": ["settings_panel.png"],
}

STRUCTURAL_CHECKLIST = {
    "home": [
        "header_nav",
        "hero_section",
        "feature_grid",
        "footer",
    ],
    "settings": [
        "sidebar",
        "profile_form",
        "save_button",
    ],
}
# ────────────────────────────────────────────────────────

OUT = Path("/workspace/qa-output")
OUT.mkdir(exist_ok=True)


def check_page(page: str) -> dict:
    """Check if a page has the required structural elements in its code."""
    page_file = PAGES_DIR / page / "page.tsx"
    if not page_file.exists():
        return {"status": "MISSING", "errors": [f"File not found: {page_file}"]}

    content = page_file.read_text()
    checklist = STRUCTURAL_CHECKLIST.get(page, [])

    found = []
    missing = []

    for item in checklist:
        keywords = item.replace("_", " ")
        found_any = any(kw in content.lower() for kw in keywords.split())
        if found_any:
            found.append(item)
        else:
            missing.append(item)

    return {
        "status": "PASS" if len(missing) == 0 else "PARTIAL" if len(missing) < len(checklist) else "FAIL",
        "page": page,
        "total_checks": len(checklist),
        "found": found,
        "missing": missing,
        "coverage": f"{len(found)}/{len(checklist)} ({len(found)/max(len(checklist),1)*100:.0f}%)",
    }


def check_all() -> dict:
    results = {}
    for page in PAGE_REFERENCES:
        results[page] = check_page(page)
    return results


def print_report(results: dict):
    print("\n" + "=" * 60)
    print(f"  STRUCTURAL QA REPORT — {PROJECT}")
    print("=" * 60)

    total_checks = 0
    total_passed = 0
    pages_failing = []

    for page, result in sorted(results.items()):
        icon = {"PASS": "✅", "PARTIAL": "⚠️", "FAIL": "❌", "MISSING": "🚫"}.get(result["status"], "❓")
        print(f"\n{icon}  {page.upper():12s} [{result.get('coverage','?')}]")

        for item in result.get("found", []):
            print(f"       ✅ {item}")
        for item in result.get("missing", []):
            print(f"       ❌ {item}")
        for err in result.get("errors", []):
            print(f"       🚫 {err}")

        total_checks += result.get("total_checks", 0)
        total_passed += len(result.get("found", []))
        if result["status"] in ("FAIL", "MISSING"):
            pages_failing.append(page)

    print("\n" + "-" * 60)
    print(f"  {total_passed}/{total_checks} checks passed ({total_passed/max(total_checks,1)*100:.0f}%)")
    print(f"  Pages failing: {len(pages_failing)}")
    if pages_failing:
        print(f"  Fix first: {', '.join(pages_failing)}")
    print("=" * 60)

    return total_passed / max(total_checks, 1)


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"

    if cmd == "all":
        results = check_all()
        score = print_report(results)
        (OUT / "qa-report.json").write_text(json.dumps(results, indent=2))
        print(f"\nReport: {OUT / 'qa-report.json'}")
        sys.exit(0 if score >= 0.9 else 1)

    elif cmd == "check":
        page = sys.argv[2] if len(sys.argv) > 2 else list(PAGE_REFERENCES.keys())[0]
        result = check_page(page)
        print(json.dumps(result, indent=2))

    else:
        print(__doc__)


if __name__ == "__main__":
    main()
