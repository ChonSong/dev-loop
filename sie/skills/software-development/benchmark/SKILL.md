---
name: benchmark
description: Measure performance baselines, detect regressions before/after changes, and compare alternatives. For LLM APIs, web pages, and code execution.
origin: ECC (adapted for Hermes)
---

# Benchmark — Performance Baseline & Regression Detection

Measure and track performance across projects.

## When to Activate

- Before and after a PR to measure performance impact
- Setting up performance baselines for a project
- Users report "it feels slow"
- Before a launch — ensure performance targets met
- Comparing stack alternatives (e.g., Vite vs Turbopack)

## Web Performance (agent-os, hermes-web-computer)

### Lighthouse CLI in Headless Docker Containers

**PITFALL**: Lighthouse CLI frequently crashes in headless Docker environments with `PROTOCOL_TIMEOUT`, `NO_FCP`, or `Connection closed` errors. This happens because:
- The headless Chrome process is unstable inside containers
- Full-page screenshot gathering hangs on SPA apps
- Tracing API timeouts on single-page apps with WebSocket connections

**Working Alternative: Puppeteer Direct Metrics**

When Lighthouse CLI fails, use Puppeteer directly:

```javascript
const puppeteer = require('puppeteer');
const page = await browser.newPage();
await page.goto('http://localhost:3005', { waitUntil: 'networkidle0' });

// Core Web Vitals
const fcp = await page.evaluate(() => {
  const entries = performance.getEntriesByType('paint');
  return entries.find(e => e.name === 'first-contentful-paint')?.startTime;
});

const lcp = await page.evaluate(async () => {
  return new Promise(resolve => {
    new PerformanceObserver(list => {
      const entries = list.getEntries();
      resolve(entries[entries.length - 1].startTime);
    }).observe({ type: 'largest-contentful-paint', buffered: true });
    setTimeout(() => resolve(null), 2000);
  });
});

const cls = await page.evaluate(async () => {
  let clsValue = 0;
  new PerformanceObserver(list => {
    for (const entry of list.getEntries()) {
      if (!entry.hadRecentInput) clsValue += entry.value;
    }
  }).observe({ type: 'layout-shift', buffered: true });
  setTimeout(() => clsValue, 2000);
});
```

**Chrome Launch Flags for Docker:**
```javascript
puppeteer.launch({
  headless: 'new',
  args: ['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage']
});
```

**Scoring Guidelines (when Lighthouse isn't available):**
| Metric | Good (90+) | Average (50-89) | Poor (<50) |
|--------|------------|-----------------|------------|
| FCP | < 1000ms | 1000-2500ms | > 2500ms |
| LCP | < 2500ms | 2500-4000ms | > 4000ms |
| CLS | < 0.1 | 0.1-0.25 | > 0.25 |
| Load Time | < 2000ms | 2000-5000ms | > 5000ms |

### Lighthouse CI

```bash
# Install
npm install -D @lhci/cli

# Configure (.lighthouserc.json)
{
  "ci": {
    "collect": {
      "url": ["http://localhost:3000"],
      "numberOfRuns": 3
    },
    "assert": {
      "assertions": {
        "categories:performance": ["error", {"minScore": 0.9}],
        "categories:accessibility": ["error", {"minScore": 0.95}]
      }
    }
  }
}

# Run
npx lhci autorun
```

### Key Metrics

| Metric | Target | What It Measures |
|--------|--------|------------------|
| LCP | < 2.5s | Largest Contentful Paint |
| FID | < 100ms | First Input Delay |
| CLS | < 0.1 | Cumulative Layout Shift |
| TTFB | < 800ms | Time to First Byte |
| TTI | < 3.8s | Time to Interactive |

### Browser Tools for Benchmarking

```python
# Using browser tools to measure performance
1. browser_navigate(url)
2. browser_console(expression="performance.getEntriesByType('navigation')[0]")
3. Extract: domContentLoaded, load, firstContentfulPaint
4. Compare against baseline
```

## API Performance (hermes-web-computer Go backend)

### Load Testing with `hey`

```bash
# Install
go install github.com/rakyll/hey@latest

# Benchmark
hey -n 1000 -c 10 http://localhost:8080/api/health
hey -n 1000 -c 50 -m POST -H "Content-Type: application/json" \
  -d '{"query":"test"}' http://localhost:8080/api/query
```

### Metrics to Track

- **P50 latency** — median response time
- **P95 latency** — 95th percentile (tail latency)
- **P99 latency** — 99th percentile (worst case)
- **Throughput** — requests per second
- **Error rate** — % of failed requests

## LLM API Cost/Speed Benchmark

```python
# Compare providers for same task
providers = [
    {"name": "MiniMax-M2.7", "cost_per_1m": 0.10},
    {"name": "Qwen3.6-plus", "cost_per_1m": 0.50},
    {"name": "Claude Sonnet", "cost_per_1m": 3.00},
]

# Measure: latency, quality, cost
# Track in /opt/data/benchmarks/llm-comparison.json
```

## Baseline Management

Store baselines in project's `docs/benchmarks/`:

```json
{
  "project": "agent-os",
  "date": "2026-05-11",
  "metrics": {
    "lcp_ms": 1200,
    "cls": 0.05,
    "build_time_s": 12,
    "bundle_size_kb": 245
  },
  "commit": "abc123"
}
```

## Regression Detection

```bash
# Compare current vs baseline
current_lcp=1500
baseline_lcp=1200
regression=$(( (current_lcp - baseline_lcp) * 100 / baseline_lcp ))

if [ $regression -gt 20 ]; then
    echo "WARNING: LCP regressed by ${regression}%"
fi
```

## CI Integration

```yaml
# .github/workflows/benchmark.yml
name: Benchmark
on: [pull_request]
jobs:
  perf:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm run build
      - name: Lighthouse
        uses: treosh/lighthouse-ci-action@v11
        with:
          urls: |
            http://localhost:3000
          budgetPath: ./lighthouse-budget.json
```
