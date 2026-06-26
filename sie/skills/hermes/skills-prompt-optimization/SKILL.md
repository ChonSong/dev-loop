---
name: skills-prompt-optimization
description: "Optimize Hermes skills system prompt to reduce token bloat. Patches prompt_builder.py to emit compact category-grouped skill index instead of verbose per-skill descriptions."
version: 1.0.0
author: Sean Cheong
license: MIT
metadata:
  hermes:
    tags: [optimization, tokens, skills, prompt-engineering]
---

# Skills Prompt Optimization

## Problem

The Hermes skills system prompt injects ~77K tokens per turn for 2,738 skills across 1,661 categories. Each skill gets its own `- name: description` line, sucking up 60%+ of the model's context window before any work begins.

## Root Cause

`build_skills_system_prompt()` in `prompt_builder.py` emits a verbose per-skill listing. With 2,738 installed skills, the index alone is 307K chars (~77K tokens).

Additionally, `_build_snapshot_entry()` derives categories from directory paths, creating 1,241 single-skill "pseudo-categories" from vendor-prefixed flat directories (e.g., `AgriciDaniel-claude-seo` is both the category AND the skill name).

## Solution: Compact Format

Replace verbose per-skill descriptions with:
1. **Category headers** with skill counts: `  microsoft: (133 skills)`
2. **Comma-separated name lists** (6 per line): `    azure-identity-py, azure-identity-ts, ...`
3. **Model discovers skills via `skill_view(name)`** on demand

### Patch Location

File: `/app/venv/lib/python3.12/site-packages/agent/prompt_builder.py`
Lines: 1164-1187 (inside `build_skills_system_prompt()`)

**IMPORTANT**: Patch the installed package copy, NOT the source at `~/.hermes/hermes-agent/`. Source and installed differ by 7 lines. A simple `git pull` will NOT apply this patch — it must be re-applied after each hermes-agent update.

### Patch Content

Replace the `else` branch that builds `index_lines` (originally lines 1164-1181) with compact category-grouped format:

```python
else:
    # ── Compact skill index ─────────────────────────────────────
    # Instead of listing every skill with its full description (~76K tokens),
    # emit category headers with skill counts and compact name lists.
    # The model uses skill_view(name) to load details on demand.
    # This saves ~70%+ tokens while preserving full discoverability.
    index_lines = []
    for category in sorted(skills_by_category.keys()):
        cat_desc = category_descriptions.get(category, "")
        # Deduplicate skill names within category
        seen = set()
        names = []
        for name, _desc in sorted(skills_by_category[category], key=lambda x: x[0]):
            if name not in seen:
                seen.add(name)
                names.append(name)

        count = len(names)
        desc_part = f" {cat_desc}" if cat_desc else ""
        index_lines.append(f"  {category}:{desc_part} ({count} skills)")
        # Compact name list: comma-separated, wrapped at ~6 per line
        for i in range(0, len(names), 6):
            chunk = ", ".join(names[i:i + 6])
            index_lines.append(f"    {chunk}")
```

### What NOT to Change

- **Preamble text** (lines 1184-1200): Model relies on this for skill discovery instructions
- **`<available_skills>` wrapper** (lines 1205-1207): Used by skill_view() to match skill names
- **Data collection logic** (lines before 1164): Still collects descriptions, just doesn't emit them
- **LRU cache** and **snapshot logic**: Untouched — they cache the data, not the format

### Results

| Metric | Original | Compact Format | + Vendor Grouping | Total Change |
|--------|----------|----------------|-------------------|--------------|
| Index chars | 308,838 | 153,072 | 84,545 | **-72.6%** |
| Est. tokens | ~77,209 | ~38,268 | ~21,136 | **-72.6%** |
| Skill entries | 2,741 (1,265 dupes) | 2,741 | ~1,476 unique | **46% dedup** |
| Categories | 1,662 | 1,662 | 686 vendor groups | **-58%** |

**Key discovery**: 1,259 skills had duplicate entries — stored in both `vendor/skill` and `vendor-skill` formats. Vendor grouping automatically deduplicates these, revealing the true unique skill count of ~1,476.

## Vendor Grouping Patch (Phase 2)

The compact format saved ~50% but left 1,662 categories (many single-skill vendor pseudo-categories like `microsoft-azure-identity-py`). Vendor grouping collapses these under vendor parents, achieving 72.6% total reduction.

### Problem

1,662 categories where ~1,241 are single-skill vendor pseudo-categories from flat directories. Example: `microsoft-azure-identity-py`, `microsoft-azure-identity-ts` are separate categories instead of grouped under `microsoft`.

Additionally, 1,259 skills exist in both `vendor/skill` and `vendor-skill` directory structures — both resolve to the same logical skill but appear as separate entries.

### Solution: Vendor Prefix Extraction

**File**: Same — `/app/venv/lib/python3.12/site-packages/agent/prompt_builder.py`
**Location**: Inside the compact format `else` branch (after the patch above), replace the `for category in sorted(skills_by_category.keys()):` loop header and add vendor extraction logic.

```python
# ── Vendor grouping ─────────────────────────────────────────────
# Collapses 1,662 flat categories into ~686 vendor groups.
# Handles both vendor-skill and vendor/skill naming conventions.
_VENDOR_PREFIXES = [
    "microsoft", "anthropics", "openai", "google", "nvidia", "firebase",
    "cloudflare", "github", "huggingface", "vercel", "netlify", "stripe",
    "auth0", "supabase", "notion", "linear", "resend", "redis", "qdrant",
    "coinbase", "binance", "polymarket", "docker", "traefik", "nginx",
    "wordpress", "flutter", "expo", "angular", "svelte", "react",
    # ... (full list sorted longest-first for prefix matching)
]

def _extract_vendor(category: str) -> str:
    """Extract vendor from category name. Handles vendor-skill and vendor/skill."""
    # Check vendor prefixes (sorted longest-first)
    for prefix in _VENDOR_PREFIXES:
        if category.lower().startswith(prefix.lower() + "-") or category.lower() == prefix.lower():
            return prefix
    # Fallback: treat as-is
    return category
```

Replace the category iteration with vendor grouping:

```python
# Group skills by vendor instead of flat category
vendor_groups: dict[str, list[tuple[str, str]]] = {}
vendor_seen: dict[str, set[str]] = {}

for category in sorted(skills_by_category.keys()):
    vendor = _extract_vendor(category)
    if vendor not in vendor_groups:
        vendor_groups[vendor] = []
        vendor_seen[vendor] = set()
    
    for name, desc in sorted(skills_by_category[category], key=lambda x: x[0]):
        if name not in vendor_seen[vendor]:
            vendor_seen[vendor].add(name)
            vendor_groups[vendor].append((name, desc))

# Emit vendor-grouped output
for vendor in sorted(vendor_groups.keys()):
    names = [n for n, _ in vendor_groups[vendor]]
    count = len(names)
    cat_desc = category_descriptions.get(vendor, "")
    desc_part = f" {cat_desc}" if cat_desc else ""
    index_lines.append(f"  {vendor}:{desc_part} ({count} skills)")
    for i in range(0, len(names), 6):
        chunk = ", ".join(names[i:i + 6])
        index_lines.append(f"    {chunk}")
```

### Results

| Metric | Before Vendor Grouping | After | Change |
|--------|----------------------|-------|--------|
| Categories | 1,662 | 686 vendor groups | -58% |
| Index chars | 153,072 | 84,545 | -45% |
| Est. tokens | ~38,268 | ~21,136 | -45% |
| Unique skills | 2,741 (1,259 dupes) | ~1,476 | 46% dedup |

### Important Notes

- `_VENDOR_PREFIXES` must be sorted **longest-first** to avoid `azure` matching before `azure-ai`
- The `_extract_vendor` function handles both `vendor-skill` and `vendor/skill` conventions
- Vendor grouping **automatically deduplicates** skills that appear under multiple category paths
- Full vendor list should be maintained to match installed skills — scan `ls ~/.hermes/skills/` to discover new vendors

## Vendor Grouping & Deduplication (COMPLETED)

Vendor grouping collapsed 1,662 pseudo-categories into 686 vendor groups, saving ~16K structural tokens. The `_extract_vendor()` function in `prompt_builder.py` uses a `_VENDOR_PREFIXES` list (~60 vendors, longest-first) to normalize both `vendor/skill` and `vendor-skill` naming formats into a single group key — automatically eliminating 1,259 duplicate path variants.

Full implementation details: `references/dedup-vendor-grouping.md`

## AGENTS.md Routing Cleanup (COMPLETED)

AGENTS.md reduced from 183→104 lines by:
- Replacing named agent tables (`zoul`, `codi`, `coder`, `security-reviewer`) with `delegate_task` + toolset mapping
- Moving heartbeat rules entirely to `HEARTBEAT.md` (authoritative source)
- Consolidating behavioral directives (no duplication between routing and rules sections)
- SKILL_SCHEMA.md created with `supersedes`/`deprecated` fields for formal dedup tracking

## Behavioral Skill Elevation Methodology

Not all skills are equal. Some encode **behavioral patterns** that should influence every turn, while others are **domain-specific tooling** loaded on demand. This section covers how to identify and elevate high-value skills to always-on directives.

### Elevation Criteria

A skill is a candidate for elevation to AGENTS.md/SOUL.md if it meets **3+ of these signals**:

| Signal | Description | Example |
|--------|-------------|---------|
| **Cross-cutting** | Applies to 80%+ of tasks, not just one domain | TDD, security review, context discipline |
| **Proactive behavior** | Changes how the agent acts before being asked | "research before coding", "plan before building" |
| **Safety guardrail** | Prevents costly mistakes or security issues | Pre-commit verification, secret scanning |
| **Context discipline** | Governs how context window is used | Skill loading limits, audit frequency |
| **Workflow enforcement** | Mandates a sequence or quality gate | RED-GREEN-REFACTOR, verification gates |

### Tier Classification

| Tier | Action | Token Budget | Examples |
|------|--------|--------------|----------|
| **Tier 1** | Bake into AGENTS.md as always-on rule | +40-60 tokens each | TDD, context-budget, search-first, security-review |
| **Tier 2** | Keep as skill but add trigger mention in directives | +15-25 tokens | coding-standards, requesting-code-review |
| **Tier 3** | On-demand only, no system prompt presence | 0 tokens | Domain-specific tooling (terraform, docker, etc.) |

### Current Tier 1 Candidates (Validated)

Based on analysis of 1,476 unique skills across 686 vendor groups:

| Skill | Cross-Cutting | Proactive | Safety | Context | Workflow | Score |
|-------|---------------|-----------|--------|---------|----------|-------|
| `test-driven-development` | ✅ | ✅ | ❌ | ❌ | ✅ | 3/5 |
| `context-budget` | ✅ | ✅ | ❌ | ✅ | ✅ | 4/5 |
| `search-first` | ✅ | ✅ | ❌ | ✅ | ❌ | 3/5 |
| `security-review` | ✅ | ✅ | ✅ | ❌ | ✅ | 4/5 |
| `systematic-debugging` | ✅ | ✅ | ❌ | ❌ | ✅ | 3/5 |

### Implementation Pattern

When elevating a skill to always-on directive:

1. **Extract the core rule** (1-2 sentences max) — not the full procedure
2. **Place in AGENTS.md** under `## 🔒 Core Behavioral Directives`
3. **Reference the skill** for detailed steps: "See `skill_view('test-driven-development')` for full RED-GREEN-REFACTOR procedure"
4. **Measure token impact** — each directive should cost <60 tokens
5. **Verify no duplication** — check existing directives before adding

### Example: TDD Elevation

```markdown
### Test-Driven Development Enforcement
- Write tests BEFORE implementation for any new feature (RED-GREEN-REFACTOR)
- Never commit code without corresponding tests
- Full procedure: `skill_view('test-driven-development')`
```

**Token cost**: ~45 tokens
**Behavioral impact**: Affects every coding task

## Further Optimization Opportunities

1. **Skill Quality Audit**: Verify `required_commands`, `linked_files`, and content validity across catalog; filter dead skills.
2. **On-disk snapshot caching**: `<24h` freshness check avoids regenerating index on every cold start.
3. **Dead skill detection**: Track skill usage over 30 days; flag skills never loaded for pruning.
4. **Filter empty stubs from index**: 2,538 of 2,761 skills are empty stubs (<10 body lines). They add ~75K chars to the index but provide zero value. Filtering them would save ~18K tokens. See `references/stub-filter-patch.md` for the prompt_builder.py patch.

## Caveman Mode (Primitive Operations)

For simple, single-tool tasks (read a file, run a command, quick search), the agent should NOT load skills. The current preamble says "load the skill even if you think you could handle the task" — this is intentional for complex work, but for primitive operations it wastes tokens scanning 2,700+ entries.

**Rule of thumb**: If the task needs exactly one tool call and no domain knowledge, skip the skill scan. If it needs 2+ tools or any domain-specific knowledge, scan normally.

This is NOT a separate skill — it's a behavioral note for the preamble's "when to load" guidance.

## Memory Hygiene (from June 2026 cleanup)

Memory stores have hard caps (2,200 chars for memory, 1,375 for user). When near capacity:

- **Remove tooling specifics** (paths, ports, binary locations, API endpoints) — these belong in skills
- **Remove stale infrastructure status** (broken services, paused jobs) — these are session state, not durable facts
- **Keep only**: user preferences, durable conventions, active project names, credentials referenced by skills
- **Target**: keep memory under 70% capacity for headroom

The same applies to MEMORY.md — it should be curated long-term facts, not a session log.

## Verification

After patching, confirm:
1. `build_skills_system_prompt()` returns compact format (test via Python import)
2. `skill_view("hermes-agent")` still loads correctly
3. `skill_view("software-development/plan")` resolves by category path
4. No snapshot file exists at `~/.hermes/.skills_prompt_snapshot.json` (cold path will regenerate)
5. LRU cache is in-memory only — clears on restart