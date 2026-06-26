---
name: infrastructure-as-code
description: Provision with Terraform for Cloudflare and AWS.
category: devops
tags: ["terraform", "cloudflare", "iac", "infrastructure", "dns", "vpn", "tunnel"]
---

# infrastructure-as-code

Provision with Terraform for Cloudflare and AWS.

**Category:** devops  
**Source:** local  

## Cloudflare Quick Tunnel (no API token)

See `references/quick-tunnel-ad-hoc.md` for the no-auth quick tunnel pattern: downloading cloudflared binary, `--url http://localhost:PORT` syntax, handling stale named tunnel credentials, and the `--config` global vs subcommand flag placement.
