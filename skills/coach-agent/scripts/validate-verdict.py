#!/usr/bin/env python3
"""Validate Coach verdict JSON against the schema. Returns 0 if valid, 1 if invalid.

Usage:
    python3 validate-verdict.py < input.json      # stdin
    python3 validate-verdict.py path/to/file.json  # file
    # Inside Coach: write verdict to /tmp/coach-verdict.json then validate
"""

import json
import sys
import re
from pathlib import Path


# Embedded schema — no external deps (jsonschema not available on host)
REQUIRED_TOP = {"verdict", "project", "timestamp", "methodology", "findings", "tasks_generated"}
VALID_VERDICTS = {"APPROVE", "FIX", "REVERT"}
VALID_SEVERITIES = {"P1", "P2", "P3"}
VALID_FINDING_TYPES = {"bug", "regression", "visual_gap", "methodology_gap", "perf", "security", "other"}
VALID_REFERENCE_MATCHES = {"exact", "minor_gaps", "significant_gaps", "broken", "not_checked"}
VALID_TASK_PRIORITIES = {"P1", "P2", "P3"}


def validate_iso_timestamp(s: str) -> bool:
    """Basic ISO 8601 check: YYYY-MM-DDTHH:MM:SS..."""
    return bool(re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', s))


def validate(verdict: dict) -> list[str]:
    """Return list of errors. Empty list = valid."""
    errors = []

    # Required top-level fields
    missing = REQUIRED_TOP - set(verdict.keys())
    if missing:
        errors.append(f"Missing required fields: {missing}")

    # verdict
    if "verdict" in verdict:
        if verdict["verdict"] not in VALID_VERDICTS:
            errors.append(f"verdict must be one of {VALID_VERDICTS}, got: {verdict['verdict']}")

    # timestamp
    if "timestamp" in verdict:
        if not validate_iso_timestamp(str(verdict["timestamp"])):
            errors.append(f"timestamp must be ISO 8601, got: {verdict['timestamp']}")

    # reference_match (optional but validated if present)
    if verdict.get("reference_match") and verdict["reference_match"] not in VALID_REFERENCE_MATCHES:
        errors.append(f"reference_match must be one of {VALID_REFERENCE_MATCHES}")

    # methodology
    if "methodology" in verdict and isinstance(verdict["methodology"], dict):
        m = verdict["methodology"]
        for field in ["total_failures", "test_bugs", "methodology_failures"]:
            if field in m and not isinstance(m[field], int):
                errors.append(f"methodology.{field} must be integer, got: {type(m[field]).__name__}")
        if "systemic" in m and not isinstance(m["systemic"], bool):
            errors.append(f"methodology.systemic must be boolean")
        if "can_approve" in m and not isinstance(m["can_approve"], bool):
            errors.append(f"methodology.can_approve must be boolean")
        # Gate: if >50% methodology failures, can_approve MUST be false
        if isinstance(m.get("total_failures"), int) and isinstance(m.get("methodology_failures"), int) and m["total_failures"] > 0:
            ratio = m["methodology_failures"] / m["total_failures"]
            if ratio > 0.5 and m.get("can_approve") is True:
                errors.append(f"GATE VIOLATION: {m['methodology_failures']}/{m['total_failures']} methodology failures ({ratio:.0%}) > 50% — can_approve must be false")

    # findings
    if "findings" in verdict and isinstance(verdict["findings"], list):
        for i, f in enumerate(verdict["findings"]):
            if not isinstance(f, dict):
                errors.append(f"findings[{i}] is not an object")
                continue
            if "severity" not in f:
                errors.append(f"findings[{i}] missing severity")
            elif f["severity"] not in VALID_SEVERITIES:
                errors.append(f"findings[{i}].severity must be one of {VALID_SEVERITIES}, got: {f['severity']}")
            if "type" not in f:
                errors.append(f"findings[{i}] missing type")
            elif f["type"] not in VALID_FINDING_TYPES:
                errors.append(f"findings[{i}].type must be one of {VALID_FINDING_TYPES}, got: {f['type']}")
            if "description" not in f:
                errors.append(f"findings[{i}] missing description")

    # fidelity (optional — from DELEGATE-52 port)
    if "fidelity" in verdict and isinstance(verdict["fidelity"], dict):
        f = verdict["fidelity"]
        for field in ["diff_size_bytes", "codebase_size_bytes", "files_read", "files_changed"]:
            if field in f and not isinstance(f[field], int):
                errors.append(f"fidelity.{field} must be integer, got: {type(f[field]).__name__}")
        if "cfs" in f:
            if not isinstance(f["cfs"], (int, float)):
                errors.append(f"fidelity.cfs must be number, got: {type(f['cfs']).__name__}")
            elif f["cfs"] < 0 or f["cfs"] > 1:
                errors.append(f"fidelity.cfs out of range [0.0–1.0]: {f['cfs']}")
        if "trend" in f and f["trend"] not in ("improving", "stable", "degrading", "unknown"):
            errors.append(f"fidelity.trend must be one of: improving, stable, degrading, unknown")
        if "token_budget_used" in f and not isinstance(f["token_budget_used"], int):
            errors.append(f"fidelity.token_budget_used must be integer")
        if "must_change_gate" in f:
            if not isinstance(f["must_change_gate"], bool):
                errors.append(f"fidelity.must_change_gate must be boolean")
            elif f["must_change_gate"] is False:
                # DELEGATE-52 has_written guard: empty commits block APPROVE
                errors.append("GATE VIOLATION: must_change_gate is false — Player produced zero changes. Blocks APPROVE.")
    # adversarial (optional — from adversarial review gate step 2.7)
    if "adversarial" in verdict and isinstance(verdict["adversarial"], dict):
        a = verdict["adversarial"]
        if "ran" in a and not isinstance(a["ran"], bool):
            errors.append(f"adversarial.ran must be boolean")
        if "model" in a and not isinstance(a["model"], str):
            errors.append(f"adversarial.model must be string")
        for field in ["findings_added", "findings_primary_missed", "conflicts", "time_taken_seconds"]:
            if field in a and not isinstance(a[field], int):
                errors.append(f"adversarial.{field} must be integer")
        if "verdict_changed" in a and not isinstance(a["verdict_changed"], bool):
            errors.append(f"adversarial.verdict_changed must be boolean")
        if "novel_finding_types" in a:
            if not isinstance(a["novel_finding_types"], list):
                errors.append(f"adversarial.novel_finding_types must be array")
            elif not all(isinstance(x, str) for x in a["novel_finding_types"]):
                errors.append(f"adversarial.novel_finding_types must contain only strings")
    if "tasks_generated" in verdict and isinstance(verdict["tasks_generated"], list):
        for i, t in enumerate(verdict["tasks_generated"]):
            if not isinstance(t, dict):
                errors.append(f"tasks_generated[{i}] is not an object")
                continue
            if "id" not in t:
                errors.append(f"tasks_generated[{i}] missing id")
            if "description" not in t:
                errors.append(f"tasks_generated[{i}] missing description")

    return errors


def extract_json_from_text(text: str) -> dict | None:
    """Try to extract a JSON object from text that may have markdown/prefix."""
    # Try direct parse first
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try markdown code block
    m = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Try finding first { ... } block
    start = text.find('{')
    if start >= 0:
        depth = 0
        for i in range(start, len(text)):
            if text[i] == '{':
                depth += 1
            elif text[i] == '}':
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i+1])
                    except json.JSONDecodeError:
                        break

    return None


def main():
    # Read input
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
        if not path.exists():
            print(f"ERROR: file not found: {path}", file=sys.stderr)
            sys.exit(1)
        raw = path.read_text()
    else:
        raw = sys.stdin.read()

    # Parse
    verdict = extract_json_from_text(raw)
    if verdict is None:
        print("ERROR: could not parse JSON from input", file=sys.stderr)
        print("Input (first 500 chars):", file=sys.stderr)
        print(raw[:500], file=sys.stderr)
        sys.exit(1)

    # Validate
    errors = validate(verdict)
    if errors:
        print(f"INVALID: {len(errors)} error(s):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(1)

    print("VALID ✓")
    sys.exit(0)


if __name__ == "__main__":
    main()
