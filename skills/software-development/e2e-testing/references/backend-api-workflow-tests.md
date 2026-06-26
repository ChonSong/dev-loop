# Backend API Workflow Tests — llm-benchmark-platform Example

Concrete reference for the backend API testing pattern described in the e2e-testing skill.

## Quick Stats

| Metric | Value |
|---|---|
| Test files | 2 (`test_benchmark_workflow.py`, `test_scoring_engine.py`) |
| Total tests | 18 (9 workflow + 8 scoring unit + 1 fixtures) |
| Run time | 0.64s |
| External deps | Zero (mock mode) |
| Framework | pytest + pytest-asyncio + httpx.AsyncClient |
| DB | SQLite in-memory, session-scoped, cleaned between tests |

## File Structure

```
backend/
├── tests/
│   ├── conftest.py              # Fixtures: async client, DB, seed data, table cleanup
│   ├── test_benchmark_workflow.py  # Full lifecycle workflow tests (9 tests)
│   └── test_scoring_engine.py     # Scoring logic unit tests (8 tests)
├── pyproject.toml                # [tool.pytest.ini_options] asyncio_mode = "auto"
└── .github/workflows/
    ├── promptfoo-eval.yml        # LLM quality gate
    └── test.yml                  # Backend test CI
```

## Key Fixtures (conftest.py)

```python
# Environment override MUST be before app imports
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

from app.core.database import engine, init_db
from app.main import app
from app.models import Benchmark, BenchmarkResult, ModelConfig, TestCase
```

Three critical fixture scopes:
- **`setup_database`** (session) — creates all tables once
- **`clean_tables`** (function, autouse) — deletes all rows between tests via `Base.metadata.sorted_tables`
- **`client`** (function) — `httpx.AsyncClient` wrapping `ASGITransport(app=app)`

## Workflow Test Skeleton

```python
class TestBenchmarkWorkflow:
    """Full benchmark lifecycle using mock mode (no API keys needed)."""

    async def test_seed_and_list_models(self, client: AsyncClient):
        resp = await client.post("/api/models/seed-defaults")
        assert resp.status_code == 200

    async def test_create_benchmark_returns_pending(self, client, seeded_models, seeded_test_cases):
        resp = await client.post("/api/benchmarks/", json={
            "name": "test", "model_names": ["gpt-4o"],
            "test_case_names": ["rate-limiter-adherence"], "use_mock": True,
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "pending"

    async def test_benchmark_completes_and_has_results(self, client, seeded_models, seeded_test_cases):
        # Create
        resp = await client.post("/api/benchmarks/", json={...})
        bid = resp.json()["id"]

        # Poll until completed (with timeout)
        deadline = asyncio.get_event_loop().time() + 30.0
        while asyncio.get_event_loop().time() < deadline:
            resp = await client.get(f"/api/benchmarks/{bid}")
            if resp.json()["status"] == "completed":
                break
            await asyncio.sleep(0.5)

        # Verify results
        resp = await client.get(f"/api/results/benchmark/{bid}")
        assert len(resp.json()) > 0
        for r in resp.json():
            assert r["status"] == "completed"
            assert 0 <= r["overall_score"] <= 100

        # Verify comparison endpoint
        resp = await client.get(f"/api/results/benchmark/{bid}/comparison")
        assert "by_model" in resp.json()["summary"]

        # Delete and verify cascade
        await client.delete(f"/api/benchmarks/{bid}")
        resp = await client.get(f"/api/benchmarks/{bid}")
        assert resp.status_code == 404
```

## Scoring Engine Test Skeleton

```python
class TestScoringEngineAdherence:
    def setup_method(self):
        self.engine = ScoringEngine()

    def test_perfect_implementation(self):
        code = open("test_fixtures/perfect_impl.py").read()
        rules = [{"description": "Class name is TokenBucketLimiter", "points": 10}, ...]
        result = self.engine.score_task_a_adherence(code, rules)
        assert result.overall_score > 80
        assert len(result.issues) == 0
```

## GitHub Actions CI

```yaml
# .github/workflows/test.yml
name: Backend Tests
on:
  pull_request:
    paths: ["backend/**"]
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: backend
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv python install 3.11
      - run: uv pip install --system fastapi uvicorn[standard] sqlalchemy pydantic pydantic-settings httpx aiosqlite pytest pytest-asyncio python-multipart
      - run: PYTHONPATH=$PWD python -m pytest tests/ -v --junitxml=results.xml
      - if: always()
        uses: actions/upload-artifact@v4
        with:
          name: test-results
          path: backend/results.xml
```

## Common Pitfalls Hit

1. **pytest-asyncio strict mode** — Install >1.0.0 defaults to strict. Add `[tool.pytest.ini_options] asyncio_mode = "auto"` to pyproject.toml.
2. **Env var timing** — `os.environ["DATABASE_URL"]` must be set before `from app.core.config import settings` because pydantic-settings reads env vars at class definition time.
3. **BackgroundTasks vs sync vs async** — FastAPI `BackgroundTasks` in `ASGITransport` mode share the same event loop, so a blocking await prevents progress. Use `asyncio.sleep(0.5)` in the poll loop to yield control.
4. **API returns 200 not 201** — FastAPI's default status code is 200 unless `status_code=201` is set in the route decorator. Test for 200 unless the backend explicitly uses 201.
5. **Cascade delete returns JSON** — If the delete endpoint returns `{"message": "Deleted"}` (200) instead of 204 No Content, the test should expect 200.
6. **Paginated list endpoints** — If `GET /api/resource/` returns `{"data": [...], "total": N}` instead of a raw array, the test should check `data["data"]` or `data["items"]` or `data["benchmarks"]` whichever the API uses.
7. **Poetry package structure** — A pyproject.toml without `[tool.poetry.packages]` or with a missing `README.md` at the expected path will fail `pip install -e .`. Install runtime deps directly via `uv pip install --system <deps>` instead of trying to build the package.
