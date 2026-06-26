# cwd-scanning for trigger matching

## The problem

First version of `match_triggers` only checked `context["files"]`. When
`session-startup` was called with `--cwd /workspace`, it added the cwd string
itself to the files list — but `/workspace` doesn't match `*linkedin*.py` even
though `/workspace/linkedin-post-v5.py` does. Result: zero matches in a
workspace with 8 linkedin-*.py files.

## The fix

When a `cwd` is provided to `gotcha show`, scan the immediate children and
add them to the context file list before matching:

```python
cwd = context.get("cwd")
if cwd and os.path.isdir(cwd):
    try:
        for entry in os.listdir(cwd)[:200]:  # cap at 200
            full = os.path.join(cwd, entry)
            context_files.append(full)
    except (PermissionError, OSError):
        pass
```

## Why cap at 200

- A typical project dir has 10-100 files
- A `/tmp` or `node_modules` can have 10K+
- 200 catches the relevant files (you almost never need to match files 201+ in a single session) without O(n) blowup on weird dirs
- If you need deeper matching, add explicit `--file <path>` args

## Why 1 level deep, not recursive

- Recursive scan = O(depth × fanout) = potentially O(10K+ files) on a real workspace
- Most trigger patterns target top-level files (entry points, configs)
- Recursive would also match files in `node_modules/`, `.venv/`, `__pycache__/` — false positives
- If you genuinely need recursive: add a `--recursive` flag explicitly, don't make it default

## When this DOESN'T apply

- The user passes `--file <path>` explicitly → use those files only
- The user passes `--command <cmd>` → match against commands, not files
- The user passes `--error <msg>` → match against error patterns, not files

The cwd-scan is a fallback for "I just want the gotchas for where I am" ergonomics.

## Test coverage

The `cmd_show` path in `gotchas/cli.py` has a test in the test script:
- `/workspace` → 8 linkedin files matched, score 10
- empty dir → "No matching gotchas"
- `/home/.../cloudflare-tunnel` → 1 cf-tunnel set, score 2
