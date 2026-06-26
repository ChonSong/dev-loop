---
name: refqa
description: >-
  Reference-Augmented Agentic QA runner — self-healing YAML tests with
  LLM-powered browser automation. Uses OpenCode Zen (mimo-v2.5-free) as the
  LLM backend. Playwright for browser automation. Designed for fast regression
  smoke tests, NOT deep reference comparison.
---

# RefQA — Reference-Augmented Agentic QA

## Core Concept

A natural-language YAML test format where steps are LLM-resolved browser
automation actions (navigate, click, verify_text, wait, verify_element,
screenshot, type, select, hover). The LLM converts plain-English step
descriptions into structured action plans for Playwright.

**Important: RefQA is for fast regression smoke tests, NOT reference comparison.**
The original reference-verified approach (comparing clone vs original page
side-by-side) was dropped because (1) it doubles LLM calls per step, (2) the
free model is too flaky for parallel resolution, and (3) deep comparison is
the Coach's job in Step 2 (manual browser QA).

## Repository

`https://github.com/ChonSong/refqa` (private)

## Quick Start

```bash
cd ~/repos/refqa
python3 -m pip install .
python3 -m playwright install chromium
```

> **Important:** Must use Python >=3.11. The `pyproject.toml` requires
> `[build-system]` with `requires = ["setuptools>=64"]` — already configured.
> Use `python3 -m pip install .`, not `pip` (system pip may point to Python 3.8).

## Test Format

```yaml
test-id: my-test-name
name: Human-readable test name
targets:
  primary:
    name: my-app
    url: https://my-app.example.com
steps:
  - description: Navigate to "https://my-app.example.com/study"
  - description: Wait for position cards to load
  - description: Take a screenshot
```

No `reference:` key — RefQA tests are smoke-only. The Coach handles reference comparison.

## Running

```bash
# Validate YAML
refqa validate tests/my-test.yaml

# Run headless (production)
refqa run tests/my-test.yaml

# Run with visible browser (debugging)
refqa run tests/my-test.yaml --visible
```

## Test Inventory

| File | Project | Steps | Duration | Scope |
|------|---------|-------|----------|-------|
| `tests/gto-study-preflop.yaml` | GTO Wizard | 4 | ~94s | Navigate, wait, verify body text, screenshot |
| `tests/polytopia-core-loop.yaml` | Polytopia | 4 | ~46s | Navigate, wait for canvas, wait for game init, screenshot |

Both use `mimo-v2.5-free` model on OpenCode Zen.

## LLM Client

- **Provider:** OpenCode Zen (OpenAI-compatible)
- **Model:** `mimo-v2.5-free` (free tier)
- **API key resolution** (in priority order):
  1. `OPENCODE_ZEN_API_KEY` environment variable
  2. `~/.hermes/.env` file (Hermes credential store — key stored there)
  3. `~/.hermes/auth.json` credential pool (legacy; entries may only store fingerprints, not the key value)
- **Timeout:** 60s per call; 3 retry attempts on failure

## Architecture

1. Parse YAML test → Pydantic models
2. Launch Playwright (headless by default, 1280x800 viewport)
3. Navigate to primary target URL
4. For each step:
   a. Send natural-language step description → LLM
   b. LLM returns structured action plan (list of BrowserAction objects)
   c. Execute actions sequentially via Playwright
   d. On action failure, retry the same plan up to 3 times
   e. On LLM failure (returns `{}`), retry up to 3 times with retry delay
5. Return aggregated pass/fail report with per-step results

## Coach Integration

RefQA is used at **Step 2b** of the Coach's review cycle. The Coach delegates
`refqa run` to a subagent (runs in parallel with Step 2 open-ended browser QA).

**Results interpretation:**
- ✅ All pass → no regressions (nothing to report)
- ❌ Step failures → regression likely. Coach re-runs manually to confirm.
- ❌ User-friendly `refqa run` — actually, just the runner output

**Delegation pattern:**

```python
delegate_task(tasks=[{
    "goal": "Run RefQA for GTO Wizard",
    "context": """
        CLI: refqa
        Test: /home/sc/repos/refqa/tests/gto-study-preflop.yaml
        Command: refqa run /home/sc/repos/refqa/tests/gto-study-preflop.yaml
        Print every line of output — especially failures.
    """,
    "toolsets": ["terminal", "file"]
}])
```

See `coach-agent` skill's `references/refqa-integration.md` for full details.

## Targets

Targets define URLs and LLM configuration per project:

```bash
~/repos/refqa/targets/
├── gto-wizard.yaml    # URL + LLM config for GTO Wizard Clone
└── polytopia.yaml     # URL + LLM config for Polytopia Clone
```

Each targets file defines:
- Target name and URL
- LLM provider/model/API key source
- Runner defaults (workers, retries, screenshot-on-failure)

## Known Issues

- **Free model flakiness:** `mimo-v2.5-free` returns `{}` ~30-40% of the time.
  The runner has 3 internal retries, but false positives still leak through.
  Never file P1 on a single ambiguous failure — yellow-flag and re-run.
- **Slow resolution:** 15-30s per step. A 4-step test takes ~46-94s.
  Subagent delegation prevents this from blocking the Coach. Keep tests short.
- **Canvas game limits:** Polytopia (Phaser) has minimal DOM. Tests can only
  verify page load + canvas present, not game state.
- **YAML goes stale:** When UI changes, step descriptions become unresolvable
  by the LLM. Flag as outdated rather than silently ignoring failures.
- **.env key resolution:** The `~/.hermes/.env` file is the primary key store.
  Terminal sessions don't inherit it — the code reads it explicitly.
  Change the env file path if Hermes credential store location changes.

## Pitfalls

- Always validate before running: `refqa validate tests/my-test.yaml`
- Keep tests at 4 steps or fewer — more steps means more failure points
- Use concrete, verifiable step descriptions ("Navigate to URL", "Take a screenshot")
- Avoid vague steps ("Verify it looks right") — the LLM needs specific actions
- Do NOT add `reference:` keys — they double LLM calls per step and the free model can't handle it
- Reinstall after any code changes: `cd ~/repos/refqa && python3 -m pip install .`
- If the runner hangs, the free model may be unavailable — check API status
