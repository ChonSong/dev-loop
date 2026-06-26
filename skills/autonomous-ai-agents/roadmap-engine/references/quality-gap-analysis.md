# Roadmap Engine — Quality Gap Analysis
**Session:** 2026-05-01 02:23 AM Sydney
**Context:** User said engine "not leveraging enough intelligence and tools to produce high quality outputs"

---

## What It's Actually Doing vs. Perceived

| Phase | Perceived | Reality |
|-------|-----------|---------|
| Phase 1 | Deep repo analysis | Greps TODOs + GitHub issues REST call only |
| Planner revision | LLM reasoning | 30-line heuristic: `if votes >= 3 promote` |
| Phase 2 code | TDD cycle | 2 hermes chat calls, commits regardless of test pass |
| Phase 2 research | Deep investigation | Single hermes chat, generic prompt |
| Quality gate | Tests pass = quality | Only runs tests if they exist; no lint/type-check/security |

---

## 5 Specific Failure Modes

1. **No task decomposition** — tasks handed whole to subagent; should be: identify APIs → smoke test → edge cases → verify coverage
2. **No context injection** — coder sees only `task['description']`; no source files, test patterns, CI config, imports
3. **No quality gates** — fails to compile = still commits; no lint/type-check/security scan
4. **No iteration** — first attempt fails → records learning, moves on; no retry with feedback
5. **No cross-task intelligence** — task A changes API → task B fails; engine doesn't notice relationship

---

## 8-Step Improvement Roadmap

### Immediate (this session)
1. **Context injection** — `_build_coder_context()` preloads source files + test patterns + config into coder prompt
2. **Quality gate** — run `ruff check` + `mypy` after tests, before commit; block on failure
3. **Task decomposition** — planning subagent in Phase 1 decomposes multi-step tasks

### This week
4. **Docker isolation** — run code/test tasks in containers per project stack
5. **CI signal reader** — Phase 1 reads GitHub Actions API for failures, creates tasks automatically
6. **Multi-source research** — research: web search + file analysis + GitHub issues + synthesis

### Medium term
7. **CI/CD pipeline** — GHA path filters + semantic-release + quality gate job + check_run webhook
8. **Monorepo migration** — Nx/Turborepo for shared tooling across projects

---

## CI/CD Strategy Document Review

**Good:** Monorepo vs polyrepo framing, Strangler Fig pattern, semantic versioning, path-based triggering

**Critical gaps:**
- No feedback loop from CI back to roadmap engine
- Docker mentioned but not wired into task execution
- Assumes self-managed CI server (not realistic for solo dev — lean into GHA instead)
- Path filtering needs concrete GHA YAML example

**Tailoring question to resolve:** Monorepo (Nx/Turborepo) or independent repos?

---

## Highest-Leverage Single Fix

```python
def _build_coder_context(task, local, proj):
    context_parts = []
    target = task.get("target_file", "")
    if target and (local / target).exists():
        context_parts.append(f"=== FILE: {target} ===\n{(local / target).read_text()}")
    for test_dir in ["tests", "test"]:
        if (local / test_dir).exists():
            for f in (local / test_dir).glob("test_*.py")[:2]:
                context_parts.append(f"=== TEST PATTERN: {f.name} ===\n{f.read_text()[:1000]}")
    for cfg in ["pyproject.toml", "package.json", "setup.py"]:
        if (local / cfg).exists():
            context_parts.append(f"=== CONFIG: {cfg} ===\n{(local / cfg).read_text()[:500]}")
    return "\n\n".join(context_parts)
```

Prepend output to coder system prompt. Estimated 2-3x quality improvement from this alone.
