# Case Study: tunnel 404 — the 1,250-message debugging spiral

This is the specific case that motivated the entire agent-ops system.
Every number below comes from real session transcripts at
`/home/hermeswebui/.hermes/sessions/`. Use it to calibrate expectations.

## The problem

User reported: `hermes.codeovertcp.com is down error 1033`

## What actually happened (5 sessions, ~1,250 messages)

| Session | Messages | Real tool errors | Top tools |
|---|---|---|---|
| `...015609_59f8da` | 286 | 12 | terminal:105 |
| `...014235_61fd61` | 226 | 11 | terminal:88 |
| `...021342_09ffec` | 319 | 16 | terminal:118 |
| `...65147d4a0940` | 322 | 20 | terminal:136 |
| `...022532_103bf1` | 342 | 20 | terminal:136 |

Same first user message every time: "hermes.codeovertcp.com is down
error 1033". Same root cause every time. Different debugging paths
each time because the agent had no continuity.

## The 4 NoneType.get() crashes

In session `...022532_103bf1` alone, the agent crashed 4 separate
times on the same pattern:

```
AttributeError: 'NoneType' object has no attribute 'get'
KeyError: 'zone_id'
```

Root cause: Cloudflare API responses with `result: null` (empty lists,
auth failures, duplicate names). Agent's pattern: `data['result'].get('field_id')`.
Crashes every time `result` is null.

After 4 crashes, agent eventually added `.get('result', {}) or {}` to
the parsing. **This is a 50-message fix that should have been a
5-line schema.**

## The 15 gotchas (what was learned across all 5 sessions)

Backfilled into `gotchas/sets/cf-tunnel.yaml` from the 200-line
`/home/hermeswebui/.hermes/skills/devops/cloudflare-tunnel/SKILL.md`:

1. API endpoint: `cfd_tunnel` not `tunnels` (4 occurrences)
2. Ingress config drops hostnames silently (5 occurrences)
3. cloudflared binary on /tmp gets wiped (3 occurrences)
4. Stale credentials after recreate (2 occurrences)
5. `--config` is global flag, order matters
6. Tunnel secret: 32+ random bytes, base64
7. Credentials file uses TunnelSecret, not JWT
8. Config changes need process reload
9. DNS CNAME 30-60s propagation
10. One cloudflared per tunnel ID
11. Quick tunnels: no SLA
12. `/token` endpoint: result is RAW STRING, not object
13. Duplicate name: returns null token
14. API tokens may lack tunnel permissions
15. Watchdog race: pgrep matches dying process

Each was discovered through 50-300 messages of debugging.

## What the gotcha system would have done

If the gotcha system had existed before these sessions:

- Session 1 (342 msgs): `gotcha show --error 1033` would surface
  cf-tunnel gotchas at message 1. The "API endpoint cfd_tunnel not
  tunnels" gotcha would lead directly to the fix in ~5 messages
  instead of ~150.

- Sessions 2-5: same. The gotcha was already known. The agent would
  start by checking the known list, not re-debugging.

**Estimated savings: 1,000+ messages across 5 sessions. ~$3 in API
costs. ~30 minutes of agent + user time per session.**

## What the schema validation would have done

If `validate cloudflare-api-generic.json` had been run on every
API response:

- 4 NoneType crashes in session `...022532_103bf1` would have
  become 4 schema-validation errors at parse time, each pointing
  to the exact problem and the gotcha to read.

- No code would have crashed. No manual retry. No 50-message
  "add .get('result', {})" fix.

**Estimated savings: ~50 messages per session, every API-heavy
session going forward.**

## What the gated-terminal would have done

If terminal calls had been wrapped:

- The 136-call session would have aborted at call 6 of any identical
  failing command, or at 10 total failures, forcing the agent to
  reconsider approach.

- Even if the agent overrode with `GATED_BUDGET_OVERRIDE=1`, the
  warning at retry 3 ("Same command run 3 times. Consider: is the
  approach wrong?") would have triggered earlier reconsideration.

**Estimated savings: 50-100 messages per runaway-loop session.**

## Honest limitations of this case study

- The savings are estimated, not measured (we have no A/B test).
- Some of the 1,250 messages were useful exploration that wouldn't
  be eliminated by the system.
- The 5 sessions were not identical — the agent made different
  choices each time, some of which the gotcha system couldn't have
  predicted.

Use this as calibration, not gospel. Run your own measurement on
your own sessions after the system is in place.
