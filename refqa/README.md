# RefQA — Reference-Augmented Agentic QA

A unified QA runner that combines self-healing UI interaction with reference-based verification.

## What it does

One YAML format, two execution modes:

```yaml
steps:
  # Pure UI interaction — self-healing, LLM-resolved
  - Click on "UTG" position card

  # UI interaction + reference verification — checks against the original app
  - Verify cell "AA" shows "raise" with 100% frequency
    reference: app.gtowizard.com
```

Every step can optionally be **reference-verified**. Without a reference, it's a self-healing
UI interaction. With a reference, the runner checks both the app under test and the reference
target in parallel, and fails the step if results diverge.

## Why not agent-qa?

agent-qa has self-healing YAML tests but no reference comparison — it can't tell you
whether your app's behavior matches the original. Coach has reference comparison but
requires manual browser sessions. RefQA is the synthesis: one step type that does both.

## Why not Playwright + Coach?

Playwright + Coach works, but requires two separate systems and a human-in-the-loop
review cycle. RefQA automates the comparison: the test itself encodes "this behavior
must match the reference." Parallel browser sessions, no manual comparison needed.

## Quick start

```bash
pip install -e .
refqa run tests/gto-study-preflop.yaml
```

## License

MIT
