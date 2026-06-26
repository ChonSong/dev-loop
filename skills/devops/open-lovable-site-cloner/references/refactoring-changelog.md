# Open Lovable Refactoring Log

Concretely what was changed from `firecrawl/open-lovable` upstream to the self-contained version at `/workspace/open-lovable`.

## Files Created
| File | Purpose |
|------|---------|
| `lib/sandbox/providers/local-provider.ts` | Full `SandboxProvider` implementation: `fs` for file ops, `child_process` for commands, spawns Vite dev server. Uses `os.tmpdir()` + `crypto.randomUUID()` for sandbox dirs. Terminatable with cleanup. |
| `lib/local-scraper.ts` | Puppeteer + Turndown scraper: headless Chrome, HTML→Markdown, main content extraction, screenshot as base64, link extraction. Exported for fallback use. |
| `app/api/scrape-website-local/route.ts` | Next.js route wrapping `scrapeWithPuppeteer` as a POST endpoint. |

## Files Modified
| File | Change |
|------|--------|
| `lib/ai/provider-manager.ts` | Complete rewrite: removed 4 SDK imports, single `createOpenAI` pointing to OpenRouter. ~20 lines down from 120. |
| `lib/sandbox/factory.ts` | Default `'e2b'` → `'local'`. Added `LocalProvider` import and factory case. `isProviderAvailable('local')` always true. |
| `lib/sandbox/sandbox-manager.ts` | Added `LocalProvider` handling in `getOrCreateProvider` (no reconnect needed). |
| `lib/sandbox/types.ts` | `'e2b' \| 'vercel'` → `'e2b' \| 'vercel' \| 'local'` in `SandboxInfo.provider`. |
| `lib/sandbox/providers/vercel-provider.ts` | Static import → dynamic `import()` with `@ts-expect-error`. `Sandbox.create()` → `(await getSandbox()).create()`. |
| `lib/sandbox/providers/e2b-provider.ts` | Same lazy-load pattern. All `appConfig.e2b.*` references inlined with literal values. |
| `app/api/create-ai-sandbox/route.ts` | Rewrote from Vercel-specific to factory pattern (delegates to `SandboxFactory.create()`). |
| `app/api/generate-ai-code-stream/route.ts` | Removed Morph prompt blocks. Replaced multi-provider routing with single `openrouter` client. Fixed truncation recovery to use `openrouter`. |
| `app/api/apply-ai-code-stream/route.ts` | Removed Morph import/apply logic. Stripped all `morphEnabled`/`morphEdits`/`morphUpdatedPaths` dead code. |
| `app/api/analyze-edit-intent/route.ts` | Replaced 4 SDK imports with single OpenRouter client. |
| `app/api/scrape-website/route.ts` | Added fallback: if no `FIRECRAWL_API_KEY`, delegates to `scrapeWithPuppeteer` from `@/lib/local-scraper`. |
| `config/app.config.ts` | Removed `vercelSandbox` + `e2b` sections. Added `localSandbox`. Updated models to OpenRouter IDs. Removed `modelApiConfig`. |
| `next.config.ts` | Added webpack `externals` and `resolve.fallback` for `@e2b/code-interpreter` and `@vercel/sandbox`. |
| `.env.example` | Replaced 15+ vars with 2: `FIRECRAWL_API_KEY` + `OPENROUTER_API_KEY`. |

## Files Deleted
| File | Reason |
|------|--------|
| `lib/morph-fast-apply.ts` | Morph Fast Apply removed — optional paid feature |

## Packages Removed
`@ai-sdk/groq`, `@ai-sdk/anthropic`, `@ai-sdk/google`, `@anthropic-ai/sdk`, `groq-sdk`, `@vercel/sandbox`, `@e2b/code-interpreter`

## Packages Added
`puppeteer` (^23.0.0), `turndown` (^7.2.0), `@types/turndown` (^5.0.4)

## Debugging Issues Hit
1. **read_file → write_file corruption**: Line-number prefixes from `read_file` output baked into file when passed to `write_file`. Fixed with `re.sub(r'^\s*\d+\|', '', content, flags=re.MULTILINE)`.
2. **Webpack can't resolve dynamic imports**: Even lazy `await import('@pkg')` traced at build time. Fixed with webpack externals/fallback in `next.config.ts`.
3. **Next.js route export restriction**: `export { scrapeWithPuppeteer }` from route.ts caused build failure. Fixed by moving function to `lib/local-scraper.ts`.
4. **Dangling braces after Morph removal**: Surgical line removal left stray `}` causing syntax errors. Fixed by deleting complete blocks.
5. **applyMorphEditToFile still referenced**: Dead code path still imported the deleted module. Bulk-removed all morph variables and blocks.
