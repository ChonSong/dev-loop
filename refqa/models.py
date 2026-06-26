"""Pydantic models for RefQA test definitions and execution results."""

from __future__ import annotations

import re
from enum import Enum
from typing import Optional, Union

from pydantic import BaseModel, Field, field_validator


# ── LLM Action Models ──────────────────────────────────────────────────────


class ActionType(str, Enum):
    """Browser actions the LLM can output."""

    NAVIGATE = "navigate"
    CLICK = "click"
    TYPE = "type"
    SELECT = "select"
    WAIT = "wait"
    VERIFY_TEXT = "verify_text"
    VERIFY_ELEMENT = "verify_element"
    SCREENSHOT = "screenshot"
    HOVER = "hover"


class BrowserAction(BaseModel):
    """A single browser action produced by the LLM."""

    action: ActionType
    selector: Optional[str] = None
    value: Optional[str] = None
    url: Optional[str] = None
    description: str = ""


class ActionPlan(BaseModel):
    """Structured plan returned by the LLM for a step."""

    actions: list[BrowserAction]
    reasoning: str = ""


# ── Test Definition Models ─────────────────────────────────────────────────


class Target(BaseModel):
    """A named target (app under test or reference app)."""

    name: str
    url: str
    browser: Optional[str] = None  # e.g. "chromium", "firefox", "webkit"


class TestTargets(BaseModel):
    """Target definitions for a test.

    Accepts two forms in YAML:
      1. Simple names: ``primary: gto-wizard``
      2. Full objects: ``primary: {name: gto-wizard, url: https://...}``

    Simple names are resolved via the ``url_map`` passed at runtime.
    """

    primary: Union[str, Target]
    references: list[Union[str, Target]] = []

    def resolve(self, url_map: dict[str, str]) -> tuple[Target, list[Target]]:
        """Resolve all targets to full ``Target`` objects using *url_map*."""
        primary = self._resolve_one(self.primary, url_map)

        refs: list[Target] = []
        for ref in self.references:
            refs.append(self._resolve_one(ref, url_map))

        return primary, refs

    @staticmethod
    def _resolve_one(item: Union[str, Target], url_map: dict[str, str]) -> Target:
        if isinstance(item, Target):
            return item
        name = item  # plain string
        url = url_map.get(name)
        if not url:
            raise ValueError(
                f"Target {name!r} has no URL. "
                f"Provide it inline in the YAML or pass a --targets-url-map."
            )
        return Target(name=name, url=url)


class Step(BaseModel):
    """A single test step.

    In YAML, a step can be:
    - A plain string: ``- Click on "UTG"``
    - A dict with a description and optional reference:
      ``- description: Verify cell "AA"
         reference: app-gtowizard``
    """

    description: str
    reference: Optional[str] = None

    @classmethod
    def from_yaml_item(cls, item: Union[str, dict]) -> "Step":
        if isinstance(item, str):
            return cls(description=item)
        if isinstance(item, dict):
            return cls(
                description=item.get("description", item.get("", "")),
                reference=item.get("reference"),
            )
        raise ValueError(
            f"Step must be a string or dict, got {type(item).__name__}: {item!r}"
        )


class Test(BaseModel):
    """Top-level test definition."""

    test_id: str = Field(alias="test-id")
    name: str
    targets: TestTargets
    workers: int = Field(default=2, ge=1, le=10)
    steps: list[Step]

    @field_validator("test_id", mode="before")
    @classmethod
    def validate_test_id(cls, v: str) -> str:
        if not v or not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                f"test-id must be non-empty alphanumeric/dash/underscore, got {v!r}"
            )
        return v

    @field_validator("steps", mode="before")
    @classmethod
    def coerce_steps(cls, v: list) -> list[Step]:
        return [Step.from_yaml_item(item) for item in v]

    model_config = {"populate_by_name": True}


# ── Execution Result Models ────────────────────────────────────────────────


class StepResult(BaseModel):
    """Result of executing a single step."""

    step_index: int
    description: str
    success: bool
    primary_result: Optional[dict] = None
    reference_result: Optional[dict] = None
    match: Optional[bool] = None
    error: Optional[str] = None
    attempts: int = 1


class RunResult(BaseModel):
    """Aggregated result of running an entire test."""

    test_id: str
    name: str
    success: bool
    step_results: list[StepResult]
    total_steps: int
    passed_steps: int
    failed_steps: int
    duration_seconds: float
