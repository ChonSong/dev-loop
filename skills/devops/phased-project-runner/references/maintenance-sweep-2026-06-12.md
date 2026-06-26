# Maintenance Sweep — 2026-06-12

## R1: hermes-web-computer (Go)
- **Path:** `/opt/data/hermes-web-computer`
- **State:** Fully clean. All tests pass, build OK, vet clean, gofmt has zero project-source diffs.
- **Tests:** 5 packages test clean (audio, layout, security, session, ws).
- **Notes:** gofmt diffs only appear in `.gopath/` vendored deps. Project source `find . -name '*.go' -not -path './.gopath/*'` shows zero formatting issues.
- **Mod verify:** `go mod verify` passes. No dependency drift.

## R2: gto-wizard-clone (Python monorepo)
- **Path:** `/tmp/gto-wizard-clone`
- **Initial ruff errors:** 387
- **After `ruff check --fix`:** 122 (265 fixed)
- **After `ruff check --unsafe-fixes --fix`:** 85 (37 more fixed)
- **After `ruff format`:** 53 (32 more from formatting merge + E701 manual fixes)
- **Remaining 53 (all intentional):**
  - 32× E402: lazy imports in verify_final.py, inline sys.path.append patterns
  - 12× F401: router __init__.py side-effect imports, try/except availability checks
  - 2× F821: string annotations in nodes.py (forward refs)
  - 1× F403: wildcard import in verify_final.py
- **Real bugs found and fixed:** 6 missing imports
  - `timezone` missing in broadcast.py, handlers.py
  - `os` missing in test_grpc_service.py, tasks.py
- **E741 fixes:** 9 ambiguous `l` → `leak` in analyze_leaks.py (4), courses.py (1), gto_comparison.py (4)
- **E701 fixes:** 9 multi-statement lines in trainer.py
- **Verification:** All 106 modified files compile with `python -m py_compile`
- **Commit:** `362fd9c` — 106 files, 7644 insertions, 6543 deletions
