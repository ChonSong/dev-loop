# Documentation Task Delegation — Verification Pattern

## The Problem

When delegating documentation creation to subagents, the summary reports success but files may not exist at the expected path.

**Why:** Subagents run in isolated contexts with their own working directory. `write_file` paths in subagent context resolve relative to wherever the subagent process runs — not necessarily the controller's expected location.

## The Pattern

### DON'T trust the subagent summary for file existence

```bash
# Subagent reported: "Created /home/hermeswebui/.hermes/hermes-web-computer/AGENTS.md"
# Reality: check it
ls -la /home/hermeswebui/.hermes/hermes-web-computer/AGENTS.md  # may not exist
```

### DO verify with git status after every subagent documentation task

```bash
cd /home/hermeswebui/.hermes/hermes-web-computer && git status --short
```

If the file doesn't appear in `git status`, it wasn't written to the expected path. Re-read the subagent's actual working directory or create the file directly in the controller session.

## Code vs Documentation Tasks

| Task Type | Subagent Behavior | Verification |
|-----------|------------------|-------------|
| **Code** (Svelte, Go) | Times out after 600s, work on disk | `git status --short` after timeout — files usually exist |
| **Documentation** | Completes in <60s, reports success | `ls`/`git status` — file may not exist where expected |
| **Both** | Summary may say "wrote file" | No substitute for filesystem check |

## Known Cases

**hermes-web-computer AGENTS.md** (2026-05-24): Subagent reported "Done" but `ls` showed file NOT created. Controller created it directly via `write_file` in the main session.

**repo-transmute-v2 docs** (2026-05-24): Subagent correctly created files at `/home/hermeswebui/.hermes/repo-transmute-v2/` — verification passed.

The difference: absolute paths in the subagent `goal` string vs relative paths or ambiguous paths.

## When This Matters Most

- New repo root-level files (`AGENTS.md`, `README.md`, `*.md` in repo root)
- Files in `docs/` subdirectory
- Any time the subagent's task is "write file X" where X has a specific path

## Fix When Verification Fails

If `git status` shows the file wasn't created, create it directly in the controller session using `write_file`. Do NOT re-delegate the same task — the subagent will likely produce the same result.

## Prevention

In subagent goal strings for documentation tasks, always include:
```
CRITICAL: After writing the file, run `ls -la /absolute/path/to/file` to confirm it exists.
If the file does not exist at that exact path, create it using write_file tool before finishing.
```