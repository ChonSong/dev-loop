# RefQA Integration — Coach Delegation Guide

## Purpose

RefQA provides **fast regression smoke tests** for the Coach's review cycle.
The Coach delegates `refqa run` for each project's smoke test and incorporates results into
its findings. This catches regressions (broken page, missing elements, game crash) that
would waste a full Coach review cycle.

**Important: RefQA is for regression detection, not reference comparison.**
The Coach does deep reference comparison manually in Step 2 (open-ended browser QA).
RefQA tests are fast smoke tests — they verify the page loads, core elements render,
and no crashes occur. Reference-verified steps are too slow for the free model
(10+ minutes for 17 steps with 2x LLM calls per step). Keep tests focused on
load/render verification.

## Test Inventory

| Test file | Project | Steps | Scope | Typical duration |
|-----------|---------|-------|-------|-----------------|
| `tests/gto-study-preflop.yaml` | GTO Wizard Clone | 4 | Page load, body text check, no reference | ~94s |
| `tests/polytopia-core-loop.yaml` | Polytopia Clone | 4 | Page load, canvas render, game init, no reference | ~46s |

## When to add a new test

Add a test when:
1. A regression was missed by a previous Coach cycle (the test would have caught it)
2. A core workflow is stable enough to define expected behavior
3. The workflow has identifiable DOM elements (not just canvas)

Don't add tests for:
- Features still in active development (tests go stale in hours)
- Canvas game interactions (coordinates change with layout changes)
- Anything requiring reference comparison (Coach does this in Step 2)

## Infrastructure

```
~/repos/refqa/
  ├── pyproject.toml          # Build config + dependencies
  ├── refqa/                  # Runner package
  ├── targets/                # Target definitions (URLs, LLM config)
  │   ├── gto-wizard.yaml     # GTO targets (clone only — no reference target needed)
  │   └── polytopia.yaml      # Polytopia target (hex.codeovertcp.com)
  └── tests/                  # YAML test files
      ├── gto-study-preflop.yaml
      └── polytopia-core-loop.yaml
```

### Install

```bash
cd ~/repos/refqa && python3 -m pip install .
```
Requires Python >=3.11, Playwright with chromium installed.

### Running

```bash
# Validate YAML before running
refqa validate tests/gto-study-preflop.yaml

# Run headless (production)
refqa run tests/gto-study-preflop.yaml

# Run with visible browser (debugging)
refqa run tests/gto-study-preflop.yaml --visible
```

## Delegation Pattern

The Coach delegates RefQA runs to a subagent in **Step 2b**, which runs concurrently with
the Coach's own Step 2 (open-ended browser QA). Each project's test is delegated as a
separate parallel task.

### Standard delegation (single project)

```python
delegate_task(tasks=[{
    "goal": "Run RefQA regression tests for gto-wizard-clone",
    "context": """
        CLI: refqa (installed globally via pip)
        Test: /home/sc/repos/refqa/tests/gto-study-preflop.yaml
        Command: refqa run /home/sc/repos/refqa/tests/gto-study-preflop.yaml
        Print every line of output — especially failures.
        Expected: all steps PASS (~60-90s total).
    """,
    "toolsets": ["terminal", "file"]
}])
```

### Multiple projects (parallel)

```python
delegate_task(tasks=[
    {
        "goal": "Run RefQA for GTO Wizard",
        "context": """
            CLI: refqa
            Test: /home/sc/repos/refqa/tests/gto-study-preflop.yaml
            Command: refqa run /home/sc/repos/refqa/tests/gto-study-preflop.yaml
        """,
        "toolsets": ["terminal", "file"]
    },
    {
        "goal": "Run RefQA for Polytopia",
        "context": """
            CLI: refqa
            Test: /home/sc/repos/refqa/tests/polytopia-core-loop.yaml
            Command: refqa run /home/sc/repos/refqa/tests/polytopia-core-loop.yaml
        """,
        "toolsets": ["terminal", "file"]
    },
])
```

## Interpreting results

| Output signal | Meaning | Coach action |
|---|---|---|
| ✅ All steps pass | No regressions detected | Nothing to report |
| ❌ Step fails | The page/spec has a regression | File as finding, re-run manually in browser to confirm |
| ❌ All steps fail or runner crashes | Page likely down or RefQA broken | Flag as P1 blocker: "RefQA smoke test failed — page may be down" |
| ⚠️ Single ambiguous failure | Free model returned `{}` on one step | Yellow-flag, re-run next cycle before filing P1 |

## Maintenance

- **Test goes stale**: If the clone's UI changes (new buttons, renamed labels, restructured
  page), the YAML step descriptions become unresolvable by the LLM. The Coach should file a
  finding: "RefQA test outdated — update step descriptions."
- **New project added**: Write a smoke test YAML and add a targets file. Update this doc.
- **Runner fails to install**: Check Python version (>=3.11), Playwright install, and
  pyproject.toml build settings. Re-run `pip install .`.
- **Free model changes**: The targets file configures the model. If `mimo-v2.5-free` becomes
  unavailable, update the targets file.

## Known issues

- **Free model flakiness**: `mimo-v2.5-free` returns `{}` ~30-40% of the time. The runner
  retries internally (3 attempts), but occasional false failures still leak through.
  Never file P1 on a single ambiguous failure — yellow-flag and re-run next cycle.
- **Slow on complex pages**: The LLM resolves each step in 15-30s. A 7-step test takes
  ~60-90s. Subagent delegation prevents this from blocking the Coach's context.
- **Canvas game limits**: Polytopia (Phaser canvas) has minimal DOM elements. The smoke
  test can only verify the page loads and the canvas element exists. It cannot verify
  game state (tribes, cities, units).
- **Reference verification impractical**: Reference-verified steps against
  app.gtowizard.com take 10+ minutes due to 2x LLM calls per step. The Coach does
  reference comparison manually in Step 2 — don't add `reference:` keys to smoke tests.
