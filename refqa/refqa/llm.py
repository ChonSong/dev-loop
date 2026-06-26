"""LLM client that resolves natural-language steps into structured action plans.

Calls the OpenCode Zen API (OpenAI-compatible) with model ``mimo-v2.5-free``.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

import httpx

from .models import ActionPlan, BrowserAction

# ── Helpers ────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a browser automation assistant. Given a natural-language step
description, output a JSON object with an "actions" array of browser actions.

Each action has:
- "action": one of "navigate", "click", "type", "select", "wait", "verify_text", \
"verify_element", "screenshot", "hover"
- "selector": a CSS selector for the target element (omit for "navigate", "wait", "screenshot")
- "value": text to type or verify (omit when not needed)
- "url": target URL (only for "navigate")
- "description": a brief human-readable description of what this action does

SELECTOR RULES (most important):
- Prefer aria-label selectors: [aria-label="UTG position, 100bb stack, active"]
- Prefer role selectors: [role="gridcell"], [role="button"]
- Prefer data-testid selectors: [data-testid="..."]
- Use :has-text() sparingly and narrow by context (e.g. button:has-text("UTG"))
- For position cards, use aria-label like [aria-label="UTG position, 100bb stack, active"]
- For grid cells in the hand matrix, use [role="gridcell"]
- For verify_text, use a specific selector that targets only ONE element

CRITICAL: Do NOT use generic selectors like div:has-text("UTG") that match 13 elements.
Always narrow the selector to the specific UI component.

IMPORTANT constraints:
- Output ONLY valid JSON, no markdown fences, no extra text.
- For verify_text actions, include a specific selector AND the expected value.
- Break compound steps into multiple actions in order.

Example:
Input: Navigate to "https://example.com" and click the "Login" button
Output: {"actions": [{"action": "navigate", "url": "https://example.com", \
"description": "Navigate to example.com"}, {"action": "click", \
"selector": "button:has-text('Login')", "description": "Click Login button"}]}"""


def _resolve_api_key() -> str:
    """Return the OpenCode Zen API key.

    Priority:
    1. ``OPENCODE_ZEN_API_KEY`` environment variable
    2. ``~/.hermes/.env`` file (Hermes credential store)
    3. ``~/.hermes/auth.json`` credential pool key ``opencode-zen``
    """
    env_key = os.environ.get("OPENCODE_ZEN_API_KEY")
    if env_key:
        return env_key

    # Check ~/.hermes/.env (Hermes credential store, loaded by agent but not inherited by shells).
    hermes_env = Path.home() / ".hermes" / ".env"
    if hermes_env.exists():
        try:
            for line in hermes_env.read_text().splitlines():
                line = line.strip()
                if line.startswith("OPENCODE_ZEN_API_KEY="):
                    val = line.split("=", 1)[1].strip("\"'")
                    if val:
                        return val
        except (OSError, ValueError):
            pass

    auth_path = Path.home() / ".hermes" / "auth.json"
    if auth_path.exists():
        try:
            data = json.loads(auth_path.read_text())
            pool = data.get("credential_pool", {})
            entries = pool.get("opencode-zen", [])
            # entries is a list of credential dicts — take the first valid one
            for entry in entries if isinstance(entries, list) else [entries]:
                key = entry.get("access_token", "")
                if key:
                    return key
        except (json.JSONDecodeError, KeyError, OSError):
            pass

    raise RuntimeError(
        "OpenCode Zen API key not found. "
        "Set OPENCODE_ZEN_API_KEY or configure ~/.hermes/auth.json "
        "with credential_pool.opencode-zen.api_key"
    )


# ── Client ─────────────────────────────────────────────────────────────────


class ZenClient:
    """An HTTP client for the OpenCode Zen /chat/completions endpoint."""

    BASE_URL = "https://opencode.ai/zen/v1/chat/completions"
    MODEL = "mimo-v2.5-free"
    DEFAULT_TIMEOUT = 60.0

    def __init__(self, api_key: Optional[str] = None, timeout: float = DEFAULT_TIMEOUT):
        self.api_key = api_key or _resolve_api_key()
        self._http = httpx.Client(timeout=httpx.Timeout(timeout))

    def resolve(
        self,
        step_description: str,
        page_context: str = "",
    ) -> ActionPlan:
        """Send *step_description* to the LLM and parse the structured reply.

        Parameters
        ----------
        step_description:
            The natural-language step from the test YAML.
        page_context:
            Optional HTML snapshot / error context for self-healing retries.

        Returns
        -------
        ActionPlan
        """
        user_content = f"Step: {step_description}"
        if page_context:
            user_content += f"\n\nCurrent page context:\n{page_context[:4000]}"

        payload = {
            "model": self.MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.1,
            "max_tokens": 2048,
        }

        resp = self._http.post(
            self.BASE_URL,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        resp.raise_for_status()
        body = resp.json()

        raw_content = body["choices"][0]["message"].get("content")

        # Handle empty/null content from the LLM.
        raw_content = raw_content or "{}"
        raw_content = str(raw_content).strip()
        if raw_content.startswith("```"):
            raw_content = raw_content.strip("`")
            if raw_content.startswith("json"):
                raw_content = raw_content[4:]
            raw_content = raw_content.strip()

        data = json.loads(raw_content)
        if isinstance(data, list):
            # Some models return an array directly.
            return ActionPlan(actions=[BrowserAction(**a) for a in data])
        if not data or "actions" not in data:
            raise ValueError(
                f"LLM returned invalid plan (no 'actions' key): "
                f"{str(raw_content)[:200]}"
            )
        return ActionPlan(**data)

    def close(self) -> None:
        self._http.close()
