---
name: systematic-debugging
description: '4-phase root cause debugging: understand bugs before fixing. Trigger on bug / broken / throwing / failing / not working / error / stack trace / asks to debug/diagnose/investigate. Includes runtime-blocked pivot rule - when a tool (browser, JS runtime, native binary) cannot launch in the current environment after 3 attempts, stop and pivot to static evidence or delegate to a host-capable subagent.'
category: software-development
tags: [debugging, troubleshooting, problem-solving, root-cause, investigation, environment-fallback, pivot]
source: local
is_imported: true
related_skills: [debug-mantra, writing-plans, test-driven-development]
---

# systematic-debugging

4-phase root cause debugging: understand bugs before fixing.

**Category:** software-development
**Source:** local**

## Quick Reference

The iron law: **No fixes without root cause investigation first.** Complete Phase 1 before proposing any fix.

For the full 4-phase process (root cause → pattern → hypothesis → implementation), the Rule of Three, common rationalizations, and case studies, see the obra-imported `software-development/systematic-debugging` skill (rich version).

## Local Addition: The Runtime-Blocked Pivot Rule

When a tool you need to complete Phase 1 (e.g. headless browser, JS runtime, network access, package manager, native binary) is failing in the current environment:

1. **First 1-2 attempts**: legitimate investigation — fix missing libs, env vars, args, version mismatch. Fine.
2. **By attempt 3**: the tool is not going to work here without rebuilding the environment. You are in thrash. **Stop.**
3. **Ask the pivot question**: "Can I gather the same evidence with what DOES work in this environment?" Often yes — `curl` + `read_file` + `search_files` gives 80% of the runtime evidence without a browser.

**Trigger phrases that mean "stop and pivot":**
- 3rd different "missing shared library" error in the same container for the same binary
- Even a `data:text/html,<h1>test</h1>` URL times out in a headless browser
- Adding more `--no-sandbox` / `--disable-gpu` / `--single-process` flags stops changing the failure mode
- You find yourself `apt-get`/`dpkg-deb`-installing system userland to make a third-party binary launch
- The error mode after fix #3 is identical to the error mode before fix #1

**What to do instead:**
- `curl`/`wget` the resource, then `read_file` + `search_files` the inline source for data flows, error paths, undefined references
- Use `delegate_task` with `toolsets=['browser', 'file']` — the subagent may run on a host where the tool works
- If neither is possible: tell the user the runtime evidence is unavailable, summarize what static evidence you CAN provide, and ask whether to proceed blind or wait

**Hard rule:** Do NOT capture environment-dependent failures as durable rules ("Chromium doesn't work in containers", "no node here"). The environment is fixable. The lesson is the *pivot pattern*, not the *negative claim*.

See `references/runtime-blocked-pivot.md` for the full worked example (chrome-in-container trap → 6+ libs downloaded → FATAL fontconfig → even a data URL times out → correct pivot: `curl` + `read_file` + `delegate_task`).
