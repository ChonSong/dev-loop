# Codebase Readiness Assessment — Checklist & Worked Example

## Checklist Template

### Phase 1: High-Level Survey
```
[ ] README read — understand what the app does
[ ] package.json / pyproject.toml / Cargo.toml checked — language, framework, build system
[ ] SPEC.md / ARCHITECTURE.md / DEVELOPMENT_PLAN.md located
[ ] Build scripts inventoried (dev, build, test, lint)
[ ] Docker / Compose / deploy config found
```

### Phase 2: Environment Inventory
```
[ ] Runtime versions: node __, python __, go __, rustc __
[ ] Package managers: npm __, pnpm __, pip __, cargo __
[ ] Infrastructure: docker __, cloudflared __, systemctl __
[ ] Resource limits: CPUs __, RAM __, disk free __
[ ] SSH access to host: yes/no
```

### Phase 3: Dependency Audit
```
[ ] `npm ci` / `pnpm install` / `pip install` succeeds
[ ] No UNMET DEPENDENCY in `npm ls --depth=0`
[ ] `.env.example` present, all vars documented
[ ] No suppressed build flags: ignoreBuildErrors, skipLibCheck, strict: false
[ ] Python version requirement vs available (e.g. 3.11+ needed, 3.8 available)
```

### Phase 4: Build Verification
```
[ ] `npm run build` (or equivalent) succeeds
[ ] TypeScript errors not silently suppressed
[ ] Docker image builds (if Docker deploy)
```

### Phase 5: Infrastructure Scan
```
[ ] Ports listening: __
[ ] Tunnel active? cloudflared tunnel list shows connections
[ ] Tunnel ingress routes match running services
[ ] Systemd services active for auto-restart
[ ] Stale tunnels from past experiments identified
```

### Phase 6: Test Health
```
[ ] Test suite runs (unit + E2E)
[ ] All tests pass
[ ] Visual regression configured? (toHaveScreenshot, pixelmatch, etc.)
[ ] Test results directory checked for old failures
[ ] E2E config checked for base URL correctness
```

### Phase 7: Process DNA
```
[ ] SPEC-driven development? (architecture doc before coding)
[ ] Phase-based delivery? (tracked phases with scope)
[ ] External library integration pattern? (adapt not rewrite)
[ ] QA depth: unit | integration | E2E | visual regression
[ ] Deploy pattern: Docker Compose | systemd | manual | helm
```

---

## Worked Example: GTO Wizard Clone

Findings from the actual assessment (2026-06-13):

### Phase 1 Result
- Next.js 15 + React 19 + FastAPI monorepo
- Comprehensive SPEC.md and DEVELOPMENT_PLAN.md
- 6 phases, all marked complete
- Docker Compose with 5 services (web, api, solver, worker, redis, postgres)

### Phase 2 Result
- Node v22.22.3 ✅
- Python 3.8.10 ❌ (needs 3.11+ for solver/API)
- No Go, no Rust, no pnpm
- 2 CPUs, 8GB RAM, 81GB free
- Docker available, cloudflared installed, no systemd

### Phase 3 Result
- All npm packages: UNMET DEPENDENCY ❌ (never installed)
- `typescript.ignoreBuildErrors: true` in next.config.ts ❌
- `.env.example` present with all vars

### Phase 4 Result
- Build not attempted (deps not installed)
- Suppressed TS errors are a known risk

### Phase 5 Result
- Only Hermes agent (8642) and cloudflared mgmt (20241) listening
- Tunnel "codeovertcp" 17 ingress rules but ZERO connections ❌
- Multiple stale tunnels from experiments
- No systemd services

### Phase 6 Result
- 7 Playwright E2E spec files with Page Object Model
- Tests failing with "Cannot navigate to invalid URL" ❌
- No visual regression setup
- Test results directory shows unfixed failures

### Phase 7 Process DNA
- **SPEC-driven**: Yes — comprehensive SPEC.md guided all phases
- **Phase-based**: Yes — 6 tracked phases with files/tests/endpoints per phase
- **External libs**: Yes — OMPEval (C++), PokerHandEvaluator adapted into Python
- **QA depth**: Unit (Python) + E2E (Playwright) — no visual regression
- **Deploy pattern**: Docker Compose — `docker compose up` one-command

### Priority Synthesis

**Blockers:**
1. Dependencies not installed — can't build or run
2. Cloudflare tunnel has zero connections — no external access
3. No services running on any ingress port

**High Priority:**
1. Fix E2E test base URL config
2. Install Python 3.11+ for solver backend
3. Fix suppressed TypeScript errors

**Low Priority (debt):**
1. Add visual regression tests
2. Prune stale tunnels
3. Set up systemd services for auto-restart
