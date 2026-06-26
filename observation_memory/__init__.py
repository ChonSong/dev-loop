"""Observation Memory — self-correcting behavioral knowledge for dev loops.

Usage:
    from observation_memory import ObservationStore, MemoryIndex, curate, classify_failure, CircuitBreaker

    # Query memory before a review
    store = ObservationStore("~/.coach-memory")
    index = MemoryIndex(store).build(product="gto-wizard")
    context = index.query("review the study page preflop tab", step_index=0)
    # → injects <memory-context>...</memory-context> into LLM prompt

    # Classify failures
    result = classify_failure(status="failed", error_texts=["timeout after 30s"])
    # → FailureClassification(category="timeout", confidence=0.90)

    # Curate observations after a review
    log = curate(
        memory_root="~/.coach-memory",
        project="gto-wizard",
        review_summary="Study page preflop review",
        findings=["Preflop tab loads correctly", "Position buttons highlight on click"],
        status="passed",
        task_id="task-1",
    )
    # → {added: 1, confirmed: 2, deprecated: 0, deleted: 0, deltas: [...], errors: []}
"""

from .schema import Observation
from .store import ObservationStore
from .index import MemoryIndex
from .curator import curate, run_curator
from .circuit_breaker import CircuitBreaker, CircuitBreakerConfig
from .classifier import classify_failure, FailureClassification
from .similarity import jaccard_similarity, find_similar

__all__ = [
    "Observation",
    "ObservationStore",
    "MemoryIndex",
    "curate",
    "run_curator",
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "classify_failure",
    "FailureClassification",
    "jaccard_similarity",
    "find_similar",
]
