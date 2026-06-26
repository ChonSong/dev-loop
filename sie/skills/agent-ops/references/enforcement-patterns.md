# Enforcement Patterns — replacing prose rules with code

## The core insight

SOUL.md, AGENTS.md, and similar files contain rules like:
- "Max 5 tool calls per response"
- "Stop after 2 failed retries"
- "Verify before claiming done"

These are **prose constraints**. The agent reads them. The agent
violates them. The agent is not at fault — the LLM is not a state
machine. Prose rules are suggestions, not enforcement.

The fix: wrap the tools that the rules govern, and have the wrapper
enforce the rule in code. Three patterns, ordered by ROI.

## Pattern 1: State-aware tool wrapper (gated-terminal)

**Use when:** the rule is about HOW MANY times or HOW LONG a tool runs.

**Implementation:**
- Track per-session state in `/tmp/<wrapper>-state/<session_id>.json`
- Increment counters on each call
- Hard-abort (exit 126) when threshold exceeded
- Normalize commands (strip timestamps, UUIDs) so retries don't reset count
- Provide env-var override (`GATED_BUDGET_OVERRIDE=1`) for emergencies

**Thresholds to set:**
- Same-command retries: 5 (matches the SOUL.md rule, which it doesn't)
- Total failures per session: 10 (3x the retry limit)
- Total calls per session: 200 (matches observed worst case: 136)

**Pitfall:** argparse REMAINDER with optional flags. If you declare
`--foo` without `action="store_true"`, argparse will consume the next
positional as `--foo`'s value. Use env vars, not CLI flags, for
wrapper-level overrides. See `argparse-cli-wrapper-pitfall.md`.

## Pattern 2: Pre-commit gate (pre-commit-gate)

**Use when:** the rule is about WHAT lands in a commit.

**Checks (in order):**
1. Syntax validation per-language (Python `ast.parse`, JSON `json.load`,
   JS `node --check`)
2. Secret scan on the diff (NOT on the working tree — false positives
   on `.env` files in dev)
3. Diff size sanity (warn if > 1000 lines)
4. Auto-detected test run (`pytest`, `npm test`, `go test`, etc.)
5. `git diff --check` (whitespace, line endings)

**Critical insight:** secret patterns need to be **specific** to be
useful. Generic "20+ char string after api_key=" gets 80% false
positives. Specific patterns (`AKIA[0-9A-Z]{16}` for AWS,
`ghp_[a-zA-Z0-9]{36}` for GitHub) get <5% false positives and
catch real leaks.

**Install as hook:** `python3 pre-commit-gate.py --install` writes
`.git/hooks/pre-commit`. Use `--diff-only` to skip test execution
(fast pre-commit check; full tests run in CI).

## Pattern 3: Schema-as-validator (validate)

**Use when:** the rule is about TRUSTING data from external sources.

The user proposed "cryptographic proof" and "AST parsing" for
verifiable evidence. Both are wrong for the failure modes I see:

| User's proposal | What actually catches bugs |
|---|---|
| Hash test outputs | Test runner with real assertion parsing (`X passed, Y failed`) |
| Parse AST | Run `git diff --check` + language-specific syntax |
| Cryptographic proof of execution | `git diff` before/after + runnable repro command |
| — | **JSON schema validation on every API response** |

Schema validation catches the bugs that actually recur: `NoneType.get()`
on null API fields, `KeyError` on missing JSON keys, `TypeError` from
non-standard response shapes (e.g., the Cloudflare token endpoint that
returns a string where you'd expect an object).

**Implementation:**
- One schema per external API endpoint
- Schemas in `evidence/schemas/<api>--<endpoint>.json` (Draft-07)
- Test cases that include the EXACT failure modes from prior sessions
- Cross-reference: each schema violation should link to a gotcha
  (e.g., `cloudflare-tunnel-token.json` schema violation → gotcha
  `cf-tunnel-012`)

## When NOT to enforce

- **Single-step tasks**: enforcement overhead > benefit
- **Truly novel problems**: premature enforcement creates false rules
- **Human-in-the-loop workflows**: the human IS the enforcement
- **Sub-2-minute jobs**: overhead dominates

## The cost of NOT enforcing

Evidence from one prior session: 136 terminal calls in a single
debugging session, violating the SOUL.md "5 calls max" rule. The rule
existed for months. The agent had read it many times. It didn't help.

After enforcement: 6 retries of `false` → exit 126 with explicit
reason. The agent reconsiders. The loop breaks.

That's the difference between prose and code.
