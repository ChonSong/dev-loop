---
name: affine-logger
description: |
  AFFiNE-compatible logger. Creates journal entries in local JSON log file with AFFiNE-compatible format.
  Can later be synced to AFFiNE when self-hosted instance is available.
  Use this skill for logging system telemetry and diagnostics.
metadata:
  author: journal-agent
  version: "1.0"
---

# affine-logger

Local-first logger with AFFiNE-compatible schema. Creates journal entries that can later be synced to an AFFiNE instance.

## Configuration

### Environment Variables

- `AFFINE_URL` - Your AFFiNE instance URL (optional, for future sync)
- `AFFINE_TOKEN` - Your AFFiNE API token (optional, for future sync)
- `JOURNAL_LOG_PATH` - Path to local log file (default: /home/sean/.openclaw/agents/journal/memory/journal.jsonl)

## Usage

### Log Entry

```bash
node scripts/affine-logger.mjs log --title "System Status" --content "Errors: 2, Warnings: 1" --tags "error,warning"
```

### List Recent Entries

```bash
node scripts/affine-logger.mjs list --limit 10
```

### Export to AFFiNE (when configured)

```bash
node scripts/affine-logger.mjs sync
```

## Output Format

Each entry in the JSONL file follows this schema:

```json
{
  "id": "uuid",
  "title": "System Status",
  "content": "Errors: 2, Warnings: 1",
  "tags": ["error", "warning"],
  "created": "2026-03-16T12:00:00Z",
  "synced": false
}
```

## AFFiNE Integration (Future)

When `AFFINE_URL` and `AFFINE_TOKEN` are set, the `sync` command will:
1. Connect to your AFFiNE instance
2. Create a new page in the specified workspace
3. Format content using AFFiNE's block-based format
4. Mark entries as synced in local storage
