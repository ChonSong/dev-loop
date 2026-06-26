# Site Cloner & UI-to-Code Tool Landscape

Research from 2026-06-06 comparing URL-to-code and screenshot-to-code tools.

## Tier 1: Full Site Cloners (URL → React Project)

| Tool | ★ Stars | Approach | Output | License | Key Trait |
|------|---------|----------|--------|---------|-----------|
| **firecrawl/open-lovable** | 26.7k | Firecrawl scrape → LLM code gen | Full Vite/React project | MIT | Best for full-site cloning; Firecrawl handles JS rendering, anti-bot, clean Markdown |
| **dyad-sh/dyad** | 20.5k | Local AI app builder | Next.js project | Custom | v0/Lovable/Bolt alternative; many LLM providers; local-first |
| **nextify-limited/libra** | 1.6k | v0/Lovable alternative on CF Workers | Next.js | AGPL-3.0 | Cloudflare-native; smallest of the three |

## Tier 2: Component & Interface Generators (Description/Screenshot → Code)

| Tool | ★ Stars | Approach | Output | License | Key Trait |
|------|---------|----------|--------|---------|-----------|
| **wandb/openui** | 22.4k | Text/screenshot → live rendered UI | HTML/CSS/React/Svelte | Apache-2.0 | From Weights & Biases; supports multiple frameworks |
| **thesysdev/openui** | 6.7k | Generative UI standard | Component code | MIT | Agent-focused; open standard for generative UI |

## Tier 3: Niche/Experimental

| Tool | ★ Stars | Notes |
|------|---------|-------|
| **Omerfaruk-aydn/sitecloner** | 1 | Pixel-perfect cloning with animations, videos, fonts |
| **willblack2006/clonify-sites** | 2 | Screenshot → Claude Code → Shopify storefront |

## Decision Matrix

| Need | Best Tool |
|------|-----------|
| Full website URL → runnable React project | **open-lovable** |
| Text/screenshot → single component | **wandb/openui** |
| Local AI app builder (general purpose) | **dyad** |
| Cloudflare-native, no server | **libra** |
| Agent-driven generative UI | **thesysdev/openui** |

## Login-Gated Sites

Most site cloners fail on auth-walled apps (app.gtowizard.com returns login page). Strategies:
1. **Describe the UI via text** — most effective when you know the app well
2. **Feed existing source code** as context — best when you have the codebase already
3. **Screenshot-based** — wandb/openui can work from screenshots if you can capture them manually
4. **Browser automation** — Puppeteer with stored cookies could get past login, but fragile
