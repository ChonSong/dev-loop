---
name: repo-portfolio-audit
description: "Systematically inventory, classify, evaluate overlap, and recommend consolidation actions across a portfolio of Git repositories. Produces a keep/merge/migrate/delete/observe map."
version: 1.1.0
---

# Repo Portfolio Audit

Evaluate a collection of repos from a **user-perspective** (not a technical-perspective): what does each project do for the user? Does it compete with another project? Could they be merged? Should any be deleted?

## Critical Rule: Full Investigation Before Any Deletion

**Never recommend deleting a repo without first proving it has no value.** "Stale" or "not used in a while" is NOT sufficient justification. Every deletion candidate requires:

1. **What does it actually do?** — Full directory tree (excluding node_modules, .git), README, key source files, package.json/pyproject.toml, git log
2. **What functionality does it provide?** — Not just a label ("experiment", "stale"), but an inventory of what code, configs, data, or documentation lives there
3. **What replaces that functionality?** — Name the specific repo, file, or service that covers the same purpose. If nothing replaces it, the repo stays or gets archived — not deleted. If the replacement is partial, explicitly list what would be LOST.
4. **Detailed breakdown showing no value** — Walk through the directory structure, explain why each component is disposable. If the only replacement is "the code works but isn't needed", say so explicitly.

**GitHub remotes are separate from local copies.** Deleting a local repo does NOT delete its GitHub remote. Always check what repos exist on GitHub separately. Some repos (GitHub Pages sites, backup history, active forks) should stay on GitHub even when the local copy is removed. Present the user with a clear list: "GH repos to DELETE: X, Y. GH repos to KEEP: A, B (reason)."

**Check for exposed credentials before deletion.** Scan scripts/configs for hardcoded API keys, tokens, passwords. Note them for rotation BEFORE deleting the repo. Run `grep -r 'sk-[a-zA-Z0-9]\{20,\}\|[0-9]\{8\}:[a-zA-Z0-9_-]\{35\}' --include='*.sh' --include='*.py' --include='*.env'` to catch common patterns.

**Check for running infrastructure.** Before deleting a repo, verify it isn't the local checkout for a running Docker container or systemd service. Run `docker ps` and check for references in `/etc/systemd/` and `~/.config/systemd/user/`.

**Example of a proper deletion analysis:**

```
❌ Repo X (200K)

DIRECTORY TREE:
  .git/
  backup.sh      — Clonezilla disk imaging script
  config.sh      — API token + backup target config

WHAT IT DOES: One-off backup automation. Pulled from gutgyv/clonezilla-backup upstream.

WHAT REPLACES IT: The upstream repo at gutgyv/clonezilla-backup still exists.
This is a local clone of someone else's code with no modifications.
No running services or cron jobs reference it.

VERDICT: DELETE — not your code, preserved upstream, no local value.
```

**Example of a WRONG analysis (what NOT to do):**

```
❌ Repo X — old, not used, delete it
```

**Why this rule exists:** Most repos have genuine value once investigated properly. In a real audit of 48 repos, the initial "delete 18" recommendation was wrong for most — only 6 actually had no value after full investigation. The rest contained live services, running infrastructure, unique code not replicated elsewhere, or irreplaceable configuration/data. See `references/2026-06-14-audit-results.md` for the full corrected audit.

## Process

### Phase 1 — Inventory

Gather metadata on every repo:

```bash
for repo in */; do
  repo=${repo%/}
  size=$(du -sh "$repo" | cut -f1)
  last_commit=$(git -C "$repo" log --oneline -1)
  has_lang=""
  [ -f "$repo/go.mod" ] && has_lang="$has_lang go"
  [ -f "$repo/pyproject.toml" ] || [ -f "$repo/setup.py" ] && has_lang="$has_lang python"
  [ -f "$repo/package.json" ] && has_lang="$has_lang node"
  [ -f "$repo/Cargo.toml" ] && has_lang="$has_lang rust"
  readme=$(head -5 "$repo/README.md" 2>/dev/null | head -c 120 | tr "\n" " " || echo "no_readme")
  tests=$(find "$repo" -name "test_*" -o -name "*_test*" -o -name "*.spec.*" 2>/dev/null | wc -l)
  echo "$repo|$size|$has_lang|$last_commit|$readme|tests:$tests"
done
```

### Phase 2 — Cluster by Domain

Group repos by functional domain:
- **Poker** — solvers, hand eval, training, game theory
- **Dashboard** — system UI, agent dashboards, telemetry
- **AI/Agent** — agent frameworks, circuit breakers, task routing
- **Web Presence** — landing pages, domain configs, chat assistants
- **System** — infrastructure scripts, backups, monitoring
- **Large Third-Party** — forked or upstream repos not authored by user
- **Knowledge/Docs** — guides, planning docs, dotfiles
- **Misc** — everything else

### Phase 3 — Deep-Dive Each Cluster

For each repo in a cluster:

1. **What does it actually do?** — Read README, key source files, package.json/pyproject.toml. Run `find . -not -path './.git/*' -not -path '*/node_modules/*' -type f | sort` to see all files.
2. **Is it active?** — Last commit date, test count, CI status, is it running in production?
3. **Is it unique?** — Does another repo already do this? Could they merge?
4. **User value** — Does this help the user's goals, or is it a past experiment?
5. **⚠️ If considering deletion, apply the Critical Rule above first.**

### Phase 4 — Overlap Analysis

The key question for overlapping repos: **does one app already cover the other's functionality?**

Build a feature matrix. Example:

| Feature | Repo A | Repo B | Notes |
|---|---|---|---|
| Web UI | ✅ | ✅ | Both have frontends |
| Solver | ✅ Python | ✅ Rust | B is 10× faster |
| Hand eval | ✅ | ✅ | Same results |
| Training mode | ✅ | ❌ | Unique to A |
| Bunching effect | ❌ | ✅ | Unique to B |

Be precise about what each repo uniquely provides. Don't assume architectural differences are irrelevant — in-browser WASM execution vs server-side CPU is a real design tradeoff.

### Phase 5 — Recommendations

Each repo gets one of:

| Classification | Meaning | Action |
|---|---|---|
| 🏆 **Keep** | Active, valuable, running | Continue development as-is |
| 🔄 **Merge / Vendor** | Overlaps with KEEP target | Absorb into the target repo, delete standalone |
| 🔄 **Migrate** | Being replaced by successor | Stop new development, port features forward |
| 👁️ **Observe** | Minimal value, not hurting | Maintain lightly, no active development |
| ❌ **Delete** | Redundant, stale, no value | Archive and remove local copy. For the full execution playbook (backup, containers, images, GitHub, config, skills cleanup), use `project-decommissioning`. |
| ❓ **Discuss** | Unknown purpose | Ask user before classifying |

### Consolidation Patterns

**Poker consolidation** — typical pattern: one full-stack app (UI + solver + training) absorbs libraries and alternative UIs as vendored dependencies:
- Standalone Rust solver → compile as PyO3 native extension
- Standalone game library → vendor into packages/
- Standalone web UI → evaluate carefully: if it has unique features (WASM execution, donk betting, 16-bit precision), keep it

**Dashboard consolidation** — when a successor project exists:
- Legacy: more features, older architecture, PostgreSQL
- Successor: better architecture (Go single binary, Svelte 5), fewer features, no database
- Strategy: port features forward, stop backporting
- **Don't delete the legacy until the successor functionally replaces it**

## Pitfalls

- **Don't delete forks of active upstream repos** — if upstream is active, you lose pull ability. Document as "vendored" instead.
- **Size can be misleading** — node_modules inflates size. Check actual source with `du -sh --exclude=node_modules`. Some "196M" repos are only 1-2M of actual code.
- **"Active" means different things** — upstream project may be maintained even if your fork hasn't pushed. Check original repo.
- **Tests don't equal quality** — 1000 unit tests of questionable value < 5 real workflow E2E tests. Check what the tests actually assert.
- **Don't rush deletion** — archive first, delete after a settling period. Give the user a chance to push back.
- **"Not used in a while" is NOT a deletion signal** — repos contain reference implementations, running services, historical context, vendored dependencies, and irreplaceable configuration. Investigate before labeling.
- **Check for security-sensitive content** — hardcoded API keys, tokens, and credentials may be present in scripts/configs. Note these for rotation before deletion.
- **Check for running infrastructure** — a repo may serve as the local checkout for a running Docker container or systemd service. Check `docker ps` and `systemctl` before deleting.

## Related Skills

- `project-decommissioning` — execution playbook for safely removing a project (containers, images, GitHub repo, local clone, config, skills, catalog). Run this *after* the user approves a ❌ Delete recommendation.
