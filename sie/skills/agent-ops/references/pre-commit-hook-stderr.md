# Pre-commit hook output goes to STDERR

## The rule

When a script becomes a git pre-commit hook, **git displays stderr to the
committer and captures stdout internally**. If you print your pass/fail
status to stdout, the user sees nothing — they just see "commit was blocked"
with no reason.

## The trap

A tool written as a CLI typically prints pass/fail to stdout:

```python
print(f"✓ PASSED")
print(f"✗ FAILED: {reason}")
```

This works fine when called directly: `python3 pre-commit-gate.py`
But as a hook, the user sees:
```
$ git commit -m "fix"
# (nothing)
# commit is blocked
```

## The fix

Write status to stderr, reserve stdout for data only:

```python
import sys
print(f"✓ PASSED", file=sys.stderr)
print(f"✗ FAILED: {reason}", file=sys.stderr)
# Or use logging to stderr by default
```

## How to test

In the test that verifies the hook blocks a bad commit:

```python
r = subprocess.run(["git", "commit", "-m", "test"], cwd=repo, capture_output=True, text=True)
assert r.returncode == 1  # blocked
# WRONG: assert "FAILED" in r.stdout  # won't be there
# RIGHT: assert "FAILED" in r.stderr  # will be there
```

This bit me on my first test — the assertion was on `r.stdout` and the
test reported "hook didn't surface the block" even though the hook was
working perfectly.

## Why git does this

Git runs hooks via `run-command.h:cmdio_log` which pipes stdout to its
internal log and merges stderr to the user's terminal. This is intentional:
stdout is "data the script produced," stderr is "the script talking to the
operator." Pre-commit hooks are operator-facing, so stderr is correct.

## When stdout IS right

If the hook emits machine-readable output that another tool consumes (e.g.,
a hook that produces a JSON report for a CI system), stdout is correct.
In that case, document the contract clearly in the SKILL.md.

## Cross-platform note

On Windows, git-bash sometimes captures both streams together. If you need
truly portable hook output, write to a known file (`.git/hook-output.txt`)
and have the user `cat` it manually. Not recommended; just use stderr.
