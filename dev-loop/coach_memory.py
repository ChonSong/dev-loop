#!/usr/bin/env python3
"""Coach memory integration — inject observations before review, curate after.

Designed to be called from coach-agent cron job shell hooks.
Sits alongside the existing coach/player loop as a memory layer.

Usage:
  # Before review: inject relevant observations into context
  python3 coach_memory.py inject --project gto-wizard --instruction "review the study page preflop tab"

  # After review: curate findings into memory
  python3 coach_memory.py curate --project gto-wizard --status passed \
    --review-summary "Study page preflop review" \
    --findings "Tab loads correctly" "Position buttons highlight on click"

  # Classify a failure
  python3 coach_memory.py classify --error-text "browser disconnected unexpectedly"

  # Check circuit breaker status
  python3 coach_memory.py breaker-status --project gto-wizard

  # Record outcome for circuit breaker
  python3 coach_memory.py record-outcome --project gto-wizard --with-memory --passed
"""

import argparse
import json
import sys
from pathlib import Path

# Ensure workspace is on path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from observation_memory import (
    ObservationStore,
    MemoryIndex,
    curate,
    classify_failure,
    CircuitBreaker,
)


DEFAULT_MEMORY_ROOT = str(Path.home() / ".coach-memory")


def cmd_inject(args):
    """Query memory and output XML context for injection into coach prompt."""
    store = ObservationStore(args.memory_root)
    index = MemoryIndex(store).build(
        product=args.project,
        task_id=args.task_id,
        suite_id=args.suite_id,
    )

    context = index.query(args.instruction, step_index=0)
    if context:
        print(context)
    else:
        # Silent: no output → no injection
        pass


def cmd_curate(args):
    """Run curator after a review completes."""
    findings = []
    if args.findings_file:
        findings = [
            f.strip()
            for f in Path(args.findings_file).read_text().strip().split("\n")
            if f.strip()
        ]
    elif args.findings:
        findings = args.findings

    log = curate(
        memory_root=args.memory_root,
        project=args.project,
        review_summary=args.review_summary or args.instruction or "review",
        findings=findings,
        status=args.status,
        task_id=args.task_id,
        llm_call=not args.no_llm,
    )

    print(json.dumps(log, indent=2))

    # Record outcome for circuit breaker
    if args.status in ("passed", "failed"):
        breaker = _load_breaker(args.memory_root, args.project)
        breaker.record(
            with_memory=True,
            passed=(args.status == "passed"),
        )
        _save_breaker(args.memory_root, args.project, breaker)


def cmd_classify(args):
    """Classify a failure from error text."""
    error_texts = []
    if args.error_file:
        error_texts = [Path(args.error_file).read_text().strip()]
    elif args.error_text:
        error_texts = [args.error_text]

    result = classify_failure(
        status=args.status,
        error_texts=error_texts,
        logs=error_texts if args.include_logs else None,
    )

    # Output in a format easily parsed by coach bash scripts
    if args.bash:
        print(f"CATEGORY={result.category}")
        print(f"CONFIDENCE={result.confidence}")
        print(f"EVIDENCE={result.evidence[0] if result.evidence else 'none'}")
    else:
        print(json.dumps({
            "category": result.category,
            "confidence": result.confidence,
            "evidence": result.evidence,
        }, indent=2))


def cmd_breaker_status(args):
    """Show circuit breaker status for a project."""
    breaker = _load_breaker(args.memory_root, args.project)
    status = breaker.status()
    status["project"] = args.project
    print(json.dumps(status, indent=2))


def cmd_record_outcome(args):
    """Record a review outcome for circuit breaker tracking."""
    breaker = _load_breaker(args.memory_root, args.project)
    breaker.record(
        with_memory=args.with_memory,
        passed=args.passed,
    )
    _save_breaker(args.memory_root, args.project, breaker)
    print(json.dumps({"recorded": True, "tripped": breaker.is_tripped()}))


def cmd_list(args):
    """List observations for a project."""
    store = ObservationStore(args.memory_root)
    if args.tier:
        observations = store.list_tier(args.tier)
    elif args.project:
        observations = store.list("products", args.project)
    else:
        observations = store.list_all()

    if args.json:
        print(json.dumps([o.to_dict() for o in observations], indent=2))
    else:
        if not observations:
            print("(no observations)")
        for obs in observations:
            expired = "⚠️ " if obs.trust < 0.3 else ""
            print(f"{expired}[{obs.trust:.2f}] {obs.id}: {obs.title}")


# ---- Circuit breaker persistence ----

def _breaker_file(memory_root: str, project: str) -> Path:
    return Path(memory_root) / "products" / project / ".circuit_breaker.json"


def _load_breaker(memory_root: str, project: str) -> CircuitBreaker:
    """Load circuit breaker state from disk."""
    path = _breaker_file(memory_root, project)
    if path.exists():
        try:
            data = json.loads(path.read_text())
            cb = CircuitBreaker()
            for outcome in data.get("window", []):
                cb.record(
                    with_memory=outcome.get("with_memory", False),
                    passed=outcome.get("passed", False),
                )
            return cb
        except (json.JSONDecodeError, KeyError):
            pass
    return CircuitBreaker()


def _save_breaker(memory_root: str, project: str, breaker: CircuitBreaker):
    """Save circuit breaker state to disk."""
    path = _breaker_file(memory_root, project)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "window": [
            {"with_memory": o.with_memory, "passed": o.passed}
            for o in breaker.window
        ],
        "tripped": breaker.is_tripped(),
    }))


def main():
    parser = argparse.ArgumentParser(
        description="Coach memory — observation injection and curation for dev loops",
    )
    sub = parser.add_subparsers(dest="command")

    def add_memory_root(p):
        p.add_argument(
            "--memory-root",
            default=DEFAULT_MEMORY_ROOT,
            help=f"Root directory for observations (default: {DEFAULT_MEMORY_ROOT})",
        )

    def add_project(p):
        p.add_argument("--project", default="default", help="Project name")

    # inject
    p = sub.add_parser("inject", help="Query memory and output context for injection")
    add_memory_root(p)
    add_project(p)
    p.add_argument("--task-id", help="Task ID for task-scoped observations")
    p.add_argument("--suite-id", help="Suite ID for suite-scoped observations")
    p.add_argument("instruction", help="Review instruction to query against")

    # curate
    p = sub.add_parser("curate", help="Run curator after review")
    add_memory_root(p)
    add_project(p)
    p.add_argument("--status", default="passed", choices=["passed", "failed", "cancelled"])
    p.add_argument("--review-summary", help="Summary of the review")
    p.add_argument("--findings", nargs="*", help="Review findings")
    p.add_argument("--findings-file", help="File with one finding per line")
    p.add_argument("--task-id", help="Task ID for task-scoped observations")
    p.add_argument("--no-llm", action="store_true", help="Skip LLM curator (dry run)")
    p.add_argument("instruction", nargs="?", help="Review instruction (used as summary if --review-summary not set)")

    # classify
    p = sub.add_parser("classify", help="Classify a failure")
    p.add_argument("--status", default="failed")
    p.add_argument("--error-text", help="Error message text")
    p.add_argument("--error-file", help="File containing error text")
    p.add_argument("--include-logs", action="store_true", help="Also search log output")
    p.add_argument("--bash", action="store_true", help="Output in bash-friendly format")

    # breaker-status
    p = sub.add_parser("breaker-status", help="Check circuit breaker state")
    add_memory_root(p)
    add_project(p)

    # record-outcome
    p = sub.add_parser("record-outcome", help="Record review outcome for breaker")
    add_memory_root(p)
    add_project(p)
    p.add_argument("--with-memory", action="store_true", default=True, help="Review used memory")
    p.add_argument("--without-memory", dest="with_memory", action="store_false", help="Review did not use memory")
    p.add_argument("--passed", action="store_true", default=True, help="Review passed")
    p.add_argument("--failed", dest="passed", action="store_false", help="Review failed")

    # list
    p = sub.add_parser("list", help="List observations")
    add_memory_root(p)
    add_project(p)
    p.add_argument("--tier", choices=["products", "suites", "tasks"])
    p.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    if args.command == "inject":
        cmd_inject(args)
    elif args.command == "curate":
        cmd_curate(args)
    elif args.command == "classify":
        cmd_classify(args)
    elif args.command == "breaker-status":
        cmd_breaker_status(args)
    elif args.command == "record-outcome":
        cmd_record_outcome(args)
    elif args.command == "list":
        cmd_list(args)


if __name__ == "__main__":
    main()
