"""Observation schema — models behavioral knowledge about projects.

Mirrors agent-qa's observation schema but uses Python dataclasses instead of Zod.
Observations are behavioral facts ("the modal appears after a 2s delay"),
NOT testing strategies ("wait 3s then click the button").
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional
import uuid


@dataclass
class Observation:
    """A single behavioral observation about a project/application."""

    id: str  # obs_ + 10 id-agent words (mirrors agent-qa canonical IDs)
    title: str  # context-first fact headline
    content: str  # explanatory body (markdown allowed)
    trust: float = 0.5  # 0.0–1.0
    created: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_confirmed: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    confirmed_count: int = 0
    contradicted_count: int = 0
    source_review: str = ""  # what review/session created this

    # Suite-level observations can carry position + snapshot
    position: Optional[int] = None
    suite_snapshot: Optional[list[dict]] = None

    def confirm(self, delta: float = 0.02) -> None:
        """Increase trust on confirmation."""
        self.trust = round(min(1.0, self.trust + delta), 3)
        self.confirmed_count += 1
        self.last_confirmed = datetime.now(timezone.utc).isoformat()

    def contradict(self, delta: float = 0.05) -> bool:
        """Decrease trust on contradiction. Returns True if trust fell to zero."""
        self.trust = round(max(0.0, self.trust - delta), 3)
        self.contradicted_count += 1
        return self.trust < 1e-9  # effectively zero → delete

    @property
    def is_dead(self) -> bool:
        return self.trust < 1e-9

    @classmethod
    def from_dict(cls, d: dict) -> "Observation":
        return cls(**{k: v for k, v in d.items() if k in cls.__annotations__})

    def to_dict(self) -> dict:
        return asdict(self)


# Trust thresholds (mirrors agent-qa defaults)
DEFAULT_TRUST_CONFIRM_DELTA = 0.02
DEFAULT_TRUST_CONTRADICT_DELTA = 0.05
DEFAULT_MIN_TRUST = 0.3
DEFAULT_MAX_INJECTIONS = 3
