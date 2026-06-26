---
name: cloud-to-local-refactor
description: Refactor cloud-dependent AI apps to run fully local — replace cloud sandboxes, consolidate AI SDKs, add free fallbacks, eliminate API key sprawl.
tags: [refactor, self-hosted, sandbox, openrouter, local-provider]
---

# Cloud-to-Local Refactor

Pattern for taking apps that depend on multiple cloud services (sandboxes, AI providers, scraping APIs) and making them self-contained with minimal external dependencies.

## Trigger

- App requires 5+ API keys / cloud service credentials
- Cloud sandbox (Vercel, E2B, Modal) used for code that could run locally
- Multiple AI SDK imports when a single proxy (OpenRouter) would suffice
- User wants "self-contained" or "minimal deps" version of an existing tool

## Refactoring Sequence

1. **Architecture audit** — Map every external dependency: what it does, what env vars it needs, whether it can be replaced locally. Output a table: `| Dependency | Purpose | Env Vars | Can Replace? |`

2. **Sandbox → LocalProvider** (if cloud sandbox exists)
   - Look for abstract `SandboxProvider` class or factory pattern
   - Implement `LocalProvider` using Node.js built-ins: `fs` for file ops, `child_process` for commands, spawn Vite/Next.js dev server locally
   - Update factory default from cloud provider to `'local'`
   - Local sandbox URL = `http://localhost:{port}` (no HMR override, no wss protocol)
   - Kill Vercel-specific config: `clientPort:443`, `protocol:'wss'`, `.vercel.run` allowedHosts

3. **Multiple AI SDKs → Single OpenRouter**
   - Replace `@ai-sdk/groq`, `@ai-sdk/anthropic`, `@ai-sdk/google` with a single `@ai-sdk/openai` pointing to `https://openrouter.ai/api/v1`
   - OpenRouter model IDs ARE the full prefixed IDs: `anthropic/claude-sonnet-4-20250514`, `google/gemini-2.5-pro`
   - Strip prefix-stripping logic from `getProviderForModel` — just pass modelId as-is
   - Remove AI Gateway / proxy logic — OpenRouter replaces it
   - **Pitfall**: Route files often duplicate the provider setup from provider-manager.ts. Search ALL route files for direct SDK imports.

4. **Remove optional paid features** (Morph, etc.)
   - Check for `process.env.OPTIONAL_API_KEY` gating — these are conditional and can be hard-disabled
   - Delete the lib file, then clean route files: remove imports, replace `if (enabled) {...}` blocks, remove from prompt construction
   - **Pitfall**: Large route files (900+ lines) time out subagents. Use `grep -n` + targeted `patch` instead.

5. **Add free fallback** (for scraping, etc.)
   - Firecrawl → Puppeteer + Turndown for HTML→Markdown
   - Pattern: scrape route checks for API key, delegates to local scraper if missing
   - Export the local scraper function for reuse as fallback

6. **Lazy-load optional providers**
   - Cloud provider files that import removed packages cause build failures
   - Replace static `import { X } from '@pkg'` with dynamic `import()` inside an async getter
   - Getter throws helpful error: `"Package not installed. Install it or use SANDBOX_PROVIDER=local"`

7. **Config cleanup**
   - Replace cloud-specific config sections with local equivalents
   - Update model list to OpenRouter-compatible IDs
   - Prune `modelApiConfig` for provider-specific routing

8. **Verify build**
   - Add `skipLibCheck: true` to tsconfig.json (Next.js projects have messy node_modules types)
   - Run `npm run build` — expect only import-resolution errors for lazily-loaded packages
   - Test `npm run dev` — should start with zero cloud credentials

## Key Pitfalls

- **read_file → write_file line-number corruption**: `read_file` returns `N|content` prefixed lines. If you pass that output directly to `write_file`, the prefixes get baked into the file. Always strip with `re.sub(r'^\\s*\\d+\\|', '', content, flags=re.MULTILINE)` or use the raw terminal `python3 -c` approach.
- **Subagent stale-write conflicts**: When a timed-out subagent partially modified files, subsequent parent writes may conflict. Always `read_file` immediately before `write_file`/`patch` to get fresh content. The tool warns you when this happens — heed it.
- **Webpack resolution of dynamic imports**: Even `await import('@pkg')` is traced by webpack at build time. Must add the packages to `next.config.ts` webpack `externals` (for server) and `resolve.fallback` (for client) to prevent "Module not found" build failures. Pattern: `config.externals.push('@pkg'); config.resolve.fallback = { ...config.resolve.fallback, '@pkg': false };`
- **Subagent timeouts on large files**: Route files >800 lines cause subagent timeouts when reading the full file. Use `grep -n` to find target lines, then `read_file` with offset/limit to patch surgically.
- **Dangling braces after patch**: When removing an `if (condition) { ... }` block, the closing `}` may be left behind if it's outside the matched old_string. Always include the complete block boundary.
- **`tsconfig.json` strict mode**: Next.js projects default to strict TS but have tons of type errors in node_modules. `skipLibCheck: true` is essential for building refactored forks.
- **`@ts-expect-error` for dynamic imports**: TypeScript still validates the module specifier in `await import('@pkg')` even when the package is removed. Add `// @ts-expect-error — dynamic import, package may not be installed` above the import line.
- **`appConfig.*.*` references after config removal**: When removing cloud config sections (e.g., `appConfig.e2b`), search ALL provider files for `appConfig.*.` references and inline the values. Simple grep: `grep -rn "appConfig\\.e2b\|appConfig\\.vercelSandbox" --include="*.ts"`.
- **Next.js API route export rules**: `export` from a `route.ts` file is restricted to HTTP handlers (`GET`, `POST`, etc). Exporting utility functions from route files causes "is not a valid Route export field" build failure. Move shared functions to `lib/` instead.
- **OpenRouter key activation trap**: The `/api/v1/models` endpoint is public (no auth needed) — it returns a full model list even for unactivated keys. Only `/api/v1/chat/completions` reveals the real auth status. Unverified or creditless accounts return `401 User not found` on chat calls. **Always test with a real completion call, not model listing.** This caused a false-positive "keys work" in our session — model listing succeeded but all chat calls failed.

## Worked Examples

- **open-lovable-site-cloner** — Full refactor of firecrawl/open-lovable: 4 AI SDKs → 1 OpenRouter, Vercel/E2B sandbox → LocalProvider, Firecrawl-only → Firecrawl+Puppeteer fallback, Morph removed. 15+ env vars → 2. See skill for setup; see its `references/refactoring-changelog.md` for the file-by-file log.

## ML Model Feasibility

When the question is "can I run this ML model locally?" (not refactor an app), follow the diagnostic sequence in `references/ml-model-feasibility.md`. Key pattern: check GPU → check VRAM vs model requirements → check RAM → offer CPU fallback or cloud API if mismatch.

## Domain Knowledge: 3D Reconstruction from 2D Images

For "how do I create 3D models from 2D images?" questions, see `references/3d-reconstruction-from-2d.md` for the full technology landscape. TL;DR: LRM-based feed-forward transformers (TripoSR, SPAR3D) are state of the art. All need CUDA GPU. CPU fallback: DPT depth estimation → point cloud → Delaunay mesh.

### Ready-to-Use Scripts

Two reference implementations are included in this skill:

- **`scripts/image_to_3d_v2.py`** — Neural depth (DPT-Hybrid-MiDaS, ~345MB download). Best quality for CPU. 30-120s inference.
  ```bash
  /app/venv/bin/pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
  /app/venv/bin/pip install transformers Pillow numpy scipy trimesh
  /app/venv/bin/python3 scripts/image_to_3d_v2.py image.png --output output.glb
  ```

- **`scripts/image_to_3d_classical.py`** — Classical depth heuristics. No downloads, ~1s runtime. Lower quality.
  ```bash
  pip install numpy scipy Pillow trimesh
  python3 scripts/image_to_3d_classical.py image.png --output output.glb
  ```

### Headless Docker Pitfall: Open3D

Open3D requires X11/GL shared libraries and **fails in headless Docker containers**:
`OSError: libX11.so.6: cannot open shared object file`

**Workaround**: Use `trimesh` + `scipy.spatial.Delaunay` for mesh operations. Both are pure Python and work in any container. The scripts above use this approach.

### CPU PyTorch Installation Notes

- Always use `/app/venv/bin/pip` explicitly in the Hermes WebUI container — bare `pip` may target the wrong Python
- `torchvision` must be installed **separately** from `torch` — transformers depth pipelines fail without it
- Use `--index-url https://download.pytorch.org/whl/cpu` to avoid downloading 2GB CUDA runtime
- HuggingFace model downloads may be rate-limited without auth token; first download can take several minutes

## Skill Name Collisions

Several skill names collide between `/skills/` top-level and subdirectories. Always use the categorized path to disambiguate:
- `hermes-agent` — `autonomous-ai-agents/hermes-agent` vs top-level
- `hermes-docker-workflow` — `hermes/hermes-docker-workflow` vs top-level
- `teac-assignment-writing` — `productivity/teac-assignment-writing` vs top-level
- `poker-platform-stack` — `devops/poker-platform-stack` vs `devops/repo-init/references/poker-platform-stack.md`

## Ideal End State

- **2 env vars maximum**: one for the core API (OpenRouter), one optional for best-quality scraping (Firecrawl)
- **All execution local**: No cloud sandbox, no AI gateway, no optional paid features
- **Free fallbacks work**: App degrades gracefully without paid API keys
- **Build succeeds** with `skipLibCheck: true` and lazy-loaded optional deps
