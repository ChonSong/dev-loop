# Auto-Continue Log Entry Template

Append one entry per maintenance cycle. The log typically lives at one of three locations:
- **Shared path:** `/opt/data/auto-continue-log.md`
- **Inside the repo:** `<repo>/auto-continue-log.md` (previous runs may have written it here)
- **Subdirectory:** `/opt/data/auto-continue/log.md` (when /workspace/data/ doesn't exist)

Always run `find / -path '*/.*' -prune -o -name 'auto-continue-log.md' -print 2>/dev/null | head -5` first, but also try `/workspace/data/auto-continue-log.md` directly — it commonly exists there despite earlier claims to the contrary. The log can also live at `/opt/data/auto-continue-log.md`, `/opt/data/auto-continue/log.md`, or inside the repo directory itself. Try reading `/workspace/data/auto-continue-log.md` first, then `/opt/data/auto-continue-log.md`, then `/opt/data/auto-continue/log.md`. If none exist, create a new log at `/opt/data/auto-continue/log.md`.

## 2026-06-11 HH:MM UTC — R<N> T<N> (<short description>)
- **Repo:** /full/path/to/repo
- **What:** What was done, why, what was found
- **Commit:** <short sha> (if a commit was made)
- **Files:** <comma-separated list of changed files>
- **Verified:** <outcome of verification step — e.g. "go test clean, go build clean" or "ruff lint passes, 368/368 tests pass">
- **Next:** <next anticipated task to alternate to>
