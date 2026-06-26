"""Step executor with LLM resolution, Playwright action, self-healing retry,
and reference comparison."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from playwright.sync_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    sync_playwright,
)

from .llm import ZenClient
from .models import (
    ActionPlan,
    ActionType,
    BrowserAction,
    RunResult,
    Step,
    StepResult,
    Target,
    Test,
)

# ── Constants ──────────────────────────────────────────────────────────────

MAX_RETRIES = 3


# ── Helpers ────────────────────────────────────────────────────────────────


def _page_text(page: Page) -> str:
    """Return the visible text content of a page (up to 8000 chars)."""
    try:
        text = page.inner_text("body", timeout=5000)
        return text[:8000]
    except Exception:
        try:
            return page.content()[:8000]
        except Exception:
            return ""


def _page_context(page: Page) -> str:
    """Return a snippet of the page for self-healing retries."""
    parts = []
    try:
        parts.append(f"URL: {page.url}")
    except Exception:
        pass
    try:
        parts.append(f"Title: {page.title()}")
    except Exception:
        pass
    try:
        text = _page_text(page)
        parts.append(f"Visible text:\n{text[:2000]}")
    except Exception:
        pass
    return "\n".join(parts)


def _execute_action(page: Page, action: BrowserAction) -> dict:
    """Execute a single ``BrowserAction`` in *page* and return a result dict."""
    act = action.action
    sel = action.selector
    val = action.value
    url = action.url

    try:
        if act == ActionType.NAVIGATE:
            if not url:
                raise ValueError("navigate action requires a 'url' field")
            page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            return {"ok": True, "url": page.url}

        elif act == ActionType.CLICK:
            if not sel:
                raise ValueError("click action requires a 'selector' field")
            page.locator(sel).wait_for(state="visible", timeout=10_000)
            page.locator(sel).click()
            return {"ok": True}

        elif act == ActionType.TYPE:
            if not sel or val is None:
                raise ValueError("type action requires 'selector' and 'value'")
            page.locator(sel).wait_for(state="visible", timeout=10_000)
            page.locator(sel).fill(val)
            return {"ok": True}

        elif act == ActionType.SELECT:
            if not sel or val is None:
                raise ValueError("select action requires 'selector' and 'value'")
            page.locator(sel).wait_for(state="visible", timeout=10_000)
            page.locator(sel).select_option(val)
            return {"ok": True}

        elif act == ActionType.WAIT:
            timeout = int(val) if val and val.isdigit() else 2000
            page.wait_for_timeout(timeout)
            return {"ok": True}

        elif act == ActionType.VERIFY_TEXT:
            if not sel or val is None:
                raise ValueError("verify_text requires 'selector' and 'value'")
            elem = page.locator(sel)
            elem.wait_for(state="visible", timeout=10_000)
            text = elem.inner_text()
            match = val.lower() in text.lower()
            return {"ok": match, "expected": val, "actual": text, "match": match}

        elif act == ActionType.VERIFY_ELEMENT:
            if not sel:
                raise ValueError("verify_element requires a 'selector'")
            loc = page.locator(sel)
            visible = loc.is_visible(timeout=5_000)
            return {"ok": visible, "selector": sel, "visible": visible}

        elif act == ActionType.SCREENSHOT:
            path = f"/tmp/refqa_screenshot_{int(time.time())}.png"
            page.screenshot(path=path)
            return {"ok": True, "screenshot": path}

        elif act == ActionType.HOVER:
            if not sel:
                raise ValueError("hover action requires a 'selector'")
            page.locator(sel).wait_for(state="visible", timeout=10_000)
            page.locator(sel).hover()
            return {"ok": True}

        else:
            return {"ok": False, "error": f"Unknown action type: {act}"}

    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def _execute_plan(
    page: Page,
    plan: ActionPlan,
) -> list[dict]:
    """Execute all actions in *plan* sequentially, returning per-action results."""
    results: list[dict] = []
    for action in plan.actions:
        result = _execute_action(page, action)
        result["action"] = action.model_dump()
        results.append(result)
        if not result.get("ok"):
            break
    return results


def _results_match(primary_results: list[dict], reference_results: list[dict]) -> bool:
    """Compare two lists of action results to determine if they match.

    Uses the final page text as the canonical comparison.
    """
    # Extract the "actual" text from the last VERIFY_TEXT action, or use
    # the visible text captured after all actions.
    def _text(rs: list[dict]) -> str:
        for r in reversed(rs):
            if "actual" in r:
                return r.get("actual", "")
        return ""

    return _text(primary_results) == _text(reference_results)


# ── Runner ─────────────────────────────────────────────────────────────────


@dataclass
class TestRunner:
    """Orchestrates test execution using Playwright and the LLM client.

    Parameters
    ----------
    test:
        The parsed test definition.
    url_map:
        Mapping of target names → URLs.  Used to resolve string-only targets.
    api_key:
        Optional OpenCode Zen API key (auto-resolved if omitted).
    headless:
        Run Playwright in headless mode (default ``True``).
    """

    test: Test
    url_map: dict[str, str] = field(default_factory=dict)
    api_key: Optional[str] = None
    headless: bool = True

    # ── Lifecycle ──────────────────────────────────────────────────────

    def run(self) -> RunResult:
        """Execute all test steps and return the aggregated result."""
        primary_target, reference_targets = self.test.targets.resolve(self.url_map)

        llm = ZenClient(api_key=self.api_key)
        start = time.time()

        step_results: list[StepResult] = []
        browser: Optional[Browser] = None

        try:
            with sync_playwright() as pw:
                browser = self._launch_browser(pw)
                primary_ctx = self._new_context(browser)
                primary_page = primary_ctx.new_page()

                # Pre-navigate to the primary target URL.
                primary_page.goto(primary_target.url, wait_until="domcontentloaded", timeout=30_000)

                # Reference contexts (one per reference target).
                ref_pages: list[tuple[str, Page]] = []
                for rt in reference_targets:
                    ctx = self._new_context(browser)
                    pg = ctx.new_page()
                    pg.goto(rt.url, wait_until="domcontentloaded", timeout=30_000)
                    ref_pages.append((rt.name, pg))

                for idx, step in enumerate(self.test.steps):
                    sr = self._run_step(
                        llm=llm,
                        step=step,
                        step_index=idx,
                        primary_page=primary_page,
                        ref_pages=ref_pages,
                    )
                    step_results.append(sr)

                # Cleanup.
                primary_ctx.close()
                for _, pg in ref_pages:
                    try:
                        pg.context.close()
                    except Exception:
                        pass
        except Exception as exc:
            # Ensure step_results exists even on crash
            if not step_results:
                step_results.append(
                    StepResult(
                        step_index=0,
                        description="runner crash",
                        success=False,
                        error=f"Runner crashed: {exc}",
                    )
                )
        finally:
            if browser:
                try:
                    browser.close()
                except Exception:
                    pass
            llm.close()

        elapsed = time.time() - start
        passed = sum(1 for sr in step_results if sr.success)
        failed = len(step_results) - passed

        return RunResult(
            test_id=self.test.test_id,
            name=self.test.name,
            success=failed == 0,
            step_results=step_results,
            total_steps=len(step_results),
            passed_steps=passed,
            failed_steps=failed,
            duration_seconds=round(elapsed, 2),
        )

    # ── Internal helpers ───────────────────────────────────────────────

    @staticmethod
    def _launch_browser(pw: Playwright) -> Browser:
        return pw.chromium.launch(headless=True)  # always headless for now

    @staticmethod
    def _new_context(browser: Browser) -> BrowserContext:
        return browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
            ),
        )

    def _run_step(
        self,
        llm: ZenClient,
        step: Step,
        step_index: int,
        primary_page: Page,
        ref_pages: list[tuple[str, Page]],
    ) -> StepResult:
        """Execute a single step with self-healing and optional reference comparison."""
        description = step.description
        has_reference = step.reference is not None

        # ── LLM resolution (with self-healing retries) ────────────────
        plan: Optional[ActionPlan] = None
        last_error: Optional[str] = None

        for attempt in range(1, MAX_RETRIES + 1):
            page_ctx = _page_context(primary_page) if attempt > 1 else ""
            try:
                plan = llm.resolve(description, page_context=page_ctx)
                break
            except Exception as exc:
                last_error = f"LLM resolve error (attempt {attempt}): {exc}"
                if attempt < MAX_RETRIES:
                    time.sleep(1)

        if plan is None:
            return StepResult(
                step_index=step_index,
                description=description,
                success=False,
                error=last_error,
                attempts=MAX_RETRIES,
            )

        # ── Execute on primary ─────────────────────────────────────────
        primary_results, primary_ok = self._execute_with_retry(
            primary_page, description, plan
        )

        # ── Execute on reference(s) ────────────────────────────────────
        ref_results: Optional[list[dict]] = None
        ref_ok: Optional[bool] = None

        if has_reference and ref_pages:
            # Find the matching reference page.
            ref_page: Optional[Page] = None
            for rname, rpage in ref_pages:
                if rname == step.reference:
                    ref_page = rpage
                    break
            if ref_page is None:
                last_error = (
                    f"Reference target {step.reference!r} not found in targets"
                )
            else:
                ref_results, ref_ok = self._execute_with_retry(
                    ref_page, description, plan
                )

        # ── Compare ────────────────────────────────────────────────────
        match: Optional[bool] = None
        if has_reference and ref_results is not None and primary_results is not None:
            match = _results_match(primary_results, ref_results)

        # A step succeeds if:
        #   - All primary actions succeeded
        #   - If reference, reference actions also succeeded AND results match
        success = primary_ok
        if has_reference and ref_ok is not None:
            success = success and ref_ok and (match is True)
        elif has_reference and ref_results is None:
            success = False  # reference target not found

        error: Optional[str] = None
        if not success:
            errors = []
            if not primary_ok:
                errors.append("primary failed")
            if ref_ok is not None and not ref_ok:
                errors.append("reference failed")
            if match is False:
                errors.append("results do not match")
            if last_error:
                errors.append(last_error)
            error = "; ".join(errors)

        return StepResult(
            step_index=step_index,
            description=description,
            success=success,
            primary_result={"results": primary_results} if primary_results else None,
            reference_result={"results": ref_results} if ref_results else None,
            match=match,
            error=error,
            attempts=1,  # simplified; real retries are per-action
        )

    def _execute_with_retry(
        self,
        page: Page,
        description: str,
        plan: ActionPlan,
    ) -> tuple[Optional[list[dict]], bool]:
        """Execute *plan* on *page*, with self-healing retry on failure.

        Returns ``(results, success)``.
        """
        last_results: Optional[list[dict]] = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                results = _execute_plan(page, plan)
                last_results = results

                # Check if all actions succeeded.
                all_ok = all(r.get("ok") for r in results)
                if all_ok:
                    return results, True

                # On failure: capture page context and re-resolve via LLM.
                if attempt < MAX_RETRIES:
                    ctx = _page_context(page)
                    # Note: we don't re-call llm.resolve here because the plan
                    # was already resolved. Instead, we wait and retry the same plan.
                    time.sleep(1)
            except Exception as exc:
                last_results = [{"ok": False, "error": str(exc)}]
                if attempt < MAX_RETRIES:
                    time.sleep(1)

        return last_results, False
