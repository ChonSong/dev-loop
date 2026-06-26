# argparse `--flag value` collides with `nargs=REMAINDER`

## The problem

When building a command wrapper like `gated-terminal <cmd> [args...]` you naturally
want `nargs=argparse.REMAINDER` for `command` to pass everything through:

```python
parser.add_argument("command", nargs=argparse.REMAINDER)
```

But then if you add any flag that takes a value, argparse will eat the next arg:

```python
parser.add_argument("--budget-override", help="Bypass budget check")
```

Calling `gated-terminal --budget-override false`:
- argparse sees `--budget-override` and looks for its value
- Finds `false` → stores it as the override value
- `args.command` becomes `[]`
- subprocess.run([]) → FileNotFoundError or empty execution

The wrapped command (`false`) is NEVER run. Exit code is 0 (or 127) from the
empty execution, not the wrapped command.

## The fix

Use an **environment variable** for any wrapper-level override:

```python
# Don't add --budget-override to the parser
# Instead, read it from the env in main():
budget_override = os.environ.get("GATED_BUDGET_OVERRIDE", "") == "1"
```

Usage: `GATED_BUDGET_OVERRIDE=1 gated-terminal <cmd>`

## Why env var, not store_true flag

`store_true` works for boolean flags IF the flag itself comes last (no value after it).
But: argparse's REMAINDER captures everything, so even a trailing `--override` would be
eaten by the command capture. Env vars are unambiguous.

## What CAN be a CLI flag (no conflict)

Flags that don't take a value AND don't precede the command:
- `--status` (action="store_true") — output mode, command-less
- `--reset` (action="store_true") — output mode, command-less
- `--dry-run` (action="store_true") — output mode, command-less
- `--json` (action="store_true") — output mode flag

The rule: **any flag that takes a value MUST be an env var** in a REMAINDER-wrapper.

## The hidden cost

This bug is silent. Exit code 0 with no output looks like "the command worked."
The only way to catch it is:
- Test with a command that has a known nonzero exit (e.g., `false`)
- Verify the exit code matches the wrapped command's exit code
- Check `args.command` is non-empty after parsing

The original test caught this with:
```python
r = subprocess.run(["python3", "gated-terminal.py", "--budget-override", "false"], ...)
assert r.returncode == 1, f"Expected 1 from false, got {r.returncode}"
# Actually got 0 — exit code from empty execution
```

## Alternative: use `click` instead of argparse

`click` handles this more cleanly because it has explicit `pass_context` and
forward-of-unknown-args semantics. But for a 200-line script, argparse + env
var is fine and avoids the dependency.
