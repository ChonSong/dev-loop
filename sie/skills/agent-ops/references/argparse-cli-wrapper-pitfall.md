# Argparse REMAINDER pitfall (when wrapping CLIs)

## The bug

When writing a Python wrapper around another command using
`argparse.REMAINDER`, declaring a flag without `action="store_true"`
silently breaks argument passing.

**Wrong:**
```python
parser.add_argument("--budget-override", help="Bypass budget check")
parser.add_argument("command", nargs=argparse.REMAINDER)

# Invocation: wrapper --budget-override curl https://...
# argparse sees: --budget-override = "curl"  (consumes next arg as value)
# Result: command = ["https://..."], --budget-override is lost
# User thought: "the override didn't work"
# Reality: argparse ate the next arg as the flag's value
```

**Right (option A — env var):**
```python
# No --budget-override flag at all
override = os.environ.get("WRAPPER_OVERRIDE", "") == "1"

# Invocation: WRAPPER_OVERRIDE=1 wrapper curl https://...
```

**Right (option B — store_true):**
```python
parser.add_argument("--budget-override", action="store_true")
parser.add_argument("command", nargs=argparse.REMAINDER)

# Invocation: wrapper --budget-override curl https://...
# Works because store_true takes no value
```

## Why option A (env var) is better for wrappers

1. **No name collision with wrapped command's own flags.** If the
   wrapped command has its own `--override` flag, option B breaks
   it (argparse consumes it). Env vars sidestep the namespace.

2. **No `--help` pollution.** The wrapper's `--help` shouldn't list
   every possible flag of every command it might wrap.

3. **Composability.** The user can set the env var once in a
   script and run multiple commands:
   ```bash
   export GATED_BUDGET_OVERRIDE=1
   gated-terminal false
   gated-terminal foo
   gated-terminal bar
   ```

## When this bit me

I built `gated-terminal` with `--budget-override` (option B but
without `store_true`). The override test failed with exit code 0
instead of 1 — because argparse had consumed "false" as the
override flag's value, leaving no command to run. The empty
`subprocess.run([])` succeeded.

The fix: convert to env var, document the override in the abort
message, and add a self-test that actually runs a failing command
with the override to verify it bypasses correctly.

## General principle

When writing a wrapper CLI that uses `argparse.REMAINDER` to pass
through to another command:

> **All wrapper-level toggles must be either `action="store_true"`
> (no value) or env vars. Never declare a flag that takes a value
> alongside REMAINDER, because argparse can't tell where the
> flag's value ends and the wrapped command's args begin.**

Add a self-test that exercises the override path with a failing
command. Don't trust the override works just because the code
parses.
