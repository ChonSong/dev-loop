# Invoking Skills via CLI

## Correct Method

**Reliable approach** — invoke the standalone search script directly:

```bash
python3 ~/.hermes/skills/automation/job-search/scripts/run_search.py \
  --positions "Data Scientist" \
  --locations "Sydney, NSW" \
  --country AU --max 200
```

**Chat-based** (may fail to produce output depending on model):

```bash
hermes -z "Search Indeed for Data Scientist jobs in Sydney, AU" -s job-search
```

## Pitfalls

- `hermes skill run ...` does NOT exist — the `skill` subcommand is not a valid hermes CLI command.
- `-p` / `--prompt` is NOT a valid flag — use `-z` (oneshot) instead.
- `-z` + `-s` may return "no final response was produced" if the model doesn't invoke the search. Fall back to the direct script in that case.
- `--toolsets` accepts category names (e.g., `web`, `automation`), NOT skill names.
- One-shot mode (`-z`) does not support `--skills` before the prompt string — use `-s job-search -z "prompt"` order.