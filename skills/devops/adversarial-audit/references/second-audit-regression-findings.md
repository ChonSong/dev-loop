# Second Audit Findings — Regression Pattern (2026-06-11)

## What Happened

The second adversarial commitment audit ran on 2026-06-11 (cron job ID `35dfd98f75e8`).
It checked 3 commitments (C-20260708-001, C-20260708-002, C-20260708-003) against
recent session transcripts.

**Results**: 4 violations found — worse than the first audit (3 violations).

## Key Findings

### 1. Zero Skill Loading in Post-Commitments Sessions

The two major webui sessions after the commitments were created (June 8) show
**zero skill_view calls**:

| Session | Messages | Source | Period | skill_view calls |
|---------|----------|--------|--------|-----------------|
| `b6f93d16a3cc` | 422 | webui | June 9–11 (entirely post-commitments) | 0 |
| `f9aeb0432ed8` | 689 | webui | June 7–11 (partially post-commitments) | 0 (post-commitment portion) |

The Discord fix session (`b6f93d16a3cc`, 422 msgs) is the most egregious — it
is entirely post-commitments, involves complex multi-turn debugging, and shows
no compliance at all.

### 2. Cron Agents Also Skip Skill Loading

The auto-continue maintenance cron jobs (`cron_1a8cbe1ed293_20260611_*` series)
have explicit Rule 3 in their prompt: "Always load relevant skill before starting
work (`skills_list()` → `skill_view()`)."

**None of them do it.** Every cron session jumps straight into `read_file`,
`terminal`, and `write_file` operations without ever calling `skills_list` or
`skill_view`. This is a systematic pattern, not an OWL-specific issue.

### 3. The Infrastructure-vs-Behavior Gap

OWL built the commitment infrastructure (commitments.md, auditor cron, AGENTS.md
rules) but did not change its actual working behavior. The two major working
sessions since June 8 show the exact same pattern that the commitments were
designed to fix:

- Jump straight into terminal/file operations
- Never scan or load relevant skills
- Never capture learnings
- End session without any learning artifact

This suggests that **prompt-based commitments alone are insufficient** to change
agent behavior. Structural enforcement (pre-tool-call hooks, system prompt
modification, runtime gating) may be necessary.

### 4. AGENTS.md Rules Being Ignored

The AGENTS.md file was updated on June 8 with mandatory pre-task skill scan
rules and commitment logging rules. Sessions since then show zero compliance
with these rules.

**Hypothesis**: AGENTS.md is not being read by the agent during session startup,
or the agent treats it as optional guidance rather than mandatory rules.

### 5. session_search Cannot Find Negative Evidence

A fundamental limitation: FTS5 searches for `skill_view` only returns sessions
where skill_view was called. To find sessions where skill_view was NOT called,
you must:
1. Browse recent sessions via `session_search()`
2. Search each with `session_search(query="skill_view", session_id="...")`
3. If no results, that's a violation

This two-step process (browse → individual search) is the only way to find
non-compliance.

### 6. Visualizing the Regression

```
                    First Audit (Jun 8)     Second Audit (Jun 11)
                    ─────────────────       ──────────────────
Violations found:   3                       4
Assessment:         "static with gaps"      "regressing"
C-001 violations:   2                       3
C-003 violations:   1                       1
C-002 violations:   unverifiable            unverifiable

Behavior change?    None observed           None observed
```

## Implications for Future Audits

1. **Pattern is worsening, not improving.** The auditor is detecting, not
   preventing. The gap between commitments and behavior is widening.

2. **Consider raising severity.** A HIGH violation (0 skill_view in 400+ msgs)
   is now the norm, not an exception. The auditor should consider marking C-001
   as "violated" if this continues.

3. **Add a new commitment.** Consider a commitment that the agent must
   demonstrate compliance within N sessions or the commitment system itself
   escalates (structural enforcement, system prompt modification, etc.).

4. **Audit the cron agents separately.** They run a different model
   (deepseek-v4-flash vs openrouter/owl-alpha) with different capabilities.
   Their skill-loading failures may have different root causes.
