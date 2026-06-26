"""Circuit breaker for memory safety.

Mirrors agent-qa's circuit-breaker.ts:
- Rolling window of recent review outcomes (default 20)
- Two cohorts: reviews with memory injected vs baseline (without memory)
- Trips when memory cohort fail rate exceeds baseline by > threshold (default 0.15)
- Once tripped, stays tripped — requires manual reset
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ReviewOutcome:
    with_memory: bool
    passed: bool


@dataclass
class CircuitBreakerConfig:
    window_size: int = 20
    baseline_size: int = 3  # minimum cohort size before evaluation
    threshold: float = 0.15  # max allowed memory degradation


class CircuitBreaker:
    """Tracks review outcomes and trips when memory hurts more than it helps."""

    config: CircuitBreakerConfig
    window: list[ReviewOutcome]
    _tripped: bool

    def __init__(self, config: Optional[CircuitBreakerConfig] = None):
        self.config = config or CircuitBreakerConfig()
        self.window = []
        self._tripped = False

    def record(self, with_memory: bool, passed: bool) -> None:
        """Record a review outcome and re-evaluate."""
        self.window.append(ReviewOutcome(with_memory=with_memory, passed=passed))
        if len(self.window) > self.config.window_size:
            self.window.pop(0)
        self._evaluate()

    def is_tripped(self) -> bool:
        """Check if the circuit breaker has tripped."""
        return self._tripped

    def reset(self) -> None:
        """Manually reset the circuit breaker."""
        self._tripped = False

    def _evaluate(self) -> None:
        """Evaluate whether memory is making things worse."""
        if self._tripped:
            return

        baseline = [o for o in self.window if not o.with_memory]
        memory = [o for o in self.window if o.with_memory]

        if len(baseline) < self.config.baseline_size or len(memory) < self.config.baseline_size:
            return

        baseline_fail_rate = sum(1 for o in baseline if not o.passed) / len(baseline)
        memory_fail_rate = sum(1 for o in memory if not o.passed) / len(memory)

        if (memory_fail_rate - baseline_fail_rate) > self.config.threshold:
            self._tripped = True

    def status(self) -> dict:
        """Return current state for logging/debugging."""
        baseline = [o for o in self.window if not o.with_memory]
        memory = [o for o in self.window if o.with_memory]
        return {
            "tripped": self._tripped,
            "window_size": len(self.window),
            "baseline_count": len(baseline),
            "memory_count": len(memory),
            "baseline_fail_rate": sum(1 for o in baseline if not o.passed) / len(baseline) if baseline else 0,
            "memory_fail_rate": sum(1 for o in memory if not o.passed) / len(memory) if memory else 0,
            "threshold": self.config.threshold,
        }
