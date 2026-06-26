# Hermes State DB — Session Analytics Queries

> Reference for building pipeline dashboards from `~/.hermes/state.db`.

## Database Location

```
~/.hermes/state.db
```

## Schema: `sessions` Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | TEXT | Session UUID |
| `source` | TEXT | Origin: `cron`, `webui`, `subagent`, `cli`, `api_server`, `discord`, `tui` |
| `model` | TEXT | Model name, e.g. `deepseek-v4-flash`, `openrouter/owl-alpha` |
| `started_at` | REAL | Unix timestamp (seconds) |
| `ended_at` | REAL | Unix timestamp (seconds), nullable |
| `message_count` | INTEGER | Messages exchanged |
| `tool_call_count` | INTEGER | Tool calls made |
| `input_tokens` | INTEGER | Tokens sent to LLM |
| `output_tokens` | INTEGER | Tokens received from LLM |
| `estimated_cost_usd` | REAL | Cost estimate |
| `parent_session_id` | TEXT | Parent session UUID (for subagent chains) |
| `archived` | INTEGER | 0=active, 1=archived |

## Base Query

```python
import sqlite3, pandas as pd
from datetime import datetime

DB = os.path.expanduser("~/.hermes/state.db")
DAYS = 7

conn = sqlite3.connect(DB)
df = pd.read_sql(
    """SELECT id, source, model, started_at, ended_at, end_reason,
              COALESCE(message_count, 0) AS message_count,
              COALESCE(tool_call_count, 0) AS tool_call_count,
              COALESCE(input_tokens, 0) AS input_tokens,
              COALESCE(output_tokens, 0) AS output_tokens,
              COALESCE(estimated_cost_usd, 0) AS estimated_cost_usd,
              parent_session_id, title, cwd
       FROM sessions
       WHERE started_at > ? AND archived = 0
       ORDER BY started_at""",
    conn,
    params=(datetime.now().timestamp() - DAYS * 86400,),
)
conn.close()
```

## Derived Columns

```python
df["started_dt"] = pd.to_datetime(df["started_at"], unit="s", utc=True)
df["ended_dt"] = pd.to_datetime(df["ended_at"], unit="s", utc=True)
df["dur_s"] = (df["ended_dt"] - df["started_dt"]).dt.total_seconds()
df["dur_min"] = df["dur_s"] / 60.0
df["date"] = df["started_dt"].dt.date
df["hour"] = df["started_dt"].dt.hour
df["day_of_week"] = df["started_dt"].dt.day_name()
df["total_tokens"] = df["input_tokens"] + df["output_tokens"]
df["model_short"] = df["model"].str.split("/").str[-1].str[:20]
```

## Gap Computation

```python
s = df.sort_values("started_at")
s["gap_s"] = s["started_at"] - s["ended_at"].shift(1)
s["gap_min"] = s["gap_s"] / 60.0
# First session has NaN gap — that's expected
```

## Session Count & Model Distribution

```python
counts = df["source"].value_counts()
# Also: model distribution for the pie chart
model_counts = df["model"].value_counts()
```

## Key Stats for KPIs

```python
median_duration = df["dur_min"].median()
median_gap = s["gap_min"].median()
total_tokens = df["total_tokens"].sum()
total_sessions = len(df)
session_chain_depth = df["parent_session_id"].notna().sum()  # continuity
```

## Cost Tracking

Cost columns (`estimated_cost_usd`, `actual_cost_usd`) exist in the schema but may be `0` for non-configured providers. Check `cost_source` and `billing_provider` columns before reporting cost data.
