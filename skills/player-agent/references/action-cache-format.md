# Action Cache Format

## Purpose

The Action Cache caches Solution Mapper outputs so that the Player agent can skip
re-running the Mapper step when a previously-seen task signature is detected with
unchanged source files. This saves 2-3 minutes per tick on repeated task patterns.

## Storage

- **Location:** `sie/knowledge-store/action-cache.db` (SQLite3, WAL mode)
- **Table:** `cache_entries`

## Schema

| Column            | Type    | Description                                          |
|-------------------|---------|------------------------------------------------------|
| `key`             | TEXT PK | SHA-256 of `task_type::project::primary_file_glob`   |
| `task_type`       | TEXT    | Task category, e.g. `fix-layout`, `add-feature`      |
| `project`         | TEXT    | Project name (matches AGENTS.md project key)         |
| `primary_file_glob` | TEXT  | Glob pattern identifying affected files, e.g. `apps/web/src/**/*.svelte` |
| `mapper_output`   | TEXT    | Full `<code_change_plan>` block from the Mapper      |
| `file_hashes`     | TEXT    | JSON object: `{"path/to/file.py": "sha256hex", ...}` |
| `created_at`      | TEXT    | ISO 8601 UTC timestamp of entry creation             |
| `last_accessed_at`| TEXT    | ISO 8601 UTC timestamp of last `get` hit             |
| `access_count`    | INTEGER | Number of times this entry produced a cache hit      |

## Cache Key

```
key = sha256(task_type + "::" + project + "::" + primary_file_glob)
```

The triple of (task_type, project, primary_file_glob) forms a unique task
signature. Two tasks with the same signature are considered equivalent for
caching purposes.

### Example

```bash
python3 action-cache.py get \
  --task-type fix-layout \
  --project gto-wizard \
  --primary-file-glob "apps/web/src/**/*.tsx"
```

## Invalidation Rules

### 1. File hash verification (on `get`)

When a cache hit occurs, every file path stored in `file_hashes` is re-hashed.
If **any** file's current SHA-256 differs from the stored value:

- The entry is **immediately deleted** from the cache
- The caller receives exit code 1 (miss)
- The Mapper step runs normally and produces a fresh entry via `set`

### 2. Manual invalidation (`invalidate` command)

Explicitly removes an entry by key when the caller knows files have changed
but wants to clear the cache proactively.

### 3. Age-based eviction (`prune` command)

Entries older than 7 days (based on `created_at`) are evicted.

### 4. Capacity-based eviction (`prune` command)

When total entries exceed 50, the least-recently-accessed entries (by
`last_accessed_at`) are evicted until the count drops to 50.

## CLI Commands

### `get` — Retrieve cached mapper output

```bash
python3 action-cache.py get \
  --task-type <type> \
  --project <name> \
  --primary-file-glob <glob>
```

- **Hit:** prints mapper output to stdout, exits 0
- **Miss or stale:** prints reason to stderr, exits 1

### `set` — Save a cache entry

```bash
# From stdin:
echo "$mapper_output" | python3 action-cache.py set \
  --task-type <type> \
  --project <name> \
  --primary-file-glob <glob> \
  --hash "src/file.py:<sha256>" \
  --hash "src/other.py:<sha256>"

# From file:
python3 action-cache.py set \
  --task-type <type> \
  --project <name> \
  --primary-file-glob <glob> \
  --file /tmp/mapper_output.txt \
  --hash "src/file.py:<sha256>"
```

### `invalidate` — Remove an entry

```bash
python3 action-cache.py invalidate \
  --task-type <type> \
  --project <name> \
  --primary-file-glob <glob>
```

### `stats` — Print cache statistics

```bash
python3 action-cache.py stats
# Output: JSON with total_entries, max_entries, total_accesses, hit_rate_pct, db_size_bytes, oldest_entry, newest_access
```

### `prune` — Evict old or excess entries

```bash
python3 action-cache.py prune
# Evicts entries older than 7 days, then LRU-evicts until count ≤ 50
```

## Integration with Player Workflow

```
Step 3.5 (Action Cache Check):
  1. Generate cache key from current task
  2. Call "action-cache.py get"
  3. If HIT → use cached mapper output, skip to Step 4 (Solver)
  4. If MISS → continue with Step 3 (Mapper)

Step 3 (Mapper), after producing output:
  1. Compute file hashes for touched files
  2. Call "action-cache.py set" with the mapper output + file hashes
```
