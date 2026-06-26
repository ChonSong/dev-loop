---
name: open-lovable-site-cloner
description: Self-contained site cloner — URL to full React/Next.js code. Based on firecrawl/open-lovable, refactored to need only 2 env vars (FIRECRAWL_API_KEY + OPENROUTER_API_KEY) with local Vite sandbox.
category: devops
---

# Open Lovable — Self-Contained Site Cloner

A refactored version of [firecrawl/open-lovable](https://github.com/firecrawl/open-lovable) (26.7k★) that clones any website URL into a modern React/Vite application.

**Key difference from upstream:** Only 2 API keys needed instead of 15+. Everything runs locally.

## Architecture

| Component | Upstream | Refactored |
|-----------|----------|------------|
| Sandbox | Vercel/E2B cloud | **Local Vite dev server** on filesystem |
| AI Provider | 4 SDKs (Anthropic, Google, Groq, OpenAI) | **Single OpenRouter** via `@ai-sdk/openai` |
| Scraper | Firecrawl only (paid key required) | **Firecrawl + Puppeteer fallback** (works without key) |
| Morph Fast Apply | Optional via Morph API key | **Removed** (full-file generation only) |

## Setup

```bash
cd /workspace/open-lovable

# Create .env.local with your keys
cat > .env.local << 'EOF'
FIRECRAWL_API_KEY=your_key    # https://firecrawl.dev (optional — Puppeteer fallback works)
OPENROUTER_API_KEY=your_key   # https://openrouter.ai (required)
SANDBOX_PROVIDER=local        # default
EOF

npm run dev
# Open http://localhost:3000
```

## Required Environment Variables

| Variable | Source | Required? |
|----------|--------|-----------|
| `OPENROUTER_API_KEY` | https://openrouter.ai | **Yes** |
| `FIRECRAWL_API_KEY` | https://firecrawl.dev | No — Puppeteer fallback |
| `SANDBOX_PROVIDER` | — | No — defaults to `local` |

## Key Files Modified from Upstream

- `lib/sandbox/providers/local-provider.ts` — New: local filesystem Vite sandbox
- `lib/sandbox/factory.ts` — Default changed to `local` provider
- `lib/ai/provider-manager.ts` — Simplified to single OpenRouter client
- `lib/local-scraper.ts` — New: Puppeteer + Turndown scraper (no API key)
- `app/api/scrape-website/route.ts` — Falls back to local scraper when no Firecrawl key
- `config/app.config.ts` — Updated models, removed cloud sandbox config
- `next.config.ts` — Webpack externals for removed packages

## Available Models (via OpenRouter)

```
anthropic/claude-sonnet-4-20250514  (default)
openai/gpt-4.1
google/gemini-2.5-pro
meta-llama/llama-4-maverick
deepseek/deepseek-r1
```

## Flow

```
URL → Scrape (Firecrawl or Puppeteer) → AI Generate (OpenRouter) → Parse XML → Write Files → Local Vite Preview
```

## Pitfalls

- **OpenRouter keys must have credits**: The `/api/v1/models` endpoint is public and works without credits, but `/api/v1/chat/completions` returns `401 User not found` if the account has no credits or isn't verified. Always test with a real chat call, not just model listing.
- **PATH in background processes**: `npx` may not be found in background terminal. Prepend `export PATH="$HOME/.hermes/home/.local/bin:$PATH"` before any `npx` call. Docker containers often lack PATH entries for user-installed binaries.
- **Puppeteer needs Chrome**: If running in Docker, ensure Chrome/Chromium is installed for the fallback scraper. Without it, the `/api/scrape-website` route will fail when `FIRECRAWL_API_KEY` is unset.
- **First sandbox startup is slow**: npm install for Vite scaffolding takes ~30s on first run. Subsequent runs reuse installed node_modules.
- **No Morph = full file rewrites**: Edits generate complete files instead of surgical patches. Slightly more tokens but same result quality.
- **Login-gated sites can't be scraped**: `app.gtowizard.com` returns a login page via Firecrawl. For such sites, either: (a) feed the AI a text description of the UI instead of a URL, or (b) provide existing source code as context in the `conversationContext` field.
- **Source-as-context beats scraping for existing projects**: When you already have the source code of the app you want to rebuild (e.g., `/workspace/gto-wizard-clone/`), scraping the live site is inferior to feeding the source files directly into the AI prompt via the generate endpoint's context field.
- **Dynamic imports need webpack externals**: After removing `@vercel/sandbox` and `@e2b/code-interpreter` from package.json, their static imports break the build even if wrapped in dynamic `import()`. Must add them to `next.config.ts` webpack externals AND use `// @ts-expect-error` on the dynamic import lines.
- **Morph removal requires cleaning ALL routes**: Just deleting `lib/morph-fast-apply.ts` isn't enough — `apply-ai-code-stream/route.ts` and `generate-ai-code-stream/route.ts` both reference `applyMorphEditToFile`, `parseMorphEdits`, `morphEnabled`, and `morphUpdatedPaths`. Set `morphEnabled = false`, `morphEdits = []`, and delete all `if (morphEnabled)` blocks entirely.
- **read_file output has line-number prefixes**: When reading a file with `read_file` and writing it back with `write_file`, the `N|` prefixes get embedded in the file. Always strip them: `re.sub(r'^\s*\d+\|', '', content, flags=re.MULTILINE)`.

## Usage Patterns

### Pattern 1: URL → Clone (scraping-based)
Best for cloning external sites you don't have source code for.
```
Open http://localhost:3000 → paste URL → select model → "Build"
```

### Pattern 2: Description → Generate (prompt-based)
Best when you can describe the UI or have existing source code.
```
# Via the API:
curl -X POST http://localhost:3000/api/generate-ai-code-stream \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Build a poker equity calculator with...","model":"anthropic/claude-sonnet-4-20250514","context":{"sandboxId":"...","currentFiles":[],"conversationContext":{"scrapedWebsites":[]}},"isEdit":false}'
```

### Pattern 3: Existing Source → Redesign
When you have source code, include it in the prompt. Don't waste tokens scraping — the AI generates better code from reading real source than from a scraped markdown summary.

## References

- `references/refactoring-changelog.md` — Detailed file-by-file refactoring log from upstream
- `references/build-fixes.md` — Specific fixes needed after the initial refactoring to get `next build` passing

## Related Skills

- **cloud-to-local-refactor** — The general pattern this refactoring follows. Load it for other cloud-to-local migrations.
