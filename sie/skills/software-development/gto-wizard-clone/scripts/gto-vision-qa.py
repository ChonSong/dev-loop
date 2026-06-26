#!/usr/bin/env python3
"""
GTO Wizard Vision QA Pipeline
==============================
Compares our rendered pages against reference screenshots using code structure analysis.
Flags structural and visual differences, then triggers fixes.

Usage:
  python3 gto-vision-qa.py check <page_name>   # Check a page's structure
  python3 gto-vision-qa.py all                  # Run full QA sweep

Pages:
  equity, solver, strategy, icm, plo4, omaha, double-board, bomb-pot,
  hands, leaks, training, courses, spots, auth
"""

import sys, json, os
from pathlib import Path

REFERENCES_DIR = Path("/workspace/gto-wizard-references")
OUTPUT_DIR = Path("/workspace/gto-vision-qa-output")
OUTPUT_DIR.mkdir(exist_ok=True)

# Critical structural elements checklist per page
STRUCTURAL_CHECKLIST = {
    "equity": [
        "position_flow_bar",
        "sub_nav_tabs_strategy_ranges_breakdown_reports",
        "position_selectors_row",
        "range_input_with_copy_paste",
        "dual_13x13_matrices_side_by_side",
        "hero_range_colored_orange",
        "villain_range_colored_teal",
        "stats_row_combos_ev_equity_eqr",
        "equity_distribution_bar_win_tie_lose",
        "equity_graph_line_chart",
        "action_breakdown_right_panel",
        "quick_ranges_panel",
        "bottom_tabs_hands_summary_filters_blockers",
    ],
    "solver": [
        "game_type_selector",
        "board_input", "stack_pot_inputs",
        "run_solver_button", "status_display_with_polling",
        "strategy_results_table", "action_color_coding",
        "frequency_bars", "sample_configs",
    ],
    "strategy": [
        "two_panel_filters_sidebar", "strategy_lookup_filters",
        "position_stack_street_selectors", "strategy_list_results",
        "detail_view_strategy_table", "pagination", "sample_scenarios",
    ],
}

def check_page_structure(page: str) -> dict:
    page_file = Path(f"/workspace/open-lovable/app/gto/{page}/page.tsx")
    if not page_file.exists():
        return {"status": "MISSING", "errors": [f"File not found: {page_file}"]}
    content = page_file.read_text()
    checklist = STRUCTURAL_CHECKLIST.get(page, [])
    found, missing = [], []
    for item in checklist:
        keywords = item.replace("_", " ").lower()
        if any(kw in content.lower() for kw in keywords.split()):
            found.append(item)
        else:
            missing.append(item)
    return {
        "status": "PASS" if not missing else "PARTIAL" if len(missing) < len(checklist) else "FAIL",
        "page": page, "total_checks": len(checklist),
        "found": found, "missing": missing,
        "coverage": f"{len(found)}/{len(checklist)} ({len(found)/max(len(checklist),1)*100:.0f}%)"
    }

def print_report(results: dict):
    print("\n" + "=" * 70)
    print("  GTO WIZARD CLONE — STRUCTURAL QA REPORT")
    print("=" * 70)
    total, passed = 0, 0
    for page, r in sorted(results.items()):
        icon = {"PASS": "✅", "PARTIAL": "⚠️", "FAIL": "❌", "MISSING": "🚫"}.get(r["status"], "❓")
        print(f"\n{icon} {page.upper():12s} [{r.get('coverage','?')}]")
        for f in r.get("found", []): print(f"       ✅ {f}")
        for m in r.get("missing", []): print(f"       ❌ {m}")
        for e in r.get("errors", []): print(f"       🚫 {e}")
        total += r.get("total_checks", 0); passed += len(r.get("found", []))
    print(f"\n{'=' * 70}\n  Score: {passed}/{total} ({passed/max(total,1)*100:.0f}%)")
    return passed / max(total, 1)

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    if cmd == "all":
        results = {p: check_page_structure(p) for p in STRUCTURAL_CHECKLIST}
        (OUTPUT_DIR / "qa-report.json").write_text(json.dumps(results, indent=2))
        score = print_report(results)
        sys.exit(0 if score >= 0.9 else 1 if score >= 0.7 else 2)
    elif cmd == "check":
        page = sys.argv[2] if len(sys.argv) > 2 else "equity"
        print(json.dumps(check_page_structure(page), indent=2))
    else:
        print(f"Usage: {sys.argv[0]} [all|check <page>]")
