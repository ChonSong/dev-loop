# Skill Selector Prep — Batch LLM Summary Generation

## Verified Working Configuration (2026-05-25)

### Model Selection
- **Working**: `poolside/laguna-xs.2:free` — returns content in `reasoning` field
- **Broken**: `openrouter/auto` (402), `google/gemini-2.5-flash-lite:free` (402), `openrouter/free` (routes to baidu cobuddy, content=None), `deepseek/deepseek-v4-flash:free` (error)
- **Extraction**: Check `reasoning` field, NOT `content` — response comes back in `reasoning`

### Background Processing — AVOID for Large Batches

The background summarizer (`proc_xxxxx`) times out at 600s when running large batches. For 1,000+ skills, use **synchronous batch processing** with `BATCH_SIZE=10`:

```bash
cd /home/hermeswebui/.hermes/scripts
python3 generate-skill-summaries.py 2>&1
```

Monitor progress — 8 batches × ~75s each ≈ 600s total (just fitting inside a subagent timeout if needed). For full catalog refresh, run as a **cron job** with `every 30m` and `repeat: "1/3"` or similar safety limit.

### Content Extraction Fix

The OpenRouter `poolside/laguna-xs.2:free` model returns the summary in the `reasoning` field, not `content`. Extract with:

```python
content = reasoning if reasoning else content
```

The `generate-skill-summaries.py` was patched to check `reasoning` field first.

### Catalog Statistics (2026-05-25)

| Source | Count |
|--------|-------|
| voltagent (GitHub) | 1,117 |
| local skills | 153 |
| mattpocock | 28 |
| 0xNyk | 20 |
| vercel | 1 |
| expo | 1 |
| **Total** | **1,320** |

### Skill Metadata Size (2026-05-25)

- `skill_metadata.json`: 153 local skills, ~50KB
- `skill_summaries.json`: 151 LLM summaries + 11 group descriptions, ~80KB
- Remote skills (voltagent + others): scored on description text only until summarized

### Parsing Fixes Applied

**1. voltagent parser** — `re.split(r'- (.*?) - ', line)` was missing `*?` (non-greedy). Fixed to `r'- \*?(.+?)\*? - '` to match `- **[org/skill](url)** - desc` pattern.

**2. 0xNyk parser** — two patterns:
- `**[beta]** [name](url)` — maturity tag handling
- `[name](url) by [author] - desc` — plain format
- **Unified parser**: split on last ` - ` occurrence — handles both patterns without explicit branching.

**3. Ghost entries cleanup** — skill_summaries.json had 167 TOC links and section headers that weren't in skill_metadata.json. These were removed via:
```python
valid_names = {s['name'] for s in skill_metadata['skills']}
summaries = [s for s in summaries if s['name'] in valid_names]
```

### Cron Schedule

Weekly Sunday 06:00 UTC — `skill-selector-prep` cron job (job ID computed from weekly hash).

### Cache Paths

```
/home/hermeswebui/.hermes/skill-selector-cache/
├── skill_metadata.json    # 153 local skills
├── context_scores.json    # per-workspace pre-computed
└── skill_summaries.json   # LLM summaries (151 + 11 groups)
```

All scripts in `/home/hermeswebui/.hermes/scripts/`:
- `skill-selector.py` — every-turn scorer (11.6KB)
- `skill-selector-prep.py` — cache builder (10.7KB)
- `generate-skill-summaries.py` — batch LLM summarizer (6.2KB)