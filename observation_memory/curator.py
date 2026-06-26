"""A.U.D.N. Memory Curator — LLM-driven observation management.

Mirrors agent-qa's curator.ts: after each successful review, evaluates findings
using the AUDN framework (Add/Update/Deprecate/Noop) and manages observation
lifecycle with trust scoring.

The curator's system prompt enforces:
- Behavioral facts ONLY ("modal appears after 2s delay"), NOT strategies ("wait 3s")
- Product scope: structural + navigational facts (moderately selective)
- Task scope: only when review shows agent exploration/difficulty (highly selective)
- Prefer UPDATE over ADD to avoid duplicates
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from typing import Optional

from .schema import (
    Observation,
    DEFAULT_TRUST_CONFIRM_DELTA,
    DEFAULT_TRUST_CONTRADICT_DELTA,
)
from .store import ObservationStore
from .similarity import find_similar
from .index import MemoryIndex


CURATOR_SYSTEM_PROMPT = """You are a memory curator for a code review system. After each successful review, you evaluate whether any behavioral observations about the project are worth remembering.

Your decisions use the A.U.D.N. framework:
- ADD: Record a new behavioral observation about the project.
- UPDATE: Confirm an existing observation that was relevant and correct during this review.
- DEPRECATE: Mark an observation as contradicted by what happened in this review.
- NOOP: No action needed — the review did not reveal anything worth remembering.

Rules:
- Observations MUST be behavioral facts about the project ("the GTO study page loads ranges only after clicking a position button"), NOT review strategies ("check the position button first").
- Every ADD decision MUST include both a 'title' and a 'content' body.
- Titles must read like context-first fact headlines that help retrieval later, for example "Study page: position selection triggers range loading".
- Keep the title out of the body. The body should start with the explanation, not a repeated heading.
- For update (confirm): only confirm observations that were actually relevant and correct during this review.
- For deprecate: only deprecate observations that are clearly contradicted by what happened in this review.
- If existing observations cover the same behavior, prefer "update" over "add" to avoid duplicates.
- Do NOT fabricate observation IDs. Only reference IDs that appear in the provided context.

Scope-specific selectivity:
- PRODUCT scope: Moderately selective. Capture structural and navigational facts — page layout, component states, API behavior, build quirks.
  PRODUCT scope writing style:
  - Title: context-first fact headline with strong page or workflow keywords.
  - Body: a compact explanatory paragraph first. Markdown allowed only when it genuinely improves clarity.
  DO capture:
  - "The study page has preflop, flop, turn, and river tabs"
  - "The build requires pnpm instead of npm"
  - "The /api/study endpoint returns 401 without auth cookies"
  DO NOT capture:
  - "There is a submit button" (too granular, trivially discoverable)
  - "The page uses React" (technology detail, not behavioral)

- TASK scope: Highly selective. Only add task-scoped observations when the review shows exploration or difficulty.
  TASK scope writing style:
  - Title: scenario-specific fact headline.
  - Body: keep it short, usually one concise paragraph.
  - Only create task observations for genuinely surprising behavior (unexpected delays, dynamic content loading, edge cases that cost review time).

When deciding scope: use "product" for behaviors that apply across the whole project, and "task" for behaviors specific to a single review finding. If no task context is provided, do NOT use "task" scope."""


def _build_curator_user_message(
    project: str,
    review_summary: str,
    findings: list[str],
    status: str,
    existing_observations: list[dict],
    injected_ids: list[str],
    task_context: Optional[str] = None,
) -> str:
    """Build the user message for the curator LLM call."""
    lines = [
        f"Project: {project}",
        f"Review status: {status}",
        f"Task context: {task_context if task_context else 'none — do not use task scope'}",
        "",
        "## Review findings",
    ]

    for i, finding in enumerate(findings, 1):
        lines.append(f"### Finding {i}")
        lines.append(finding)
        lines.append("")

    if existing_observations:
        lines.append("## ALL existing observations for this project")
        for obs in existing_observations:
            trusted = "injected" if obs["id"] in injected_ids else "available"
            lines.append(
                f"- [{obs['id']}] [{trusted}] {obs['title']} "
                f"(trust: {obs['trust']:.2f}): {obs['content']}"
            )
        lines.append("")

    return "\n".join(lines)


def _call_llm(prompt: str) -> dict:
    """Call the LLM for curator decisions.

    Uses the HERMES_MODEL env var or falls back to configured defaults.
    Returns parsed JSON from the LLM response.
    """
    import subprocess
    import tempfile

    # Write prompt to temp file for the LLM to read
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, prefix="curator-") as f:
        f.write(prompt)
        prompt_file = f.name

    try:
        # Try using hermes CLI if available
        result = subprocess.run(
            [
                "hermes", "run",
                "--prompt-file", prompt_file,
                "--json",
                "--no-tools",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0 and result.stdout.strip():
            # Extract JSON from response
            text = result.stdout.strip()
            # Find JSON block
            json_match = re.search(r"\{[\s\S]*\}", text)
            if json_match:
                return json.loads(json_match.group(0))
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
        pass
    finally:
        os.unlink(prompt_file)

    # Fallback: return empty decisions (no LLM available)
    return {"decisions": [{"action": "noop", "reasoning": "LLM unavailable — curator skipped"}]}


def run_curator(
    store: ObservationStore,
    memory_index: MemoryIndex,
    project: str,
    review_summary: str,
    findings: list[str],
    status: str,
    task_id: Optional[str] = None,
    confirm_delta: float = DEFAULT_TRUST_CONFIRM_DELTA,
    contradict_delta: float = DEFAULT_TRUST_CONTRADICT_DELTA,
    llm_call: bool = True,
) -> dict:
    """Run the curator after a review completes.

    Args:
        store: ObservationStore instance
        memory_index: MemoryIndex that was used for this review (for injected IDs)
        project: Project name
        review_summary: Summary of the review
        findings: List of review findings (one per key observation)
        status: Review status ('passed', 'failed', etc.)
        task_id: Optional task ID for task-scoped observations
        confirm_delta: Trust increase on confirmation (default 0.02)
        contradict_delta: Trust decrease on contradiction (default 0.05)
        llm_call: Whether to call the LLM curator (False = dry run)

    Returns:
        Dict with log: {added, confirmed, deprecated, deleted, deltas, errors, duration_ms}
    """
    start = datetime.now(timezone.utc)
    log = {
        "added": 0,
        "confirmed": 0,
        "deprecated": 0,
        "deleted": 0,
        "deltas": [],
        "errors": [],
    }

    # On failure, auto-deprecate injected observations
    if status == "failed":
        injected_ids = memory_index.get_injected_ids(0)
        for obs_id in injected_ids:
            # Find and contradict each injected observation
            for tier in ("products", "suites", "tasks"):
                scopes = []
                tier_dir = store.root / tier
                if not tier_dir.exists():
                    continue
                for scope_dir in tier_dir.iterdir():
                    if scope_dir.is_dir():
                        scopes.append(scope_dir.name)

                for scope in scopes:
                    obs = store.read(tier, scope, obs_id)
                    if obs:
                        before = obs.to_dict()
                        is_dead = obs.contradict(contradict_delta)
                        if is_dead:
                            store.delete(tier, scope, obs_id)
                            log["deleted"] += 1
                            log["deltas"].append({
                                "action": "delete",
                                "tier": tier,
                                "scope": scope,
                                "observationId": obs_id,
                                "reasoning": f"Failure contradicted injected observation {obs_id}",
                                "before": before,
                                "after": None,
                            })
                        else:
                            store.write(tier, scope, obs)
                            log["deprecated"] += 1
                            log["deltas"].append({
                                "action": "deprecate",
                                "tier": tier,
                                "scope": scope,
                                "observationId": obs_id,
                                "reasoning": f"Failure contradicted injected observation {obs_id}",
                                "before": before,
                                "after": obs.to_dict(),
                            })
                        break
                else:
                    continue
                break

        log["duration_ms"] = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)
        return log

    # Only run full curator on passed reviews
    if status != "passed":
        log["duration_ms"] = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)
        return log

    # Collect existing observations for dedup context
    existing = store.list_tier("products")
    existing_dicts = [{"id": o.id, "title": o.title, "content": o.content, "trust": o.trust} for o in existing]

    injected_ids = memory_index.get_injected_ids(0)

    # LLM curator call
    if llm_call:
        user_msg = _build_curator_user_message(
            project=project,
            review_summary=review_summary,
            findings=findings,
            status=status,
            existing_observations=existing_dicts,
            injected_ids=injected_ids,
            task_context=task_id,
        )
        full_prompt = f"{CURATOR_SYSTEM_PROMPT}\n\n---\n\n{user_msg}"

        try:
            response = _call_llm(full_prompt)
            decisions = response.get("decisions", [])
        except Exception as e:
            log["errors"].append(f"LLM curator call failed: {e}")
            decisions = []
    else:
        decisions = []

    # Process decisions
    now = datetime.now(timezone.utc).isoformat()
    known_ids = {o["id"] for o in existing_dicts}

    for decision in decisions:
        action = decision.get("action", "noop")

        if action == "add":
            title = decision.get("title", "")
            content = decision.get("content", "")
            scope = decision.get("scope", "product")

            if not title or not content:
                log["errors"].append(f"ADD missing title or content: {decision}")
                continue

            # Check for near-duplicates
            similar = find_similar(f"{title} {content}", existing_dicts, threshold=0.85)
            if similar:
                log["errors"].append(f"ADD blocked by similarity to {similar[0]['id']}: {similar[0]['title']}")
                continue

            # Generate a simple ID (not canonical like agent-qa, but unique)
            import uuid
            obs_id = f"obs_{uuid.uuid4().hex[:12]}"

            tier = "tasks" if (scope == "task" and task_id) else "products"
            scope_value = task_id if (scope == "task" and task_id) else project

            obs = Observation(
                id=obs_id,
                title=title,
                content=content,
                trust=0.5,
                created=now,
                last_confirmed=now,
                confirmed_count=0,
                contradicted_count=0,
                source_review=review_summary[:200],
            )

            store.write(tier, scope_value, obs)
            log["added"] += 1
            log["deltas"].append({
                "action": "add",
                "tier": tier,
                "scope": scope_value,
                "observationId": obs_id,
                "reasoning": decision.get("reasoning", ""),
                "before": None,
                "after": obs.to_dict(),
            })

        elif action == "update":
            obs_id = decision.get("observationId", "")
            if not obs_id or obs_id not in known_ids:
                log["errors"].append(f"UPDATE: unknown observation ID {obs_id}")
                continue

            # Find the observation across all tiers
            obs = None
            found_tier = None
            found_scope = None
            for tier in ("products", "suites", "tasks"):
                tier_dir = store.root / tier
                if not tier_dir.exists():
                    continue
                for scope_dir in tier_dir.iterdir():
                    if not scope_dir.is_dir():
                        continue
                    o = store.read(tier, scope_dir.name, obs_id)
                    if o:
                        obs = o
                        found_tier = tier
                        found_scope = scope_dir.name
                        break
                if obs:
                    break

            if obs is None:
                log["errors"].append(f"UPDATE: observation not found: {obs_id}")
                continue

            before = obs.to_dict()
            obs.confirm(confirm_delta)
            store.write(found_tier, found_scope, obs)
            log["confirmed"] += 1
            log["deltas"].append({
                "action": "confirm",
                "tier": found_tier,
                "scope": found_scope,
                "observationId": obs_id,
                "reasoning": decision.get("reasoning", ""),
                "before": before,
                "after": obs.to_dict(),
            })

        elif action == "deprecate":
            obs_id = decision.get("observationId", "")
            if not obs_id or obs_id not in known_ids:
                log["errors"].append(f"DEPRECATE: unknown observation ID {obs_id}")
                continue

            obs = None
            found_tier = None
            found_scope = None
            for tier in ("products", "suites", "tasks"):
                tier_dir = store.root / tier
                if not tier_dir.exists():
                    continue
                for scope_dir in tier_dir.iterdir():
                    if not scope_dir.is_dir():
                        continue
                    o = store.read(tier, scope_dir.name, obs_id)
                    if o:
                        obs = o
                        found_tier = tier
                        found_scope = scope_dir.name
                        break
                if obs:
                    break

            if obs is None:
                log["errors"].append(f"DEPRECATE: observation not found: {obs_id}")
                continue

            before = obs.to_dict()
            is_dead = obs.contradict(contradict_delta)
            if is_dead:
                store.delete(found_tier, found_scope, obs_id)
                log["deleted"] += 1
                log["deltas"].append({
                    "action": "delete",
                    "tier": found_tier,
                    "scope": found_scope,
                    "observationId": obs_id,
                    "reasoning": decision.get("reasoning", ""),
                    "before": before,
                    "after": None,
                })
            else:
                store.write(found_tier, found_scope, obs)
                log["deprecated"] += 1
                log["deltas"].append({
                    "action": "deprecate",
                    "tier": found_tier,
                    "scope": found_scope,
                    "observationId": obs_id,
                    "reasoning": decision.get("reasoning", ""),
                    "before": before,
                    "after": obs.to_dict(),
                })

        # noop: nothing to do

    log["duration_ms"] = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)
    return log


def curate(
    memory_root: str,
    project: str,
    review_summary: str,
    findings: list[str],
    status: str,
    task_id: Optional[str] = None,
    llm_call: bool = True,
) -> dict:
    """Convenience wrapper: build index, run curator, return log.

    This is the main entry point for integration.
    """
    store = ObservationStore(memory_root)
    index = MemoryIndex(store).build(product=project, task_id=task_id)

    return run_curator(
        store=store,
        memory_index=index,
        project=project,
        review_summary=review_summary,
        findings=findings,
        status=status,
        task_id=task_id,
        llm_call=llm_call,
    )
