"""Rule-based failure classifier with 8 categories.

Mirrors agent-qa's classifyRunFailureFromDashboardData in agent-qa-server.ts.
Priority-ordered needle matching against aggregated error text.
No LLM call — instant, deterministic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# Ordered checks: (needles_list, category, confidence)
FAILURE_CHECKS: list[tuple[list[str], str, float]] = [
    (["timed out", "timeout"], "timeout", 0.90),
    (["appium server failed", "appium"], "appium_startup", 0.90),
    (
        ["browser closed", "target page, context or browser has been closed", "browser disconnect"],
        "browser_disconnect",
        0.85,
    ),
    (["hook_not_runnable", "hook failed", "hook registry", "hook"], "hook_failure", 0.80),
    (["not found", "no element", "strict mode violation", "selector"], "element_not_found", 0.80),
    (["assert", "expected", "verify"], "assertion_failure", 0.75),
    (["econnrefused", "enotfound", "network", "docker"], "infrastructure", 0.70),
]

VALID_CATEGORIES = [
    "passed",
    "timeout",
    "appium_startup",
    "browser_disconnect",
    "element_not_found",
    "assertion_failure",
    "hook_failure",
    "infrastructure",
    "unknown_failure",
]


@dataclass
class FailureClassification:
    category: str
    confidence: float
    evidence: list[str] = field(default_factory=list)
    recent_related_count: int = 0


def _collect_strings(value, output=None, limit=80):
    """Recursively collect string values from nested structures."""
    if output is None:
        output = []
    if len(output) >= limit:
        return output
    if isinstance(value, str) and value.strip():
        output.append(value)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _collect_strings(item, output, limit)
    elif isinstance(value, dict):
        for v in value.values():
            _collect_strings(v, output, limit)
    return output


def classify_failure(
    status: Optional[str] = None,
    error_texts: Optional[list[str]] = None,
    logs: Optional[list[str]] = None,
    recent_related_count: int = 0,
) -> FailureClassification:
    """Classify a failure from available evidence.

    Args:
        status: Run status (e.g., 'passed', 'failed', 'cancelled')
        error_texts: Error messages from the run
        logs: Log output from the run
        recent_related_count: Number of recent related runs (for context)

    Returns:
        FailureClassification with category, confidence, and evidence.
    """
    # Not a failure
    if status and status != "failed":
        return FailureClassification(
            category="passed",
            confidence=0.95,
            evidence=[f"Run status is {status}."],
            recent_related_count=recent_related_count,
        )

    # Collect evidence strings
    evidence_inputs = []
    if error_texts:
        evidence_inputs.extend(error_texts)
    if logs:
        evidence_inputs.extend(logs)

    evidence = _collect_strings(evidence_inputs, limit=80)
    haystack = "\n".join(evidence).lower()

    # Priority-ordered needle matching
    for needles, category, confidence in FAILURE_CHECKS:
        match = next((n for n in needles if n in haystack), None)
        if match is not None:
            # Find the evidence string containing the matched needle
            matching_evidence = next(
                (e for e in evidence if match in e.lower()),
                evidence[0] if evidence else match,
            )
            return FailureClassification(
                category=category,
                confidence=confidence,
                evidence=[matching_evidence],
                recent_related_count=recent_related_count,
            )

    # Fallback
    return FailureClassification(
        category="unknown_failure",
        confidence=0.30,
        evidence=evidence[:5],
        recent_related_count=recent_related_count,
    )
