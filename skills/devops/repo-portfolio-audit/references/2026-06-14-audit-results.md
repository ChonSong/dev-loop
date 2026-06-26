# 2026-06-14 Repo Portfolio Audit Results

Full audit of 48 repos. 6 deleted, 42 kept.

## Key Lesson

The initial "delete 18" recommendation was wrong for most. After deep investigation, only 6 repos had genuine no-value. The rest contained live services, unique code not replicated elsewhere, irreplaceable configuration/data, or were running in production.

## Investigative Triggers

For each repo consider:

1. **Is it a fork of an active upstream?** — Don't delete. You lose pull ability.
2. **Is it running in production?** — Check `docker ps`, `systemctl`, port listeners.
3. **Does another repo cover the SAME functionality?** — A web UI that runs in-browser WASM is NOT replaced by a server-side web UI. Different tradeoffs.
4. **Does it contain irreplaceable data?** — API keys, memory databases, device identity keys, agent session logs.
5. **Is it a Hermes skill?** — Even 200K skills are active tooling, not junk.

## Repos Deleted

| Repo | Size | Reason | Replacement |
|---|---|---|---|
| openclaw-backup-test | 112K | Empty repo, no commits | Nothing |
| clonezilla-backup | 200K | One-off script from upstream (gutgyv) | Upstream repo |
| seans | 32K | Superseded by seans-reporepo | seans-reporepo (auto-refreshing) |
| features-list | 4.2M | Static extract artifact from upstream | repo-transmute can re-extract |
| hermes-guide | 7.0M (local only) | GitHub Pages live site is canonical | GitHub Pages |
| system-backup | 301M | 6mo old backups, also on GitHub | GitHub keeps history |
| nanobot-workspace | 1.4M | Stale planning sandbox. Skills extracted. | Extracted to nanobot-workspace-extracted/ |

## Repos Kept After Investigation

| Repo (suspected for deletion) | Why Kept |
|---|---|
| wasm-postflop (196M) | Unique browser-native WASM solver. Donk betting, 16-bit precision, offline execution. NOT replaced by gto-wizard-clone's server-side model. |
| openclaw-backup (534M) | Contains live API keys, agent memory DBs, device identity. Irreplaceable. Browser/ dir pruned (17M). |
| starcraft-battlenet-web (316K) | Running Docker container (starcraft-vnc). Live infrastructure. |
| homepage-dashboard-sync (224K) | Active Hermes skill generating Homepage dashboard configs. |
| hermes-knowledge-graph (3.7M) | Static site generator + D3.js graph + codi agent docs. |
| ecosystem (908K) | Architecture docs, integration maps, roadmap. |
| forrest-plan-and-track (84M / 908K content) | Working Python analysis engine over OneTag HMAS database. |
| hermes-bootstrap (304K) | One-command Hermes install script. High value if bootstrapping. |
| hermes-telemetry (236K) | 198-line telemetry server, referenced in tunnel config. |
| features-list | KEPT initial assessment, then deleted after verifying upstream still exists. |
