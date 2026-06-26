# Skills Prompt Dedup & Vendor Grouping

## Problem
The skills catalog contains 3,945 entries, but ~1,259 are duplicate path variants of the same skill. Two naming conventions coexist:
- `vendor/skill` (directory-based, e.g., `NVIDIA/cuopt/cuopt-developer`)
- `vendor-skill` (hyphenated, e.g., `NVIDIA-cuopt-cuopt-developer`)

Both resolve to the same SKILL.md file on disk. Without deduplication, the skills prompt lists both, wasting ~15K tokens per turn on false entries.

## Solution: Vendor Grouping in prompt_builder.py

The deduplication happens automatically as a side effect of vendor grouping in `_generate_skills_prompt()`:

```python
def _extract_vendor(skill_name: str) -> str:
    """Extract vendor prefix from skill name."""
    lower = skill_name.lower()
    # Known vendors sorted longest-first to avoid prefix collisions
    for vendor in _VENDOR_PREFIXES:  # ~60 entries
        if lower.startswith(vendor + "-") or lower == vendor:
            return vendor
    return lower  # fallback: entire name is the group
```

### How It Works
1. Each skill name is passed through `_extract_vendor()` which returns a canonical vendor key
2. Both `NVIDIA/cuopt/cuopt-developer` and `NVIDIA-cuopt-cuopt-developer` → same vendor group `nvidia`
3. Skills are regrouped by vendor key, naturally deduplicating
4. Output format: `  vendor: (N skills)\n    skill1, skill2, ...`

### Vendor Prefix List
~60 known prefixes in `_VENDOR_PREFIXES`, sorted longest-first to prevent shorter prefixes from stealing longer ones (e.g., `NVIDIA-NeMo-RL` before `NVIDIA`). Includes:
- Multi-level: `NVIDIA-NeMo-RL`, `NVIDIA-Megatron-Bridge`, `NVIDIA-TensorRT-LLM`
- Single: `anthropic`, `openai`, `microsoft`, `google`, `cloudflare`
- Community: `garrytan`, `trailofbits`, `deanpeters`, `phuryn`

### Results
| Metric | Before | After |
|--------|--------|-------|
| Listed entries | ~2,741 | ~1,476 (unique) |
| Token count | ~77K | ~21K (skills portion) |
| Groups | 1,662 pseudo-categories | 686 vendor groups |
| Total system prompt | ~80K | ~23.5K |

## SKILL_SCHEMA.md
Formal frontmatter schema created at `/workspace/SKILL_SCHEMA.md`. Defines:
- **Required:** `name`, `description`
- **Optional:** `category`, `tags`, `source`, `is_imported`, `original_name`, `related_skills`, `required_commands`
- **New dedup fields:** `supersedes` (list of skill names this replaces), `deprecated` (bool), `deprecated_in_favor_of` (string)

The `supersedes` field enables the curator to prune superseded skills from the index and rewrite cron job references automatically.

## Patch Location
Always patch the **installed** copy, never the source:
- **Installed:** `/app/venv/lib/python3.12/site-packages/agent/prompt_builder.py`
- **Source (DO NOT PATCH):** `/home/hermeswebui/.hermes/hermes-agent/agent/prompt_builder.py`

The installed copy is what the running agent actually loads. Source changes only take effect after rebuild/reinstall.

## AGENTS.md Routing (Post-Cleanup)
After AGENTS.md slimming (183→104 lines), routing is toolset-based, not agent-based:
- Replace named agent tables (`zoul`, `codi`, `coder`, `security-reviewer`) with `delegate_task` + toolset mapping
- Keep HEARTBEAT.md as authoritative source — AGENTS.md only references it
- Behavioral directives consolidated (no duplication between routing and rules sections)
