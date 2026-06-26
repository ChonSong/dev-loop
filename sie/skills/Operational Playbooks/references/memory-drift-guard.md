# Memory Tool Drift Guard

The Hermes memory tool (`memory`) refuses to write **MEMORY.md** when the file on disk has content that wouldn't round-trip through the tool's internal representation. This guard exists to prevent silent data loss (issue #26045).

## Detection

The `memory` tool returns:
```
Refusing to write MEMORY.md: file on disk has content that wouldn't round-trip through the memory tool
(likely added by the patch tool, a shell append, a manual edit, or a concurrent session).
A snapshot was saved to /home/sc/.hermes/memories/MEMORY.md.bak.<timestamp>.
Resolve the drift first — either rewrite the file as a clean §-delimited list of entries,
or move the extra content out — then retry.
```

## Root Cause

The memory tool stores entries internally in a `§`-delimited format. The daily Memory Curation cron job (or manual edits via `patch`/`write_file`) writes MEMORY.md in **markdown format** (with headings, bullet lists, section separators). The next `memory(action=add/remove/replace)` call fails because the tool parses the file and finds content it didn't create.

## Resolution

### Quick Fix (Use This)

Write a clean version of MEMORY.md directly via `terminal` or `write_file`, then retry the memory operation:

```bash
# On the host:
cp /home/sc/.hermes/memories/MEMORY.md /home/sc/.hermes/memories/MEMORY.md.bak.$(date +%s)

# Write a clean markdown version with the same facts
cat > /home/sc/.hermes/memories/MEMORY.md << 'EOF'
# Memory — User's Hermes System
...
EOF

chmod 600 /home/sc/.hermes/memories/MEMORY.md
```

### Prevention

The issue self-heals on the next daily Memory Curation cron run (typically at 16:00), which overwrites MEMORY.md with its own §-delimited format. The memory tool will work again after that.

### When to Just Wait

If the stale data is acceptable and you don't need to add memory immediately, do nothing — the curation job fixes it within 24 hours. Only intervene if you need to record a fact *now*.

## Related

- The curation cron runs daily at 16:00 AEST and overwrites MEMORY.md with distilled facts from session_search.
- Backups accumulate in `/home/sc/.hermes/memories/MEMORY.md.bak.*` — clean old ones periodically.
