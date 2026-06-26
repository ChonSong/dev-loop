---
name: e2e-testing
description: Playwright E2E testing patterns + pytest async backend API workflow tests — critical user flows at both the frontend and API layers, Page Object Model, configuration, CI/CD integration, visual regression testing, artifact management, MockTestRunner pattern, and async database-backed test fixtures.
version: 2.0.0
author: Sean
license: MIT
metadata:
  hermes:
    category: software-development
    tags: [playwright, e2e, visual-qa, hwc, testing]
---

# E2E Testing with Playwright and pytest

End-to-end testing patterns for **frontend** (Playwright) and **backend** (pytest + async API) workflows.

## When to Activate

- Testing critical user journeys
- Setting up E2E test infrastructure
- Adding visual regression tests
- Configuring Playwright in CI/CD
- Debugging flaky E2E tests
- **ANY frontend change to a web-accessible artifact** — GitHub Pages deployment, static HTML files, JavaScript UI changes. If it ships to a browser, it must be tested in a browser before commit.

## Core Patterns

### Test Structure

```typescript
import { test, expect } from '@playwright/test';

test.describe('User Authentication', () => {
  test('should login successfully', async ({ page }) => {
    await page.goto('/login');
    await page.fill('[data-testid="email"]', 'user@example.com');
    await page.fill('[data-testid="password"]', 'password123');
    await page.click('[data-testid="login-button"]');
    await expect(page.locator('[data-testid="dashboard"]')).toBeVisible();
  });
});
```

### Page Object Model

```typescript
class LoginPage {
  constructor(private page) {}

  async goto() { await this.page.goto('/login'); }
  async login(email: string, password: string) {
    await this.page.fill('[data-testid="email"]', email);
    await this.page.fill('[data-testid="password"]', password);
    await this.page.click('[data-testid="login-button"]');
  }
}

test('login flow', async ({ page }) => {
  const loginPage = new LoginPage(page);
  await loginPage.goto();
  await loginPage.login('user@test.com', 'pass');
  await expect(page).toHaveURL('/dashboard');
});
```

### Visual Regression Testing

```typescript
test('homepage looks correct', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveScreenshot('homepage.png', {
    maxDiffPixels: 100,
    fullPage: true,
  });
});
```

## Configuration (playwright.config.ts)

```typescript
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  webServer: {
    command: 'npm run start',
    port: 3000,
    reuseExistingServer: !process.env.CI,
  },
});
```

## CI/CD Integration

```yaml
# .github/workflows/e2e.yml
name: E2E Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: npm ci
      - run: npx playwright install --with-deps
      - run: npx playwright test
      - uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: playwright-report
          path: playwright-report/
```

## Docker Compose Integration Testing

For projects with a Docker Compose stack, write a standalone E2E test script that brings up the full stack, exercises it, and tears down. This catches Docker-specific issues (port mapping, healthcheck timing, nginx config, volume mounts, networking) that unit tests miss.

### Architecture

```
test_docker_stack.py
    │
    ├── docker compose up -d --wait    # Starts full stack with healthcheck wait
    ├── urllib.request health checks   # Backend /health, frontend HTTP 200
    ├── urllib.request API workflow    # Seed → create → poll → verify → delete
    ├── docker compose logs (on fail)  # Capture container logs for debugging
    └── docker compose down -v        # Teardown (always, even on failure)
```

### Test Script Skeleton (Python stdlib, zero external deps)

```python
#!/usr/bin/env python3
import json, os, subprocess, time, urllib.request

COMPOSE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_URL = "http://localhost:8000"

def api_post(path, data):
    body = json.dumps(data).encode()
    req = urllib.request.Request(f"{BACKEND_URL}{path}", data=body,
        headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=10).read())

def api_get(path):
    return json.loads(urllib.request.urlopen(f"{BACKEND_URL}{path}", timeout=10).read())

def poll_benchmark(bid, timeout=30):
    deadline = time.time() + timeout
    while time.time() < deadline:
        data = api_get(f"/api/benchmarks/{bid}")
        if data["status"] == "completed":
            return data
        time.sleep(1)
    raise TimeoutError(f"Benchmark {bid} not completed")

def main():
    failures = []

    # 1. Bring up stack
    subprocess.run("docker compose up -d --wait --wait-timeout 60", shell=True,
        cwd=COMPOSE_DIR, timeout=90, check=True)

    # 2. Health checks
    urllib.request.urlopen(f"{BACKEND_URL}/health", timeout=10)
    urllib.request.urlopen("http://localhost:3008", timeout=10)

    # 3. Seed and run benchmark workflow
    api_post("/api/models/seed-defaults", {})
    api_post("/api/test-cases/seed-defaults", {})
    benchmark = api_post("/api/benchmarks/", {
        "name": "e2e-test", "model_names": ["gpt-4o"],
        "test_case_names": ["rate-limiter-adherence"], "use_mock": True,
    })
    completed = poll_benchmark(benchmark["id"])
    assert completed["status"] == "completed"

    # 4. Verify results
    results = api_get(f"/api/results/benchmark/{benchmark['id']}")
    assert len(results) > 0
    assert all(r["status"] == "completed" for r in results)

    # 5. Teardown (always)
    subprocess.run("docker compose down -v", shell=True, cwd=COMPOSE_DIR)

    print(f"Passed {len(failures) == 0}")

if __name__ == "__main__":
    main()
```

### Key Design Decisions

- **`urllib.request`** instead of `httpx` — zero external dependencies, ships with Python stdlib, keeps the test script self-contained
- **`docker compose up -d --wait`** — blocks until all containers pass healthcheck, no manual sleep
- **`--wait-timeout 60`** — prevent CI from hanging indefinitely on a broken stack
- **`docker compose down -v`** — `-v` removes volumes (test DB), ensuring next run is fresh
- **Log capture on failure** — `docker compose logs backend --tail 100 > /tmp/backend-log.txt` for debugging
- **Mock mode** — `use_mock: True` means zero API keys needed, tests are fully self-contained

### CI Job Structure

Two jobs in the workflow — unit tests first, then Docker E2E:

```yaml
jobs:
  unit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv python install 3.11
      - run: uv pip install --system <test-deps>
      - run: PYTHONPATH=$PWD python -m pytest tests/ -v

  docker-e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker compose up -d --wait --wait-timeout 60
      - run: python e2e/test_docker_stack.py
      - if: failure()
        run: docker compose logs backend --tail 100
      - if: always()
        run: docker compose down -v
```

### Pitfalls

- **Port conflicts**: If the GitHub runner has something on port 8000 or 3008, the stack fails. Use unique ports in docker-compose.yml or check port availability first.
- **Healthcheck timing**: `--wait` uses the container healthcheck. If a service has no healthcheck defined, `--wait` ignores it (still starts it, just doesn't wait). Ensure every critical service has a `healthcheck:` in docker-compose.yml.
- **Log capture on failure**: The `if: failure()` condition only fires when the previous step failed. For the teardown, use `if: always()` so `docker compose down` runs regardless.
- **Volume cleanup**: Without `-v` on `docker compose down`, the test SQLite file persists to the next run, causing cross-run pollution. Always use `-v` in CI.
- **Background task timing**: For FastAPI `BackgroundTasks`, the benchmark runs asynchronously. The test script must poll until completion with a timeout. A 1-second sleep between polls is sufficient for most cases.
- **No `--wait` in older Docker Compose**: Docker Compose v2.4+ required. Run `docker compose version` to check. GitHub Actions `ubuntu-latest` has v2.35+ — fine.

### When to Use Docker Compose Tests vs pytest AsyncClient

| Approach | Use When | Tradeoff |
|---|---|---|
| **pytest + ASGITransport** | Testing API logic, scoring, DB interactions | Fast (0.6s), but doesn't test real networking, nginx, or Docker config |
| **Docker Compose + urllib** | Validating the full stack boots and serves | Slow (5-30s), but catches Dockerfile, nginx, port mapping, and healthcheck issues |
| **Playwright against Docker** | Testing the real frontend renders | Slowest, but catches JS bundles, API proxying, and UI rendering issues |

In a healthy project, all three layers exist. The Docker Compose layer is the cheapest way to catch infrastructure failures before they reach production.

## Backend API Testing with pytest (FastAPI + Async)

Backend E2E tests validate the API layer by simulating real user workflows through the HTTP interface. For projects with a mock execution mode (e.g., `MockTestRunner`), no API keys are needed — tests are fully self-contained.

### Architecture

```
pytest + httpx.AsyncClient → ASGITransport(app) → FastAPI app → MockTestRunner
                              ↕
                         SQLite :memory:
                         (per-session, cleaned between tests)
```

Key components:
- **`conftest.py`** — session-scoped fixtures for DB, client, seed data
- **`httpx.AsyncClient` with `ASGITransport`** — calls FastAPI directly without HTTP (fast, no ports)
- **In-memory SQLite** (`sqlite+aiosqlite:///:memory:`) — isolated per test session, cleaned between tests
- **Mock model runner** — generates deterministic scores without calling real LLM APIs

### conftest.py Structure

```python
"""conftest.py — shared fixtures for all backend tests."""
from __future__ import annotations

import asyncio
import os

# Set test DB env BEFORE importing app modules
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from app.core.database import engine, init_db
from app.main import app


@pytest.fixture(scope="session")
def event_loop():
    """Single event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def setup_database():
    await init_db()  # Creates all tables via Base.metadata.create_all
    yield
    # Tables dropped at session end


@pytest_asyncio.fixture(autouse=True)
async def clean_tables(setup_database):
    """Clean all tables between tests (prevents cross-test pollution)."""
    yield
    async with engine.begin() as conn:
        for table in reversed(Benchmark.metadata.sorted_tables):
            await conn.execute(table.delete())


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
```

### The MockTestRunner Pattern

For projects where execution involves external API calls (LLMs, cloud services), add a `MockTestRunner` that produces realistic output without real calls:

```python
class MockTestRunner:
    """Simulates benchmark execution with pre-set score profiles."""

    def __init__(self, session):
        self.session = session

    async def run_mock_benchmark(self, benchmark_id, model_names, test_case_names):
        """Generate mock results for every model × test_case pair."""
        benchmark = await self.session.get(Benchmark, benchmark_id)
        benchmark.status = "running"
        await self.session.commit()

        profiles = {
            "gpt-4o":        {"defensive": 3, "precise": 7, "fast": False},
            "claude-sonnet": {"defensive": 1, "precise": 9, "fast": False},
            "gemini":        {"defensive": 2, "precise": 6, "fast": True},
        }

        for model_name in model_names:
            for tc_name in test_case_names:
                prof = profiles.get(model_name, {"defensive": 2, "precise": 5, "fast": False})
                score = random.uniform(65, 95) * (prof["precise"] / 10)
                result = BenchmarkResult(..., status="completed", overall_score=round(score, 1))
                self.session.add(result)

        benchmark.status = "completed"
        await self.session.commit()
```

The hook: the API endpoint accepts `use_mock: bool`. When `True`, routes to MockTestRunner instead of the real runner:

```python
@router.post("/", response_model=BenchmarkResponse)
async def create_benchmark(data: BenchmarkCreate, background_tasks: BackgroundTasks, db):
    benchmark = Benchmark(name=data.name, status="pending")
    db.add(benchmark)
    await db.commit()
    await db.refresh(benchmark)

    async def run_task():
        async with async_session() as session:
            if data.use_mock:
                await MockTestRunner(session).run_mock_benchmark(...)
            else:
                await TestRunner(session).run_benchmark(...)

    background_tasks.add_task(run_task)
    return benchmark
```

### Benchmark Lifecycle Test Pattern

For systems with background-task execution (FastAPI `BackgroundTasks`, Celery, etc.), use a **poll loop**:

```python
async def test_completed_benchmark_has_results(self, client: AsyncClient, seeded_models, seeded_test_cases):
    # 1. Create (returns immediately with status=pending)
    resp = await client.post("/api/benchmarks/", json={
        "name": "my-benchmark",
        "model_names": ["gpt-4o", "claude-sonnet"],
        "test_case_names": ["test-case-1"],
        "use_mock": True,
    })
    assert resp.status_code == 200
    bid = resp.json()["id"]

    # 2. Poll until completed (with timeout)
    deadline = asyncio.get_event_loop().time() + 30.0
    while asyncio.get_event_loop().time() < deadline:
        resp = await client.get(f"/api/benchmarks/{bid}")
        assert resp.status_code == 200
        if resp.json()["status"] == "completed":
            break
        await asyncio.sleep(0.5)

    # 3. Verify results
    resp = await client.get(f"/api/results/benchmark/{bid}")
    assert len(resp.json()) == len(model_names) * len(test_case_names)
    for r in resp.json():
        assert r["status"] == "completed"
        assert 0 <= r["overall_score"] <= 100
```

### CI Workflow for Backend Tests

```yaml
name: Backend Tests
on:
  pull_request:
    paths: ["backend/**", ".github/workflows/test.yml"]
  push:
    branches: [main]
    paths: ["backend/**"]

jobs:
  test:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: backend
    steps:
      - uses: actions/checkout@v4
      - name: Install uv
        uses: astral-sh/setup-uv@v5
      - name: Set up Python
        run: uv python install 3.11
      - name: Install dependencies
        run: uv pip install --system <runtime-and-test-deps>
      - name: Run tests
        run: PYTHONPATH=$PWD python -m pytest tests/ -v --junitxml=results.xml
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: test-results
          path: backend/results.xml
```

### Pitfalls

- **pytest-asyncio mode** — Without `asyncio_mode = "auto"` in `pyproject.toml`, async tests fail with "async def functions are not natively supported." Add to `[tool.pytest.ini_options]`:
  ```toml
  [tool.pytest.ini_options]
  asyncio_mode = "auto"
  ```
- **Environment variable ordering** — `DATABASE_URL` must be set in `os.environ` BEFORE importing app modules, because `config.py` reads it at module load time via `Settings()`. Place the os.environ assignment before any `from app import ...` statements.
- **BackgroundTasks in test** — FastAPI's `BackgroundTasks` run synchronously on the event loop when using `ASGITransport`. The poll loop needs a small `asyncio.sleep(0.5)` to yield control so the background task can make progress.
- **No `--timeout` for plain pytest** — The `pytest-timeout` plugin is a separate install. Without it, `--timeout` flag fails. Use `asyncio.wait_for()` in test code instead.
- **Table cleanup between tests** — When using a session-scoped in-memory database, the `autouse` fixture must delete from all tables between tests. Use `Base.metadata.sorted_tables` for correct foreign-key-safe ordering.
- **Poetry build issues in editable install** — If `pyproject.toml` references a `README.md` that's outside the package dir, or lacks a `[tool.poetry.packages]` section, `uv pip install -e .` fails. Install runtime deps directly instead: `uv pip install --system <pkg1> <pkg2> ...`.

### Workflow-Level API Tests

The same taxonomy from Playwright applies to API tests:

| Level | What It Tests | Example | Quality |
|---|---|---|---|
| **Existence check** | "Does the endpoint respond" | `assert resp.status_code == 200` | Minimal — proves routing works |
| **Schema check** | "Does the response have the right shape" | `assert "id" in resp.json()` | Better — proves response format |
| **Workflow test** | "Can the user accomplish a real goal" | Seed → create → poll → verify scores → delete | Proves the feature works end-to-end |
| **Cross-resource workflow** | "Do related features interoperate" | Create model → create test case → create benchmark → verify results | Proves the system is coherent |

A healthy backend test suite has at least 2-3 workflow-level tests per API resource group, with the rest being targeted unit tests for the scoring/processing logic.

**This is the single most important testing pattern.** Most Playwright test suites devolve into "existence checks" — verifying that elements are on the page without proving the user can actually accomplish anything. Workflow tests simulate real end-user journeys.

### The Taxonomy

| Level | What It Tests | Example | Quality |
|---|---|---|---|
| **Existence check** | "Does this element exist on the page" | `await expect(heading).toBeVisible()` | Minimal value — DOM could be wrong but "present" |
| **Interaction test** | "Can the user interact with a control" | Click button → see response | Better — proves interaction works in isolation |
| **Workflow test** | "Can the user accomplish a real goal" | Navigate → configure → execute → verify result | Proves the feature works end-to-end |
| **Cross-app workflow** | "Can the user flow between related features" | Study → Practice → Analyze | Proves the UX is coherent |

### Test Suite Architecture (Layered Structure)

A well-organized E2E suite has four layers, each serving a distinct purpose and speed profile:

| Layer | Purpose | Run Time | Fail on CI | 
|-------|---------|----------|------------|
| **Smoke** (fast API integration checks) | Verify real data loads on core pages — catches server-down, blank page, major regression | <5s | Block deploy |
| **Page Object Model** (per-page coverage) | Verify each page renders correctly with all its components | 10-30s | Block deploy |
| **Workflow** (cross-page journeys) | Verify real end-user tasks work end-to-end | 15-45s | Warn / manual review |
| **Infra** (PWA, manifest, SW, offline) | Verify installability, responsiveness, service worker | 5-15s | Warn |

**Smoke tests** are the fastest signal: 1-2 assertions per core page, check the page loads without crash and renders real API data. They run before the full suite.

**POM tests** are the bulk of the suite: one spec file per feature page, using Page Object Model classes for selector reuse and readability.

**Workflow tests** are the highest value: they chain multiple pages together simulating real user journeys. Fewer of these, but each one proves the app works, not just that pages load.

**Infrastructure tests** cover PWA manifest, service worker registration, offline fallback, mobile viewport rendering — things that don't change with every feature commit but break silently.

### Concrete Example: GTO Wizard Clone (79 tests, 8 spec files)

The GTO Wizard test suite at `apps/web/e2e/` is a real-world implementation of this architecture:

| File | Tests | Layer | What It Covers |
|------|-------|-------|---------------|
| `smoke.spec.ts` | 5 | Smoke | Fast API integration: landing, equity, ICM, courses, variants — verify real data loads |
| `courses.spec.ts` | 13 | POM | Course list, difficulty/category filters, detail view, progress, continue buttons |
| `equity.spec.ts` | 6 | POM | Game view, BB/BTN range grids, board, statistics, position flow bar |
| `icm.spec.ts` | 9 | POM | Prize pool editing, chip stacks, ICM results, tournament inputs |
| `spots.spec.ts` | 13 | POM | Community spots, position/board filters, search, sort, heatmap, like/unlike |
| `strategies.spec.ts` | 10 | POM | Push/fold charts, position/stack depth filters, chart toggle, export |
| `workflows.spec.ts` | 9 | Workflow | Home→Study→Range, Home→Courses→Select, Home→ICM→Calculate, Home→Spot→Solve, cross-app navigation, responsive layout |
| `pwa.spec.ts` | 14 | Infra | Service worker, manifest, installability, offline, shortcuts, theme colors, mobile viewport |

Key architectural decisions:
- Smoke tests run first and fail fast — no point running the full suite if core pages don't load
- POM tests use `data-testid` selectors where available, structural fallbacks otherwise
- Workflow tests chain 5-10 interactions across 2-3 pages, proving the app works as a unified experience
- PWA tests are the slowest and least likely to change — separated from the main suite to avoid noise
- Console error checking filters expected API proxy failures (`!e.includes("500")`) when the backend is optional

See `references/gto-wizard-test-suite-structure.md` for the full inventory including POM class structure, configuration, known pitfalls, and the e2e/ subdirectory nested-node_modules issue.

### Workflow Test Design Patterns

Chain steps realistically. A user doesn't go to `/courses` and stare at the heading. They:

1. Land on home page
2. Navigate to a feature via nav bar or card link
3. Interact with the feature (filter, select, click)
4. See state change or result
5. Navigate to a related feature
6. Repeat

Write tests that simulate this chain:

```typescript
test("user studies preflop ranges and navigates to analyze", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("h1")).toContainText("GTO");
  await page.locator('a[href="/study"]').first().click();
  await expect(page).toHaveURL(/\/study/);
  await page.locator("button", { hasText: "BTN" }).click();
  await page.waitForTimeout(300);
  await expect(page.locator("div", { hasText: "AA" }).first()).toBeVisible();
  await page.locator('a[href="/analyze"]').first().click();
  await expect(page).toHaveURL(/\/analyze/);
});
```

Key principles:
- Each step depends on the previous one (no isolated page loads)
- Verify state changes after each interaction
- Test navigation between features, not just within them
- Use conditional logic (`if (await el.count() > 0)`) for elements that may not always be present — makes tests resilient

### The "Node Lock Solving" Pattern

For tools that involve configuration → computation → results (solvers, calculators, training):

```
browse presets → select a scenario → configure parameters → 
trigger computation → verify results → repeat with different params
```

```typescript
test("user browses spots and inspects a solution", async ({ page }) => {
  await page.goto("/spots");
  await expect(page.locator("h1, h2").filter({ hasText: /Spot/i })).toBeVisible();
  const spotButton = page.locator("button").filter({ hasText: /BTN|BB/i }).first();
  if (await spotButton.count() > 0) {
    await spotButton.click();
    await page.waitForTimeout(500);
  }
  await page.goto("/study");
  const posButtons = page.locator("button").filter({ hasText: /UTG|HJ|CO|BTN|SB|BB/i });
  expect(await posButtons.count()).toBeGreaterThanOrEqual(3);
  await posButtons.nth(0).click();
  await page.waitForTimeout(200);
  await posButtons.nth(1).click();
});
```

### Workflow Research with Playwright

Playwright isn't just for pass/fail — use it for workflow research:
- Measure timing per step to identify UX friction points
- Collect console errors at each workflow stage, not just at page load
- Verify navigation paths actually connect the features coherently
- Test the same workflow at mobile (390x844), tablet (768x1024), and desktop (1920x1080)

### How to Audit Existing Tests

Evaluate every assertion by category:

```typescript
const metrics = {
  totalAssertions: 0,
  existenceChecks: 0,   // toBeVisible, toHaveCount — no interaction
  interactionTests: 0,  // click → waitFor → verify
  workflowTests: 0,     // multi-step chain of interactions
  dataValidations: 0,   // checking actual data values
};
```

A healthy suite has >50% workflowTests + dataValidations. A suite that's >80% existenceChecks is not testing the app — it's testing that the DOM hasn't 404'd.

## Best Practices

- Use `data-testid` attributes for stable selectors
- Test **workflows**, not pages — a passing page-load tells you nothing about whether the app works
- Prefer multi-step chained tests over single-step isolated tests
- At minimum have: 1 home-discovery test + 2 core workflow tests + 1 cross-app nav test per feature
- Parallelize independent workflow tests (they don't share state)
- Retry flaky tests in CI (max 2 retries)
- Capture screenshots/video on failure
- Use fixtures for common setup
- Keep individual tests under 10 seconds when possible

## Container E2E Testing Patterns

### Playwright Browser Install in Containers

When running Playwright inside a Docker container, the default browser cache path (`/opt/hermes/.playwright` or `/root/.cache/ms-playwright`) may not be writable. Override at install time:

```bash
PLAYWRIGHT_BROWSERS_PATH=/tmp/pw-browsers npx playwright install chromium
```

Then set the same path at test time:

```bash
PLAYWRIGHT_BROWSERS_PATH=/tmp/pw-browsers npx playwright test
```

### PLAYWRIGHT_BROWSERS_PATH Stale Env Var Trap

A stale `PLAYWRIGHT_BROWSERS_PATH` environment variable in shell config (`.bash_profile`, `.bashrc`, `.profile`) can silently misdirect Playwright even when browsers are installed locally. Symptoms:
- `Executable doesn't exist at /some/stale/path/chromium_headless_shell-...`
- The actual browsers exist at `$PROJECT/.playwright/` or `~/.cache/ms-playwright/` but aren't found

**Diagnosis:**
```bash
echo $PLAYWRIGHT_BROWSERS_PATH          # current value
grep -r "PLAYWRIGHT" ~/.bash* ~/.profile  # where it's set
ls ~/.cache/ms-playwright/               # actual browsers location
```

**Fix:** Update the env var in the config file to match the actual browser path, **or** set it per-command:
```bash
unset PLAYWRIGHT_BROWSERS_PATH
# or
PLAYWRIGHT_BROWSERS_PATH="$PROJECT/.playwright" npx playwright test
```

**Common stale targets:** `/opt/data/...` paths that existed before a project migration, or paths from a different container configuration.

**Rule:** Always check `echo $PLAYWRIGHT_BROWSERS_PATH` first when Playwright can't find its browsers. If it's set, it overrides the local `.playwright/` directory. This is the #1 cause of "browser not found" failures in migrated projects.

### Missing System Shared Libraries

Even after installing Chromium, the container may lack required shared libraries (e.g., `libglib-2.0.so.0`, `libnss3.so`, `libatk1.0.so.0`). Symptoms:

```
error while loading shared libraries: libglib-2.0.so.0: cannot open shared object file
```

**Diagnosis:** Check if the library exists on the host but not in the container:
```bash
# On host
ssh host "find /usr/lib -name 'libglib-2.0*'"

# In container
ls /usr/lib/libglib-2.0* 2>/dev/null || echo "NOT_IN_CONTAINER"
```

**Fix options (in preference order):**
1. Add the library to the container's Dockerfile: `RUN apt-get install -y libglib2.0-0` or `RUN pacman -S --noconfirm glib2`
2. If you can't modify the image, run E2E tests on the host via SSH instead of inside the container
3. Use a Playwright Docker image that includes all system deps (e.g., `mcr.microsoft.com/playwright`)

**Do NOT capture this as a permanent constraint** — it's an environment setup issue that gets fixed once. But DO check for it when E2E fails with "shared library" errors.

### CI Mode: Disabling webServer When Starting Externally

When a cron job or script starts the Next.js server externally (e.g., `npx next start -p 3000 &`), the Playwright config's `webServer.command` will conflict. Use `process.env.CI` to disable it:

```typescript
// playwright.config.ts
webServer: process.env.CI
  ? undefined
  : {
      command: 'npm run dev',
      url: 'http://localhost:3000',
      reuseExistingServer: true,
      timeout: 120 * 1000,
    },
```

Then run tests with `CI=true`:

```bash
CI=true PLAYWRIGHT_BROWSERS_PATH=/tmp/pw-browsers npx playwright test
```

### Separate CI Config (Alternative)

For environments where modifying the main config is undesirable, create a separate `playwright.ci.ts`:

```typescript
// playwright.ci.ts — no webServer, expects server already running
import { defineConfig, devices } from '@playwright/test';
export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  retries: 0,
  workers: 1,
  reporter: 'list',
  use: { baseURL: 'http://localhost:3000' },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
});
```

Run with: `npx playwright test --config=playwright.ci.ts`

## Hermes Web Computer E2E Patterns

### Playwright Browser Path (Container Env)

**Critical:** The default Playwright install path (`/opt/hermes/.playwright`) is permission-denied. Always set `PLAYWRIGHT_BROWSERS_PATH` before any Playwright command:

```bash
PLAYWRIGHT_BROWSERS_PATH=/opt/data/hermes-web-computer/.playwright \
  npx playwright install chromium

PLAYWRIGHT_BROWSERS_PATH=/opt/data/hermes-web-computer/.playwright \
  npx playwright test
```

### CommonJS Smoke Test Pattern

For quick smoke tests without the full test suite infrastructure, write a standalone `.cjs` script:

```javascript
// e2e/smoke.cjs — run with: node e2e/smoke.cjs
const { chromium } = require('./node_modules/playwright');

(async () => {
  const browser = await chromium.launch({
    executablePath: '/opt/data/.playwright/chromium-1159/chrome-linux/chrome',
    headless: true
  });
  const page = await browser.newPage();
  await page.goto('http://localhost:3005');
  const title = await page.title();
  if (!title.includes('Hermes')) throw new Error('App not responding');
  const tiles = await page.locator('div.rounded-2xl').count();
  if (tiles === 0) throw new Error('No tile containers found');
  await browser.close();
  console.log('✅ Smoke passed');
})();
```

### Stale Selector Pitfall

Component theme commits can silently change CSS classes. Always prefer selectors based on: `data-testid` > structural classes (`rounded-2xl`, `shadow-panel`) > color classes (`border-blue-500`). Color classes are the first to change in theme refactors.

### Page Structure Mismatch (Stale Selectors)
### Page Structure Mismatch (Stale Selectors)

The page a test was written for may not match the actual rendered DOM. Common in refactored or rushed codebases. Symptoms: `toBeVisible()` times out on a heading selector that "should exist."

**Diagnosis** — dump the actual page structure:
```typescript
const headings = await page.evaluate(() => {
  return Array.from(document.querySelectorAll('h1, h2, h3'))
    .map(h => h.tagName + ': ' + h.textContent.trim());
});
console.log(JSON.stringify(headings));
```

**Fix** — update selectors in the Page Object Model to match reality. Never force-add DOM elements just to satisfy a test. For tool/game-view pages that intentionally skip standard headings, update the test.

**Strict-mode violations** — when `.toBeVisible()` fails with "strict mode violation," the locator matches multiple elements. See `references/playwright-strict-mode-patterns.md` for fixes (exact text match, `.first()`/`.last()`, scope to container).

### API Error Tolerance in Console Checks

When the frontend proxies to an optional backend (local dev without API server), console error checks will catch the proxy failures:

```typescript
// Filter expected API errors based on what's running
const criticalErrors = consoleErrors.filter(
  (e) => !e.includes("favicon")
    && !e.includes("404")
    && !e.includes("500")
    && !e.includes("Failed to fetch")
    && !e.includes("Failed to load resource")
);
```

Keep the filter permissive enough for the CI environment but document which errors signal real problems vs missing optional backends.

### CI=true for Separate Server Management

When the dev/prod server is started externally (systemd, docker-compose, cron), prevent Playwright from launching a conflicting server:

```typescript
// playwright.config.ts
webServer: process.env.CI
  ? undefined
  : { command: 'npm run dev', url: 'http://localhost:3000', reuseExistingServer: true },
```

Run with:
```bash
CI=true PLAYWRIGHT_BROWSERS_PATH=/tmp/pw-browsers npx playwright test
```

### Pitfall: git add -A Captures Playwright Cache Bloat

The HWC repo contains Playwright browser binaries in `.playwright/` and npm cache in `.npm-cache/`. Always check before committing:

```bash
git add -A
git diff --cached --stat   # verify only intended files
# If bloat detected:
git reset HEAD
git add <specific-files>
git commit
```

## Visual QA Pipeline

### Host-side Screenshot Capture (via SSH)

```bash
cd /home/sean/.hermes/hermes-web-computer
npx playwright screenshot --browser chromium http://127.0.0.1:3005 /tmp/hwc5.png
```

### Multi-Viewport Capture

Capture at 3 standard viewports: `1440x900`, `1280x720`, `1920x1080`. Store baselines at `/tmp/hwc-qa/baselines/`.

### Two-Stage Comparison

1. **Regression check**: current vs baseline — detect accidental breakage (threshold: 1% diff)
2. **Reference check**: current vs reference image — score against target design (threshold: 85% similarity)

### CRITICAL PITFALL: Pixel-Diff Is Wrong for Theming Comparison

The PIL/pixelmatch approach is fundamentally broken for CSS theme comparison. Use **Layered Assessment**:

| Layer | Method | Tool |
|-------|--------|------|
| 1. CSS Variables | Extract `--color-*` custom properties, compare with OKLab ΔE perceptual color distance | `getComputedStyle()` in browser |
| 2. DOM Structure | Compare element presence/class structure | Playwright DOM queries |
| 3. Computed Styles | Extract rendered styles per element | `page.evaluate(getComputedStyle)` |
| 4. Visual (last resort) | SSIM or Butteraugli — NOT raw pixel-diff | resemble.js, BackstopJS with SSIM, or human review |

**When pixel-diff IS appropriate:** Detecting regression (current vs previous build of the SAME UI). Threshold: 1%.
**When pixel-diff is WRONG:** Comparing implementation against a reference design theme.

## Standalone Puppeteer Visual Regression Pipeline

The GTO Wizard Clone project has a full Puppeteer-based visual regression pipeline at `/workspace/ui-qa-tool/ui-qa.js` that is separate from Playwright but serves the same visual QA purpose. Key features:

- **`snapshot <url> <name>`** — Full-page screenshot + metadata (title, headings, links, scroll height) + console error capture
- **`diff <ref> <current>`** — Pixel-accurate diff with red highlight overlay using pixelmatch
- **`audit <url>`** — Console errors, HTTP errors, a11y (missing alt text, unlabeled inputs), DOM performance metrics
- **`check <url> --selectors=...`** — Verify specific elements exist and are visible
- **`pipeline <base-url>`** — Full regression: snapshot all pages → compare vs references → report changes

### Configuration

```json
// ui-qa-pages.json — defines pages to test
{
  "home": "",
  "about": "about",
  "equity": "gto/equity",
  "solver": "gto/solver"
}
```

### Running

```bash
cd /workspace/ui-qa-tool

# First run — captures references
UI_QA_SNAPSHOTS=./snapshots UI_QA_REFS=./refs node ui-qa.js pipeline http://localhost:8555

# After changes — detects what broke visually
UI_QA_SNAPSHOTS=./snapshots UI_QA_REFS=./refs node ui-qa.js pipeline http://localhost:8555
```

### Chrome Binary Path

The tool auto-detects the Chrome binary at the path set in `CHROME_PATH` env var (defaults to Puppeteer's Chrome install path). Verify Chrome exists:

```bash
ls "$CHROME_PATH" 2>/dev/null || echo "Install: npx puppeteer browsers install chrome"

## Game Loop E2E Testing (Canvas / Phaser Games)

Turn-based games rendered on `<canvas>` need different waiting strategies than standard web apps. AI turn processing time is variable and cannot use fixed `waitForTimeout` — always **poll for UI state change** (e.g., "End Turn" button becoming enabled) instead.

### Core Pattern: Polling Over Blind Sleep

```typescript
async function waitForMyTurn(page: Page, timeout = 15000): Promise<void> {
  const endTurn = page.locator('button:has-text("End Turn")');
  const deadline = Date.now() + timeout;
  while (Date.now() < deadline) {
    if (await endTurn.isEnabled().catch(() => false)) return;
    await page.waitForTimeout(300);
  }
  throw new Error(`Timed out waiting for player turn after ${timeout}ms`);
}
```

### Key Principles

- **Never use `waitForTimeout` for game-loop waits** — map size, number of AI tribes, and complexity make AI turn time unpredictable
- **Always set explicit per-test timeouts** for game loops (`test.setTimeout(60_000)`)
- **Click canvas by dispatching events** at computed pixel coordinates using `boundingBox()`
- **Prefer DOM signals** (button enabled/disabled, turn counter text) over canvas introspection

See `references/game-loop-e2e-patterns.md` for full patterns including canvas clicking, coordinate debugging, state signal inventory, Polytopia Clone specifics, and common failure modes.

## References

- `references/game-loop-e2e-patterns.md` — Polling-based waiting for canvas/Phaser games, turn-based AI handling
- `references/static-web-testing.md` — GitHub Pages testing, force-graph debugging
- `references/gto-wizard-e2e-audit-2026-06-14.md` — Full test quality audit
- `references/backend-api-workflow-tests.md` — llm-benchmark-platform example conftest + test patterns
- `references/mock-to-api-migration.md` — Test failures when switching from mock data to live API
- `templates/docker-e2e-test.py` — Reusable Docker Compose E2E test script (stdlib only)
