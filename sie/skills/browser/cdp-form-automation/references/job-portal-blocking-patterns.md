# Job Portal Blocking Patterns (empirical, June 2026)

## Accessibility from Container IP

| Portal | Status | Reason |
|--------|--------|--------|
| **SEEK.com.au** | ✅ via Tandem, ❌ direct | Cloudflare — container IP blocked |
| **LinkedIn** | ❌ | Sign-in wall — cannot browse without account session |
| **amazon.jobs** | ❌ | Cloudflare + account creation required per application |
| **Workday** (WEHI, etc.) | ❌ employee-only post-login | Requires org account to view listings |
| **Elmo** (NGS Super) | ✅ worked | Custom portal, no Cloudflare |
| **harrison.ai** | ❌ | Cloudflare from container IP |

## Required Approach by Portal Type

1. **SEEK Quick Apply** → Tandem Electron app (residential IP + user's authenticated session). Use `start-tandem.sh` + curl commands against localhost:3099.
2. **Company career portals** → Requires user to apply directly in their browser. Agent should find the URL + role details and hand off to the user.
3. **Direct email** → Always viable if contact info available. Send via Gmail API.

## Why Tandem Works

The Tandem Electron app runs on the user's desktop with their residential IP and browser fingerprint. Cloudflare sees a normal user session, not a container. The agent connects to it via CDP on port 9222 (proxied through electron-viewer at :3099).

## What to Try First When Job Hunting

1. Check if user has Tandem running (`curl -s http://127.0.0.1:3099/info`)
2. If not, run `bash /home/sc/.hermes/scripts/start-tandem.sh`
3. Tell user "Tandem launched — log into SEEK in the window that appeared"
4. Once logged in, search/applies go through localhost:3099 API
