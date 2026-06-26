# agent-os Master Plan (2026-05-09)

Full plan written to: `/opt/data/agent-os/MASTER_PLAN.md`

## Phase Summary

| Phase | Status | Description |
|-------|--------|-------------|
| 1: Stabilize & Deploy | Pending | Clean disk, rebuild image, deploy, fix CI deploy |
| 2: Wire Observability | Pending | Hook AIELogger → AgentLoop, populate dashboard |
| 3: Robustness | Pending | Backup cron, watchdog, remove dead code |
| 4: Feature Expansion | Pending | MCP real, Chat parity, Swarm Mode, AppStore |
| 5: Polish | Pending | PWA, multi-user, file upload |

## Key Decisions Pending

1. **Disk cleanup** — Docker prune weekly (user approved)
2. **Docker image** — Remove frontend-dist volume override, bundle into image (user approved)
3. **CI deploy** — SSH-based deploy on push to main (user approved)
4. **Observability** — HTTP POST to backend vs direct DB write (pending)
5. **Backup strategy** — GitHub + local, 7-day retention (user approved)
6. **Watchdog alerting** — Email (user approved)
7. **Dead code** — Keep stubs, implement later (user approved)
8. **MCP integration** — Use Hermes, not nanobot (user approved)
9. **Chat priority** — Markdown > Syntax highlight > Context meter > Slash commands > Forking (user approved)
10. **Agent core** — Replace nanobot with Hermes (pending decision: container vs host proxy)

## Effort Estimate: 5 phases, ~14+ days total
