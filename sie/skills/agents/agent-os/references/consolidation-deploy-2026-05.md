# Session 2026-05-10: Full Consolidation Deploy

## Context
Merged work from two prior sessions (baabd3: nanobot→Hermes migration + repo-transmute Phase 7, 6e063d: TypeUI Bento frontend) into a clean deployed state.

## Commits Pushed (10 total)

| Commit | What |
|--------|------|
| `9c4aae3` | Dockerfile node binary fix |
| `910e541` | Hermes via host.docker.internal, remove redundant docker-compose service |
| `a73b0f4` | STATE_OF_AGENT_OS.md rewrite |
| `9df763e` | README + MASTER_PLAN rewrite, delete 3 stale docs |
| `5a84d67` | ChatPage SSE replacement (was broken xterm/PTY) |
| `7cfb0f6` | Remove agent-adapter package, rename nanobot refs to Hermes |
| `050ef58` | Wire observability (chat_message/chat_response events) |
| `a6d0ee0` | CI SSH deploy step |
| `01a3546` | STATE doc final update |
| `c59cc8c` | Dockerfile node_modules + symlink fix (supersedes `9c4aae3`) |

## Key Decisions

1. **Host Hermes is canonical** — removed redundant hermes service from docker-compose. Backend connects via `host.docker.internal:8642`.
2. **ChatPage rewritten** — replaced broken xterm.js/PTY with SSE-based chat matching ChatPanel widget.
3. **Observability wired** — backend now emits `chat_message` and `chat_response` events to `aie_events` table.
4. **pg_dump backup** — daily at 3am to `~/.hermes/backups/postgres/`, 7-day retention.
5. **CI deploy** — SSH-based, requires `DEPLOY_KEY` + `DEPLOY_HOST` secrets (set by user).

## Node Binary Fix Evolution

- **Attempt 1** (`9c4aae3`): `COPY --from=ts-build /usr/local/bin/node /usr/local/bin/node` — works for the binary, but `npm` and `corepack` are symlinks that become dangling.
- **Attempt 2** (`c59cc8c`): Copy `/usr/local/lib/node_modules` (the actual files) and recreate symlinks with `RUN ln -sf`. This is the correct approach.

## Container Status at End

| Container | Status |
|-----------|--------|
| agent-os-backend | Rebuilding (new image with node_modules fix) |
| agent-os-postgres | Healthy |
| agent-os-cloudflared | Running (tunnel still broken — wrong hostname) |
| agent-os-webhook-emitter | Healthy |

## Remaining Issues

- Cloudflared tunnel needs `--network-alias backend` on backend container
- GitHub PAT expired — can't set secrets via API, user set manually
