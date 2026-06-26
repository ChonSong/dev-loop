# Vision QA Prompting — Lessons from Session 2026-06-10/11

## The Problem

vision_analyze was used for document QA but gave unreliable "8-9/10" ratings that didn't match the user's assessment. The user said PDFs "still look awful" despite vision giving positive ratings.

## Root Cause

The vision model was prompted with vague "rate 1-10" questions. It didn't know what specific criteria to evaluate. When asked generally, it gave generally positive responses — missing the specific issues (font too small, excessive whitespace, cramped line spacing) that the user cared about.

## The Fix

Prompt with **specific, directive questions** about measurable properties:

```
I need you to do a critical QA assessment of this resume PDF page. Focus only on these specific questions:

1. BODY TEXT SIZE: Is the paragraph text large enough to read comfortably when printed at A4? Compare it visually to the section headings. Is the ratio appropriate?
2. BLANK SPACE: What percentage of the page is empty white space? Is there a large empty area at the bottom?
3. LINE SPACING: Are the bullet points too tight (cramped) or reasonably spaced?
4. SIDEBAR TAGS: Are the skill tags (Python, FastAPI, etc.) readable or too small?
5. OVERALL: Does this look like a professionally formatted printed resume or does the font look too small / spacing off?
Be specific — tell me exactly what's wrong and needs to change.
```

vs what was done before:
```
Rate this resume 1-10 on layout quality, content rendering, page breaks, sidebar formatting.
```

## The Lesson

Generic vision model ratings are unreliable for subjective quality assessment. The model needs:
1. **Specific questions** about measurable visual properties
2. **Reference frames** ("compared to headings", "when printed")
3. **Actionable output** ("tell me what needs to change", not a score)
4. **Multiple specific dimensions** (font size, whitespace %, spacing, readability)

Cross-reference vision results with PyMuPDF measurements (rendered font sizes, page count, line count) before reporting to the user. Present both data sources.

### ALSO from session 2026-06-12: Provider chain knowledge

When `vision_analyze` fails with auth errors, trace the provider resolution chain:

1. Config reads `auxiliary.vision` → if not set, falls to "auto"
2. Auto-detection tries main provider's mapped vision model (`_PROVIDER_VISION_MODELS`)
3. `_resolve_strict_vision_backend` handles: copilot, openrouter, nous, openai-codex
4. If main provider (e.g. opencode-go) isn't a strict backend → falls to OpenRouter
5. OpenRouter reads `OPENROUTER_API_KEY` from env
6. If .env has `***` placeholder values → 401

**Fix paths (preferred - OpenRouter free tier):**
```yaml
auxiliary:
  vision:
    provider: openrouter
    model: nvidia/nemotron-nano-12b-v2-vl:free
    api_key: ${OPENROUTER_API_KEY}
```
Also works: `openrouter/free` as model (auto-routes).

**The `AUXILIARY_VISION_MODEL` env var trap:** the gateway bridges config to this env var at startup. Even if config.yaml changes, the stale env var overrides. Check with `env | grep AUXILIARY_VISION_MODEL`. Fix by updating `.env` with the correct model name (per-turn reload picks it up).

**Don't use data: URLs for large images** (>200KB) — the tool's file path is too long. Save to disk and pass the path.
