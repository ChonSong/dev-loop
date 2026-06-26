# Broken Pipe Diagnosis

`[Errno 32] Broken pipe` on a cron job comes from **terminal.timeout** (default 180s), NOT the agent idle timeout (600s). A test suite or build exceeding 3 minutes gets killed, and the agent errors out as a cascade.

## Wrong Fix

Trimming the skill prompt to save tokens — this doesn't prevent broken pipes, it only reduces rate-limit pressure. The two issues are orthogonal.

## Right Fix

Increase `terminal.timeout` so long commands can finish:
```bash
hermes config set terminal.timeout 600
```

This applies to any project where `npx vitest run`, `npx turbo build`, `uv run pytest`, or similar takes >2 minutes.

## Empirical Evidence

2026-06-23 — player-development-loop was failing intermittently at `*/30 * * * *` with broken pipe. Increasing timeout from 180→600s fixed it. The earlier attempt to trim the prompt was reverted when the user pointed out the simpler fix.
