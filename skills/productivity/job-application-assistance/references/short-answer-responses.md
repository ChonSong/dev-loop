# Short Answer Responses — Job Application Format

Some job postings (especially for junior/mid-level tech roles) ask for short written responses instead of or in addition to a cover letter. This reference covers the common patterns and how to answer them effectively.

## Common Question Types

### 1. "Describe a bug you debugged"

**Structure (STAR format, ~150-250 words):**
- **Situation:** What system? What was the symptom?
- **Task:** What needed to be fixed?
- **Action:** How did you trace it? What tools/logs did you use? What was the root cause?
- **Result:** What was the fix? How did you prevent recurrence?

**Key principles:**
- Be specific about tools (Python logging, browser DevTools, SQL queries, Git bisect, etc.)
- Show systematic debugging — not "I guessed and it worked"
- Mention the fix was committed via PR with tests if possible
- Even personal project bugs count — just be clear about the context

**Example (good):**
> "While building a poker equity calculator, the ICM module returned incorrect results for certain payout structures. I isolated the issue by writing test cases with known correct outputs, then traced the data flow using Python logging. The bug was a double-division in the payout normalization — percentages were divided by 100 twice. I fixed the calculation function, added regression tests, and committed via PR."

**Example (bad):**
> "I fixed a bug in my code. It was hard but I figured it out."

### 2. "Describe a code change you implemented"

**Structure (~150-250 words):**
- What was the problem or feature request?
- What did you change? (Be specific: backend, frontend, database, API)
- How did you test/validate it?
- What was the outcome?

**Key principles:**
- Show full-stack thinking if possible (not just "I changed one function")
- Mention testing strategy (unit tests, manual testing, comparison against reference)
- Reference PRs, code reviews, or release tags if applicable

### 3. "Which technologies have you worked with?" (Checklist)

**How to answer:**
- Be honest. Only check what you've genuinely used.
- If you've used a similar technology (e.g., Vue instead of React), note it: "React / Frontend frameworks — Yes. Built with Next.js and React. Also Vue.js."
- Add brief context for each: "Python — backend services, automation scripts, data pipelines"

### 4. "Have you used GitHub / raised pull requests?"

**Answer tiers:**
- "Yes, regularly" — if you use feature branches, PRs, and tagged releases for personal or professional projects
- "Yes, a few times" — if you've done it but not as a regular workflow
- "No, but familiar" — if you understand the concept but haven't practiced it
- "No" — avoid this if possible; set up a GitHub account and push a project before applying

### 5. "Are you comfortable working on production issues?"

**Answer tiers:**
- "Very comfortable" — only if you have real debugging experience (even in personal projects that you've deployed)
- "Comfortable" — if you've debugged issues but not in a commercial production environment
- "Some experience" — if you've only done limited debugging
- "No experience" — avoid this answer; reframe any debugging you've done

## General Tips

- **Specificity beats generality.** "I used Python logging and browser DevTools" beats "I used debugging tools."
- **Personal projects count.** Most junior applicants don't have professional production experience. Frame your project work honestly but confidently.
- **Show your process.** Employers want to know *how* you think, not just *what* you did.
- **Keep it concise.** These are "short answers" — 3-5 sentences per question is usually enough. Don't write an essay.
- **Match their language.** If they say "root cause analysis," use that phrase. If they say "pull requests," say "pull requests" (not "merge requests").
- **Don't fabricate.** If you haven't used a technology, say so or frame it as "familiar with" rather than "experienced in."

## Anti-Patterns

- Vague answers without tool names or specific examples
- Copy-pasting the same answer for every application
- Overstating experience (claiming "very comfortable" when you've only done tutorials)
- Writing too long (recruiters skim these — respect the "short answer" format)
- Not proofreading (typos in a written application are a red flag for a software role)
