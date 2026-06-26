# RefQA

## Tasks

### Task: implement-yaml-parser

**Description:** Write a YAML test file parser that validates the refqa format: test-id, name, targets (primary + optional references), steps, and optional reference key per step.

**Success criteria:** Parser reads a valid YAML file and returns a typed Test object. Parser rejects invalid YAML with clear error messages showing the file and line number.

### Task: implement-step-executor

**Description:** Write the step execution engine. Each step is resolved by an LLM call to OpenCode Zen (`mimo-v2.5-free` model). The LLM converts natural language into Playwright actions (click, wait, verify, navigate). The executor runs the actions and returns the result.

**Success criteria:** Given a YAML step `- Click on "UTG" position card`, the executor navigates to the target URL, clicks the right element, and returns success. The LLM resolves selector, Playwright executes it.

### Task: implement-reference-comparator

**Description:** When a step has `reference: <target>`, the executor spawns two parallel sub-sessions (one for primary target, one for reference). Both execute the same LLM-generated plan. A comparator checks if the results match.

**Success criteria:** Step with reference succeeds only when both apps return matching results. Step fails when results diverge.
