# Problem Decoder Prompt

**Adapted from Lingxi v2.0's SWE-bench decoder (81.2% Pass@1).**  
Injected into the Player's workflow BEFORE writing the mini-plan.

## Usage

The Player runs this analysis at Step 2.5 of each tick:

```
Read task from AGENTS.md → Retrieve DevKnowledge → Decoder analysis → Mini-plan → Implement
```

## Prompt

```
You are performing a structured pre-implementation analysis for the following
task. Your analysis will guide the implementation plan.

### Task to analyze

{TASK_DESCRIPTION}

Project: {PROJECT_NAME}
Repo: {REPO_PATH}

### Historical Fix Knowledge

{DEV_KNOWLEDGE}

(The above are the top-3 most similar past fixes from this project's history.
Use them to understand patterns, common pitfalls, and how similar issues were
resolved before. If empty, no prior knowledge available.)

### Trajectory Guidance (from full Decoder→Mapper→Solver traces)

{TRAJECTORY_GUIDANCE}

(The above is procedural guidance distilled from past repair trajectories — 
diagnostic tips, strategies that worked, pitfalls to avoid, regression risks.
This is richer than the diff-based knowledge above. Use it to understand
not just WHAT was fixed, but HOW it was diagnosed and WHY that approach worked.)

### Your analysis

Follow these phases:

1. READING — Restate the task in clear, specific terms.
   - If there are code/framework specifics mentioned, highlight them.
   - Distill the task to its essence: what is actually being asked?

2. EXPLORATION — Using the repo, find the files that are relevant.
   - Search for relevant components, functions, classes mentioned.
   - Identify which files will need to change.
   - Look at how similar changes were made in the past (use DevKnowledge).

3. ROOT CAUSE — If this is a bug fix, what's the root cause?
   - If this is a new feature, what's the architectural "why"?
   - Reference specific files, functions, and lines where possible.

4. EXPECTED BEHAVIOR — After the fix/feature, what should be true?
   - What should the user see? What state should change?
   - How will we verify this worked?

### Output Format

Produce your analysis as a structured block the Planner (next step) can consume:

<decoder_analysis>
  <problem_statement>
    [One-sentence distilled essence of the task]
  </problem_statement>
  <relevant_files>
    - apps/web/src/app/study/page.tsx — [why relevant]
    - apps/api/routers/solver.py — [why relevant]
    - [any others]
  </relevant_files>
  <past_patterns>
    - [Pattern from DevKnowledge: "fixed similar issue by..."]
    - [Pitfall to avoid: "previous fix caused regression in..."]
    - [If no patterns, say "No relevant past fixes found"]
  </past_patterns>
  <expected_behavior>
    - [What the user will see after the fix]
    - [What state/API change is expected]
  </expected_behavior>
  <risk_assessment>
    - [Files that are high-risk to touch]
    - [Features that could break as side effects]
    - [Complexity: low | medium | high]
  </risk_assessment>
</decoder_analysis>

### Rules

- **Use exact file paths** from the repo (via view_directory / search_files_by_keywords).
- **Be specific about expected behavior** — what the user sees, not code changes.
- **If DevKnowledge shows a pattern that contradicts the current task** (e.g., past fix broke something), flag it in risk_assessment.
- **Keep it focused**: this is for one task, not the whole project.
- **Do NOT write code or a plan** — that's the Planner's job after you.
```

## Integration

The Player runs this analysis in their terminal as a structured prompt to their LLM 
(the same model they use for implementation). The output `<decoder_analysis>` block 
is fed into the mini-plan step as context.

### DevKnowledge (diff-based historical fixes)

Populate `{DEV_KNOWLEDGE}` by querying:
```
python3 ~/repos/autonomous-dev-system/skills/coach-agent/scripts/dev-knowledge-store.py --query "{TASK_DESCRIPTION}"
```
If the query returns no good matches (similarity < 0.5), the Decoder proceeds without
historical context — the `<past_patterns>` section will say "No relevant past fixes found".

### Trajectory Guidance (procedural knowledge from past repairs)

Populate `{TRAJECTORY_GUIDANCE}` by running:
```
python3 ~/repos/autonomous-dev-system/skills/coach-agent/scripts/trajectory-save.py retrieve --task "{TASK_DESCRIPTION}" --project "{PROJECT_NAME}"
```
This queries the trajectory store for guidance from past APPROVED repairs — diagnostic tips,
strategies that worked, pitfalls to avoid. If no trajectories exist, the section is empty.
Trajectory guidance is richer than diff-based knowledge because it captures HOW a fix was
diagnosed and implemented, not just WHAT changed.
