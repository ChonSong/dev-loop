"""File-based observation store — markdown files with YAML frontmatter.

Mirrors agent-qa's observation-io.ts: each observation is a .md file with
YAML frontmatter (trust, confirmed_count, etc.) and markdown body.

Directory structure:
    {root}/
      products/{name}/   — product-level observations (structural, navigational)
      suites/{id}/        — suite-level observations (cross-test patterns)
      tasks/{id}/         — task-level observations (test-specific quirks)
"""

from __future__ import annotations

import os
import re
import yaml
from pathlib import Path
from typing import Optional
from .schema import Observation


def _frontmatter_split(raw: str) -> tuple[dict, str]:
    """Parse YAML frontmatter from markdown file. Returns (metadata, body)."""
    if not raw.startswith("---"):
        return {}, raw

    parts = raw.split("---", 2)
    if len(parts) < 3:
        return {}, raw

    try:
        meta = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        meta = {}

    body = parts[2].strip()
    return meta, body


def _to_frontmatter(obs: Observation) -> str:
    """Serialize observation to markdown with YAML frontmatter."""
    meta = {
        "id": obs.id,
        "title": obs.title,
        "trust": obs.trust,
        "created": obs.created,
        "last_confirmed": obs.last_confirmed,
        "confirmed_count": obs.confirmed_count,
        "contradicted_count": obs.contradicted_count,
        "source_review": obs.source_review,
    }
    if obs.position is not None:
        meta["position"] = obs.position
    if obs.suite_snapshot is not None:
        meta["suite_snapshot"] = obs.suite_snapshot

    yaml_block = yaml.dump(meta, default_flow_style=False, sort_keys=False).strip()
    return f"---\n{yaml_block}\n---\n\n{obs.content}\n"


def _validate_path_component(value: str) -> bool:
    """Reject path components with .. or / to prevent traversal."""
    return not (".." in value or "/" in value or "\\" in value or "\0" in value)


class ObservationStore:
    """File-based CRUD for observations."""

    def __init__(self, root: str):
        self.root = Path(root)

    # ---- Tier directory helpers ----

    def _tier_dir(self, tier: str, scope: str) -> Path:
        """Get directory for a given tier and scope."""
        if not _validate_path_component(scope):
            raise ValueError(f"Invalid scope: {scope}")
        return self.root / tier / scope

    def _obs_path(self, tier: str, scope: str, obs_id: str) -> Path:
        """Get path for a specific observation file."""
        if not _validate_path_component(obs_id):
            raise ValueError(f"Invalid observation ID: {obs_id}")
        return self._tier_dir(tier, scope) / f"{obs_id}.md"

    # ---- Read ----

    def read(self, tier: str, scope: str, obs_id: str) -> Optional[Observation]:
        """Read a single observation by ID."""
        path = self._obs_path(tier, scope, obs_id)
        if not path.exists():
            return None

        raw = path.read_text()
        meta, body = _frontmatter_split(raw)
        meta["content"] = body
        return Observation.from_dict(meta)

    def list(self, tier: str, scope: str) -> list[Observation]:
        """List all observations in a tier/scope."""
        dir_path = self._tier_dir(tier, scope)
        if not dir_path.exists():
            return []

        results = []
        for f in sorted(dir_path.iterdir()):
            if not f.name.endswith(".md"):
                continue
            obs_id = f.stem
            obs = self.read(tier, scope, obs_id)
            if obs:
                results.append(obs)
        return results

    def list_all(self) -> list[Observation]:
        """List ALL observations across all tiers and scopes."""
        results = []
        for tier in ("products", "suites", "tasks"):
            tier_dir = self.root / tier
            if not tier_dir.exists():
                continue
            for scope_dir in tier_dir.iterdir():
                if scope_dir.is_dir():
                    results.extend(self.list(tier, scope_dir.name))
        return results

    def list_tier(self, tier: str) -> list[Observation]:
        """List all observations in a tier (across all scopes)."""
        results = []
        tier_dir = self.root / tier
        if not tier_dir.exists():
            return results
        for scope_dir in tier_dir.iterdir():
            if scope_dir.is_dir():
                results.extend(self.list(tier, scope_dir.name))
        return results

    # ---- Write ----

    def write(self, tier: str, scope: str, obs: Observation) -> str:
        """Write (create or update) an observation. Returns the file path."""
        dir_path = self._tier_dir(tier, scope)
        dir_path.mkdir(parents=True, exist_ok=True)

        path = self._obs_path(tier, scope, obs.id)
        path.write_text(_to_frontmatter(obs))
        return str(path)

    def delete(self, tier: str, scope: str, obs_id: str) -> bool:
        """Delete an observation. Returns True if it existed."""
        path = self._obs_path(tier, scope, obs_id)
        if path.exists():
            path.unlink()
            return True
        return False

    # ---- Utility ----

    def exists(self, tier: str, scope: str, obs_id: str) -> bool:
        """Check if an observation exists."""
        return self._obs_path(tier, scope, obs_id).exists()
