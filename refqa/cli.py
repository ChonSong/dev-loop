"""CLI entry points for RefQA.

Usage::

    refqa validate <test.yaml>          # parse-only check
    refqa run      <test.yaml>           # full execution
    refqa run      <test.yaml> [options] # with optional overrides
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .parser import parse_test, validate_test_yaml
from .runner import TestRunner


# ── Helpers ────────────────────────────────────────────────────────────────


def _load_url_map(path: str) -> dict[str, str]:
    """Load a JSON file mapping target names → URLs."""
    raw = Path(path).read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError(f"URL map must be a JSON object, got {type(data).__name__}")
    return {k: str(v) for k, v in data.items()}


def _run_action(args: argparse.Namespace) -> None:
    """Handle the ``run`` subcommand."""
    test_path = args.test_file
    url_map: dict[str, str] = {}

    if args.url_map:
        url_map = _load_url_map(args.url_map)

    # Also accept inline --target-url / --reference-url.
    if args.target_url:
        # If no url_map, derive primary from target_url.
        # This is a simple fallback.
        test = parse_test(test_path, url_map=url_map)
        # Ensure primary target has a URL.
        primary, _ = test.targets.resolve(url_map)
        if not primary.url:
            url_map[primary.name] = args.target_url
        # Re-parse with updated map.
        test = parse_test(test_path, url_map=url_map)

    test = parse_test(test_path, url_map=url_map)

    runner = TestRunner(
        test=test,
        url_map=url_map,
        headless=not args.visible,
    )

    result = runner.run()

    # ── Output ────────────────────────────────────────────────────────
    status = "PASS" if result.success else "FAIL"
    print(f"\n{'='*60}")
    print(f"  {result.test_id}: {result.name}")
    print(f"  Status: {status}")
    print(f"  Steps: {result.passed_steps}/{result.total_steps} passed, "
          f"{result.failed_steps} failed")
    print(f"  Duration: {result.duration_seconds:.1f}s")
    print(f"{'='*60}")

    for sr in result.step_results:
        icon = "✓" if sr.success else "✗"
        print(f"  {icon} Step {sr.step_index}: {sr.description[:100]}")
        if sr.error:
            print(f"     Error: {sr.error}")
        if sr.match is not None:
            print(f"     Reference match: {sr.match}")

    sys.exit(0 if result.success else 1)


def _validate_action(args: argparse.Namespace) -> None:
    """Handle the ``validate`` subcommand."""
    url_map: dict[str, str] = {}
    if args.url_map:
        url_map = _load_url_map(args.url_map)

    msg = validate_test_yaml(args.test_file, url_map=url_map)
    print(msg)
    sys.exit(0 if msg.startswith("✓") else 1)


# ── Parser ────────────────────────────────────────────────────────────────


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="refqa",
        description="Reference-Augmented Agentic QA — self-healing YAML tests "
        "with reference-based verification.",
    )
    parser.add_argument(
        "--url-map",
        help="Path to a JSON file mapping target names → URLs "
        "(e.g. {\"gto-wizard\": \"https://...\"})",
    )

    sub = parser.add_subparsers(required=True, dest="command")

    # validate
    val = sub.add_parser("validate", help="Validate a test YAML file (no execution)")
    val.add_argument("test_file", type=str, help="Path to the test YAML file")
    val.add_argument(
        "--url-map",
        help="Path to a JSON file mapping target names → URLs",
    )
    val.set_defaults(func=_validate_action)

    # run
    run = sub.add_parser("run", help="Run a test YAML file")
    run.add_argument("test_file", type=str, help="Path to the test YAML file")
    run.add_argument(
        "--url-map",
        help="Path to a JSON file mapping target names → URLs",
    )
    run.add_argument(
        "--target-url",
        type=str,
        default="",
        help="Fallback URL for the primary target (when not in url-map)",
    )
    run.add_argument(
        "--visible",
        action="store_true",
        default=False,
        help="Run browser in visible (non-headless) mode",
    )
    run.set_defaults(func=_run_action)

    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
