# Requirements Engine — Evaluation Rubric

## Overview

Each BUILD-candidate signal from the Opportunity Radar is scored on four dimensions. Items must reach a **combined threshold of ≥12/20** to proceed to the spec phase.

---

## Scoring Dimensions

### 1. Domain Alignment (max 5)

How well the opportunity aligns with our strategic domains.

| Score | Domain                 |
|-------|------------------------|
| 5     | Poker / GTO            |
| 4     | Game Development       |
| 3     | AI Infrastructure      |
| 2     | 3D Concrete Printing   |
| 0     | Unrelated / Unknown    |

**Mapping logic:**

- The radar's `domain` field is mapped directly: `poker` → 5, `game-dev` → 4, `ai-agents` → 3, `3dcp` → 2.
- Unknown or unmatched domains score 0.
- Projects that span multiple domains take the **maximum** of the matched scores.

### 2. Build Complexity (max 5)

Estimated engineering effort to produce a working prototype.

| Score | Complexity Level    | Typical Characteristics                      |
|-------|---------------------|----------------------------------------------|
| 1     | CLI tool            | Single script, no UI, local-only             |
| 2     | Single-page webapp  | One HTML/JS page, minimal state              |
| 3     | Full-stack app      | Backend + database + frontend                |
| 4     | Game engine / 3D    | Real-time rendering, physics, or simulation  |
| 5     | Multi-service       | Microservices, distributed system, platform  |

**Estimation logic:**

- If the signal carries an explicit `build_complexity` field, use it.
- Otherwise, infer from domain and description keywords:
  - `cli`, `tool`, `script`, `utility` → 1
  - `web`, `dashboard`, `page`, `frontend` → 2
  - `api`, `backend`, `database`, `full-stack` → 3
  - `game`, `engine`, `render`, `3d`, `simulation` → 4
  - `platform`, `service`, `orchestration`, `multi` → 5
- Falls back to 3 (full-stack) if no keywords match.

### 3. Data / API Dependency (max 5)

Availability of required data sources or external APIs.

| Score | Dependency Level | Meaning                                             |
|-------|------------------|-----------------------------------------------------|
| 5     | None             | Self-contained; no external data needed             |
| 4     | Free APIs        | Public APIs (GitHub, arXiv, Wikipedia) available    |
| 2     | Paid API         | Requires paid service (OpenAI, Stripe, AWS credits) |
| 0     | No data source   | Data is inaccessible or doesn't exist               |

**Estimation logic:**

- If the signal carries an explicit `data_dependency` field, use it.
- Otherwise, infer from domain and description:
  - `poker` / `gto` → 4 (free data: hand histories, solver outputs)
  - `game-dev` → 5 (self-contained)
  - `ai-agents` / `ai-infra` → 4 (free APIs: OpenRouter free tier, HuggingFace)
  - `3dcp` → 2 (often requires hardware/sensor data)
- References to `API`, `data`, `database`, `stripe`, `openai`, `paid` in description lower the score.

### 4. Learning ROI (max 5)

Transferability of skills/knowledge gained from building this.

| Score | ROI Level           | Meaning                                          |
|-------|---------------------|--------------------------------------------------|
| 5     | High transferable   | Skills reuseable across many future projects     |
| 2     | Narrow              | Domain-specific; limited reuse                   |

**Estimation logic:**

- If the signal carries an explicit `learning_roi` field, use it.
- Otherwise, infer from domain:
  - `poker` / `ai-agents` → 5 (broad ML/strategy skills)
  - `game-dev` → 4 (graphics, UX, performance)
  - `3dcp` → 2 (niche domain, hardware-coupled)
- Unknown domains → 2 (conservative).

---

## Combined Scoring

```
combined_score = domain_alignment + build_complexity + data_dependency + learning_roi
```

- **Maximum possible:** 20
- **Threshold:** ≥ 12 → Proceed to spec phase
- **9–11:** Borderline — flags as "REVIEW" (manual decision needed)
- **≤ 8:** Rejected — recorded but not spec'd

---

## Edge Cases

### Missing domain
Scores 0 on domain alignment. Combined score will likely fail threshold unless other dimensions are maxed.

### Conflicting signals
If a BUILD item has contradictory metadata (e.g., domain=poker but description is about 3D printing), domain alignment takes precedence, but a warning is emitted.

### Duplicate titles
If two signals share the same `title` (case-insensitive), only the highest-scored one is processed. The duplicate is logged and skipped.

### Overridden scores
If any dimension is explicitly set in the input JSON (via `domain_alignment`, `build_complexity`, `data_dependency`, `learning_roi` fields), those values are used and heuristic inference is skipped for that dimension.

### Null / empty descriptions
Heuristic inference for build_complexity and data_dependency uses description keywords. If `description` is empty, fallback to domain-based defaults.

---

## Example Scoring

| Signal                          | Domain | Complexity | Data | ROI | Total | Result    |
|---------------------------------|--------|------------|------|-----|-------|-----------|
| GTO Range Viewer (CLI)          | 5      | 1          | 4    | 5   | 15    | ACCEPT    |
| 3DCP Slicer Web App             | 2      | 2          | 2    | 2   | 8     | REJECT    |
| AI Agent Benchmark Dashboard    | 3      | 2          | 4    | 5   | 14    | ACCEPT    |
| Poker Hand History Parser       | 5      | 1          | 4    | 5   | 15    | ACCEPT    |
| Minecraft Clone (Web)           | 4      | 4          | 5    | 4   | 17    | ACCEPT    |
| Unknown Domain Thing            | 0      | 3          | 0    | 2   | 5     | REJECT    |
