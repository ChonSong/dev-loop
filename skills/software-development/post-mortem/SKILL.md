---
name: post-mortem
description: Write the canonical engineering record of a fixed bug — root cause, mechanism, fix, validation, and how it slipped through. Use after a debug session lands a fix, before closing the ticket. Trigger on /post-mortem, when the user says "write the post-mortem / postmortem / RCA / root cause analysis", "document this fix", "write up the root cause", or hands you a fixed-and-validated bug and asks for the writeup.
---

# Post-mortem

The canonical engineering record of a bug fix. Written **after** debugging lands a real fix, **for** other engineers (and future-you, who will have forgotten everything in 6 months). Code identifiers are welcome here.

## When to invoke

- `/post-mortem`
- "write the post-mortem / postmortem / RCA / root-cause analysis"
- "document this fix" / "write up the root cause" / "close out this bug with a writeup"
- After a debug session has clearly landed a fix, proactively offer to draft one.

## When NOT to use

- **Bug not fixed yet, or fix not validated.** A post-mortem of a hypothesis is misleading. Refuse and tell the user what's missing.
- **Customer-visible outage / incident.** Those need a separate incident report. This skill is bug-fix scope.
- **Trivial fix** (typo, obvious one-liner). The PR description is the record.

## Required inputs — refuse to draft without these

Before writing a single line, confirm all four. If any are missing, list what's missing and stop:

- [ ] **Reliable repro** exists (not "happens sometimes" — a deterministic or high-rate-flake repro)
- [ ] **Root cause is known** (the mechanism is identified, not a hypothesis)
- [ ] **Fix is identified** (PR / commit / branch pointer)
- [ ] **Fix is validated** (the original repro now passes)

## Structure

Use these blocks in this order. **Summary, Root cause, Fix, and Validation are mandatory.**

### 1. Summary _(mandatory)_
One paragraph. What broke in user/workload terms. What fixed it in one sentence. JIRA key, PR number, owner. A reader who stops here should have the right answer.

### 2. Symptom
What was actually observed. Test output, error message, log line, perf number, customer report.

### 3. Root cause _(mandatory)_
The actual bug mechanism. **Code identifiers welcome and expected** — function names, file paths, struct fields, branch conditions. Walk the cause chain end-to-end.

### 4. Why it produced the symptom
Link the root cause to the symptom. Walk the chain so a reader who only knows the symptom can connect it back to the cause without re-deriving it.

### 5. Fix _(mandatory)_
What changed and **why this change addresses the root cause**. Link to PR / commit. If a previous fix attempt papered over the symptom, name it and explain what was wrong with it.

### 6. How it was found
Short. The debugging path. What repro made it deterministic. What tools cracked it. Hypotheses tried and rejected. The single experiment that confirmed the cause.

### 7. Why it slipped through
What allowed this bug to reach the branch / release / customer. Pick the real reason:
- CI gap (no test exercises this path)
- Latent code (correct when written, broken by a later change)
- Workload gap (no real workload reached this code path until now)
- Incomplete prior fix (defensive check hid the symptom; root cause untouched)
- Review miss

**Blameless** — describe the gap, not the person.

### 8. Validation _(mandatory)_
How we know the fix works. Concrete:
- Original failing test now passes (test name, link)
- Customer workload now completes
- Stress / soak / fuzz run completed clean

State coverage honestly — *"Not retested on other configurations"* is information, not a hole.

### 9. Action items / follow-ups
Concrete next-steps that aren't in the fix PR itself. Each: what + owner + tracking artifact.

If there are no action items: *"None — the fix is sufficient and no class-of-bug follow-up is warranted."*

## Output flow

1. **Confirm all four required inputs are satisfied.** If any missing, list them and stop.
2. **Produce the draft** as a single chat block.
3. **Sign-off before posting.** Wait for explicit *"post it"* / *"go ahead"* / *"yes."*
4. **Offer the handoff:** *"Want a leadership-flavored version? I can hand this to `management-talk`."* Don't do it automatically.

## Tone

- **Code identifiers are first-class** — keep them.
- **Mechanism over narrative** — walk the actual cause chain.
- **Active voice, concrete subjects, short paragraphs.**
- **No hedging.** "We believe" / "appears to" — drop. State it or don't write it.
- **Blameless.** Describe the bug and the gap, never the person.
- **No advocacy.** This records what happened and what's next. If you want to argue for a refactor, that's a separate proposal.