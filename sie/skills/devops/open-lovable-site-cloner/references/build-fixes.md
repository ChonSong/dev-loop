# Build Fixes After Refactoring open-lovable

These are the specific issues that arose when making `next build` pass after stripping cloud dependencies from the upstream firecrawl/open-lovable repo.

## 1. Dynamic Imports for Removed Packages

When `@vercel/sandbox` and `@e2b/code-interpreter` are removed from `package.json`, their static imports break the build even if converted to dynamic `import()`.

**Fix in `next.config.ts`:**
```ts
webpack: (config, { isServer }) => {
  config.resolve.fallback = {
    ...config.resolve.fallback,
    '@e2b/code-interpreter': false,
    '@vercel/sandbox': false,
  };
  if (isServer) {
    config.externals = config.externals || [];
    if (Array.isArray(config.externals)) {
      config.externals.push('@e2b/code-interpreter', '@vercel/sandbox');
    }
  }
  return config;
},
```

**Fix in provider files** — replace static import with lazy getter:
```ts
// vercel-provider.ts and e2b-provider.ts
let Sandbox: any;
async function getSandbox() {
  if (!Sandbox) {
    try {
      // @ts-expect-error — dynamic import, package may not be installed
      const mod = await import('@vercel/sandbox');
      Sandbox = mod.Sandbox;
    } catch {
      throw new Error('Package not installed. Use SANDBOX_PROVIDER=local');
    }
  }
  return Sandbox;
}
```

Then replace `Sandbox.create(...)` with `(await getSandbox()).create(...)`.

## 2. Morph Removal — Clean ALL References

Deleting `lib/morph-fast-apply.ts` alone isn't enough. Three files reference it:

- `app/api/apply-ai-code-stream/route.ts` — imports `parseMorphEdits`, `applyMorphEditToFile`; has `morphEnabled` / `morphEdits` / `morphUpdatedPaths` runtime variables and large `if (morphEnabled)` blocks
- `app/api/generate-ai-code-stream/route.ts` — has `morphFastApplyEnabled` boolean, adds Morph-specific prompt sections

**Fix:** Set `morphEnabled = false`, `morphEdits: any[] = []`, and delete entire `if (morphEnabled)` / `if (morphFastApplyEnabled)` blocks. Remove the import line. Remove `morphUpdatedPaths` set and the filter that uses it.

## 3. AI Provider Consolidation to OpenRouter

The generate-ai-code-stream route has provider selection logic scattered across 100+ lines (truncation recovery, fallback, error messages). Key replacements:

- `const modelProvider = isAnthropic ? anthropic : ...` → `const modelProvider = openrouter;`
- `const actualModel = model.replace('anthropic/', '')` → `const actualModel = model;` (OpenRouter handles routing)
- `completionClient = anthropic` → `completionClient = openrouter`
- `completionModelName = model.replace('openai/', '')` → `completionModelName = model`

Also remove: `isAnthropic`, `isGoogle`, `isOpenAI`, `isKimiGroq`, `isUsingAIGateway` variables and all branching on them.

## 4. Config References After Removing `appConfig.e2b` / `appConfig.vercelSandbox`

The E2B provider referenced `appConfig.e2b.timeoutMs`, `appConfig.e2b.vitePort`, `appConfig.e2b.viteStartupDelay`. Replace with hardcoded values:

| Old | New |
|-----|-----|
| `appConfig.e2b.timeoutMs` | `1800000` |
| `appConfig.e2b.vitePort` | `5173` |
| `appConfig.e2b.viteStartupDelay` | `10000` |
| `appConfig.packages.useLegacyPeerDeps` | `true` |
| `appConfig.packages.autoRestartVite` | `true` |

Then remove the `import { appConfig }` line from the E2B provider.

## 5. Scraping Fallback — Extract to lib, Not Route

Next.js route files can only export HTTP method handlers (`GET`, `POST`, etc). Exporting `scrapeWithPuppeteer` from a route file causes:

```
Type error: Route does not match the required types of a Next.js Route.
"scrapeWithPuppeteer" is not a valid Route export field.
```

**Fix:** Move `scrapeWithPuppeteer` to `lib/local-scraper.ts`, import it from there in both the route and the Firecrawl fallback route.

## 6. `read_file` Line-Number Prefixes

When reading a file via `read_file()` and writing it back via `write_file()`, the `N|` line-number prefixes from read_file output get embedded in the file. Always strip:

```python
import re
content = re.sub(r'^\s*\d+\|', '', content, flags=re.MULTILINE)
```

Or better: use `patch()` instead of read-then-write for targeted edits.
