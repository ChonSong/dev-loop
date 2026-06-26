#!/usr/bin/env python3
"""CLI for Observation Memory — query, curate, classify, and manage observations."""

import argparse
import json
import sys
from pathlib import Path

# Add parent to path for direct execution
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from observation_memory import (
    ObservationStore,
    MemoryIndex,
    curate,
    classify_failure,
    CircuitBreaker,
)


def cmd_query(args):
    """Query memory for observations relevant to a review."""
    store = ObservationStore(args.memory_root)
    index = MemoryIndex(store).build(product=args.project, task_id=args.task_id)

    result = index.query(args.text, step_index=0)
    if result:
        print(result)
    else:
        print("(no relevant observations found)")


def cmd_curate(args):
    """Run curator after a review."""
    findings = []
    if args.findings_file:
        findings = Path(args.findings_file).read_text().strip().split("\n")
    elif args.findings:
        findings = args.findings

    log = curate(
        memory_root=args.memory_root,
        project=args.project,
        review_summary=args.review_summary or args.text or "review",
        findings=findings,
        status=args.status,
        task_id=args.task_id,
        llm_call=not args.no_llm,
    )

    print(json.dumps(log, indent=2))


def cmd_classify(args):
    """Classify a failure from error text."""
    error_texts = []
    if args.error_file:
        error_texts = [Path(args.error_file).read_text()]
    elif args.error_text:
        error_texts = [args.error_text]

    result = classify_failure(
        status=args.status,
        error_texts=error_texts,
        logs=error_texts,
    )

    print(json.dumps({
        "category": result.category,
        "confidence": result.confidence,
        "evidence": result.evidence,
        "recent_related_count": result.recent_related_count,
    }, indent=2))


def cmd_list(args):
    """List observations for a project."""
    store = ObservationStore(args.memory_root)
    if args.tier:
        observations = store.list_tier(args.tier)
    else:
        observations = store.list_all()

    for obs in observations:
        print(f"[{obs.trust:.2f}] {obs.id}: {obs.title}")


def cmd_breaker(args):
    """Manage circuit breaker state."""
    # Circuit breaker state is stored in memory only — show docs
    print("Circuit breaker is instantiated per-session. To persist state:")
    print("  Store outcomes in a JSON file alongside observations.")
    print("  Create a new CircuitBreaker() and call .record(with_memory, passed)")
    print("  Check .is_tripped() before injecting memory.")
    print()
    print("Example usage:")
    print("  from observation_memory import CircuitBreaker")
    print("  cb = CircuitBreaker()")
    print("  cb.record(with_memory=True, passed=True)")
    print("  if cb.is_tripped():")
    print("      print('Memory disabled — breaker tripped')")


def main():
    parser = argparse.ArgumentParser(
        description="Observation Memory — self-correcting behavioral knowledge",
    )
    sub = parser.add_subparsers(dest="command")

    # Common args
    def add_common(p):
        p.add_argument("--memory-root", default=str(Path.home() / ".coach-memory"),
                       help="Root directory for observation storage")
        p.add_argument("--project", default="default",
                       help="Project name (scope for product-level observations)")

    # query
    p = sub.add_parser("query", help="Query memory for relevant observations")
    add_common(p)
    p.add_argument("text", help="Review instruction text to query")
    p.add_argument("--task-id", help="Task ID for task-scoped observations")

    # curate
    p = sub.add_parser("curate", help="Run curator after a review")
    add_common(p)
    p.add_argument("--status", default="passed",
                   choices=["passed", "failed", "cancelled"],
                   help="Review status")
    p.add_argument("--review-summary", help="Summary of the review")
    p.add_argument("--findings", nargs="*", help="Review findings (one per argument)")
    p.add_argument("--findings-file", help="File with one finding per line")
    p.add_argument("--task-id", help="Task ID for task-scoped observations")
    p.add_argument("--no-llm", action="store_true",
                   help="Skip LLM curator call (dry run)")
    p.add_argument("text", nargs="?", help="Review text (used as summary if --review-summary not set)")

    # classify
    p = sub.add_parser("classify", help="Classify a failure")
    p.add_argument("--status", default="failed", help="Run status")
    p.add_argument("--error-text", help="Error message")
    p.add_argument("--error-file", help="File containing error text")

    # list
    p = sub.add_parser("list", help="List observations")
    add_common(p)
    p.add_argument("--tier", choices=["products", "suites", "tasks"],
                   help="Filter by tier")

    # breaker
    sub.add_parser("breaker", help="Circuit breaker documentation")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    if args.command == "query":
        cmd_query(args)
    elif args.command == "curate":
        cmd_curate(args)
    elif args.command == "classify":
        cmd_classify(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "breaker":
        cmd_breaker(args)


if __name__ == "__main__":
    main()
