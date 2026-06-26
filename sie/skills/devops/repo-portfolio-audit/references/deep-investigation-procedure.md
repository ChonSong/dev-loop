# Deep Investigation Procedure for Repo Evaluation

Use this when evaluating whether a repo can be deleted, merged, or kept. This is the step-by-step process derived from the June 2026 audit correction.

## Tier 1 — Metadata Scan (2 min per repo)

```bash
# Full file listing (exclude noise)
find /home/sc/repos/<repo> -type f -not -path './.git/*' -not -path '*/node_modules/*' | sort

# Actual content size
du -sh /home/sc/repos/<repo> --exclude=.git --exclude=node_modules

# Git activity
git -C /home/sc/repos/<repo> log --oneline -10
git -C /home/sc/repos/<repo> remote -v

# Language detection
[ -f <repo>/go.mod ] && echo "go"
[ -f <repo>/pyproject.toml ] || [ -f <repo>/setup.py ] || [ -f <repo>/requirements.txt ] && echo "python"
[ -f <repo>/package.json ] && echo "node"
[ -f <repo>/Cargo.toml ] && echo "rust"
[ -f <repo>/Dockerfile ] && echo "docker"
```

## Tier 2 — Functionality Understanding (5 min per repo)

Read, don't skim:

1. **README.md** — entire first screen. What does the author say this project does?
2. **package.json / pyproject.toml / Cargo.toml** — dependencies tell you what it connects to
3. **Key source files** — the entry point (main.py, index.ts, main.go, lib.rs, server.py, cli.py)
4. **Config files** — config.yaml, .env.example, docker-compose.yml live tell you what infrastructure it assumes
5. **AGENTS.md / CLAUDE.md** — if present, these contain the canonical purpose statement

**Ask: "If I delete this, what breaks?"** — not "when was it last touched?"

## Tier 3 — Infrastructure Check (3 min per repo)

Before labeling anything "delete":

```bash
# Is it running right now?
docker ps | grep <repo>
systemctl --user status <repo> 2>/dev/null

# Is any cron referencing it?
grep -r "<repo>" ~/.hermes/cron/ 2>/dev/null

# Is any tunnel routing to it?
grep -r "<repo>" ~/.cloudflared/config.yml 2>/dev/null

# Is any systemd service using it?
grep -r "<repo>" ~/.config/systemd/user/ 2>/dev/null
```

**A repo with zero recent commits but a running Docker container is NOT a "delete" candidate.**

## Tier 4 — Replacement Analysis (the hard part)

For each proposed deletion, write a specific replacement statement:

**Good:** "`clonezilla-backup` — the upstream repo at `gutgyv/clonezilla-backup` still exists and this local copy has no modifications."

**Good:** "`hermes-guide` — the canonical source is the GitHub Pages site at `chonsong.github.io/hermes-guide/`. The local docs/ directory is a build artifact."

**Bad:** "`wasm-postflop` — the functionality is covered by gto-wizard-clone's frontend." (WRONG: wasm-postflop's browser-native WASM execution model, donk betting, 16-bit precision, and tree editor are NOT in gto-wizard-clone.)

## Tier 5 — Security Scan

Before deleting a repo that could contain secrets:

```bash
# Search for potential tokens
grep -r "sk-[a-zA-Z0-9]\{20,\}" <repo> 2>/dev/null
grep -r "ghp_\|gho_\|github_pat" <repo> 2>/dev/null
grep -r "telegram\|TELEGRAM\|bot_token" <repo> 2>/dev/null
grep -r "API_KEY\|api_key\|apikey" <repo> 2>/dev/null

# Check .env and config files for exposed creds
find <repo> -name ".env" -o -name "*.env" 2>/dev/null
```

**If exposed creds found:** note them for rotation before deletion. The repo may contain a live token that needs revocation.

## Checklist — Is This Deletion Ready?

- [ ] Full directory structure documented
- [ ] README and key source files read
- [ ] Replacement named specifically (not "nothing" — if truly nothing, explain why that's OK)
- [ ] Running infrastructure checked (docker, systemd, cron, tunnel)
- [ ] Remote backup exists (GitHub/GitLab)
- [ ] Security scan done
- [ ] User has been shown the analysis, not just the conclusion
