# Time Budget Rules for Player Ticks

Each tick has a hard ~500s tool-call limit. Use this table to know when to bail on a phase:

| Phase | Target | If exceeded |
|-------|--------|-------------|
| State intent + codebase survey | ≤ 30s | Skip survey, read one key file only |
| Task size pre-check | ≤ 10s | Assume task fits, revert if wrong |
| Design tree walk (if needed) | ≤ 30s | Make best-guess decision, flag in report |
| Implementation (writing code) | ≤ 120s | Revert and log a blocker — task too large for one tick |
| TDD cycle (RED → GREEN) | ≤ 60s | Skip test-first, implement then test |
| Pre-commit self-review | ≤ 30s | Commit without review, note the gap |
| Test suite run | ≤ 180s | Use `-q` or `--timeout` flags; skip very slow sections |
| Build/dependency install | ≤ 300s | If longer → setup blocker, report and stop |
| End-of-tick capture | ≤ 15s | Skip capture, checkpoint is sufficient |

**Total hard limit**: 500s of tool-call time. Beyond this, you risk the 600s idle wall (tool calls count as activity, but prolonged processing between them does not).
