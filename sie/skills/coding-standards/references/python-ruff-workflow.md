# Python Ruff Lint Sweep — Practical Workflow

Systematic approach to cleaning up ruff lint issues in a Python monorepo.

## Quick Commands

```bash
# Safe auto-fixes only (unused imports, unused vars in source)
ruff check <path> --fix

# Also fix style issues (E712 True/False comparisons, some F841)
ruff check <path> --fix --unsafe-fixes

# Summary of remaining issues
ruff check <path> --statistics

# Format all files
ruff format <path>
```

## Order of Operations

1. **Safe sweep first:** `ruff check --fix` — handles F401 (unused imports), F841 (unused vars), some F811 (redefinition)

2. **Unsafe sweep second:** `ruff check --fix --unsafe-fixes` — catches E712 (``== True/== False`` equality comparisons), remaining F841

3. **Check for F821 (undefined name) bugs:** After auto-fixes, run `ruff check --select F821` to find actual runtime bugs:
   - Missing imports (e.g., `timezone`, `SoftTimeLimitExceeded`)
   - Forward references as string annotations (`"TexasHoldEm"`) — these are **false positives**, suppress with ``# noqa: F821``
   - Code in ``if __name__ == "__main__":`` blocks may need local imports

4. **Handle intentional patterns:**
   - E402 (module-level import not at top of file): often intentional for `sys.path.insert(0, ...)` + import patterns in solver/test code. Do not "fix" by moving imports above path inserts — that would break the code.
   - E741 (ambiguous `l`): list comprehension vars in leak-analysis code. Style-only, low priority.
   - E701 (multiple statements on one line): compact heuristic code. Style-only.
   - F401 in `__init__.py` re-exports: these are intentional side-effect imports for router registration. Suppress with ``# noqa: F401``.

5. **Verify with test suite:** Always run tests after lint fixes to confirm nothing broke.

## Pitfalls

- **Auto-fixes can remove imports that are used for side-effects** (e.g., API router registration in `__init__.py` files). Check for ``F401`` in `__init__.py` specially — these are often intentional.
- **`--unsafe-fixes` CAN remove variables that look unused but are actually needed** (e.g., assigned-then-never-read but used in a later block). Review the diff for F841 removals carefully.
- **E402 in test files** often follows a pattern of `sys.path.insert(0, ...)` then imports. Moving the import up above the path insertion would break the code. These are not real bugs.
- **F821 on string annotations** (e.g., ``game: "TexasHoldEm"``) is a false positive — Python string annotations are always valid forward references. Add ``# noqa: F821`` to suppress.
- **Always run `ruff check --statistics` after fixes** to see the full picture — the count tells you which category still has issues and whether you're making progress.