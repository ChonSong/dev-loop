#!/usr/bin/env python3
"""
Verification Phase — inline check between Solver and Test.

Reads Mapper output, Solver summary, git diff, and test output, then
sends a structured prompt to a fast LLM to detect common failure patterns:
  - Files changed don't match the plan (±1 tolerance)
  - Test pass count doesn't match expected
  - Debug artifacts (console.log, debugger, # TODO) in diff
  - Files >500 LOC changed without matching plan scope

Output: JSON {status: "PASS"|"FLAG", warnings: [{type, message, severity}]}
Exit 0 on PASS, exit 1 on FLAG (non-fatal — Player decides to proceed or re-run).
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────
REPO_ROOT = Path.home() / "repos" / "autonomous-dev-system"
MAPPER_OUTPUT = Path("/tmp/mapper-output.txt")
SOLVER_SUMMARY = Path("/tmp/solver-summary.txt")
TEST_OUTPUT = Path("/tmp/test-output.txt")

# ── API Config ────────────────────────────────────────────────────────────────
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "deepseek/deepseek-v4-flash"

# ── Helpers ───────────────────────────────────────────────────────────────────

def load_env_api_key() -> str:
    """Load OPENROUTER_API_KEY from environment or ~/.hermes/.env."""
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if key:
        return key
    # Fallback: parse ~/.hermes/.env
    env_path = Path.home() / ".hermes" / ".env"
    if env_path.exists():
        content = env_path.read_text()
        match = re.search(r'OPENROUTER_API_KEY\s*=\s*"?([^"\n]+)"?', content)
        if match:
            return match.group(1).strip()
    return ""


def read_file_safe(path: Path) -> str:
    """Read file contents, return empty string if missing."""
    try:
        return path.read_text()
    except (FileNotFoundError, OSError):
        return ""


def get_git_diff_stat(repo: Path) -> str:
    """Get git diff --stat for the repo."""
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), "diff", "--stat"],
            capture_output=True, text=True, timeout=10
        )
        return result.stdout.strip()
    except (subprocess.TimeoutExpired, OSError):
        return ""


def get_git_diff_full(repo: Path) -> str:
    """Get full git diff (truncated to 8000 chars for LLM)."""
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), "diff"],
            capture_output=True, text=True, timeout=10
        )
        return result.stdout[:8000]
    except (subprocess.TimeoutExpired, OSError):
        return ""


def call_llm(prompt: str, api_key: str, timeout: int = 30) -> dict:
    """Send prompt to OpenRouter and return parsed JSON response."""
    import urllib.request
    import urllib.error

    payload = json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are a code review verification agent. You output ONLY valid JSON, no other text."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 1024,
        "response_format": {"type": "json_object"}
    }).encode("utf-8")

    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://hermes-agent.nousresearch.com",
            "X-Title": "Player Verification Phase"
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            content = body["choices"][0]["message"]["content"]
            # Strip markdown code fences if present
            content = re.sub(r'^```(?:json)?\s*', '', content.strip())
            content = re.sub(r'\s*```$', '', content.strip())
            return json.loads(content)
    except (urllib.error.URLError, json.JSONDecodeError, KeyError) as e:
        return {"status": "FLAG", "warnings": [{"type": "llm_error", "message": str(e), "severity": "high"}]}


def local_checks(mapper_text: str, solver_text: str, diff_stat: str, diff_full: str, test_output: str) -> list:
    """
    Run lightweight local checks before the LLM.
    Returns warnings list. An empty LLM call is avoided if local checks are clean
    and the input looks reasonable — but we still run LLM for full verification.
    """
    warnings = []

    # Check: mapper output exists
    if not mapper_text.strip():
        warnings.append({"type": "missing_input", "message": "No mapper output found at /tmp/mapper-output.txt", "severity": "high"})

    # Check: solver summary exists
    if not solver_text.strip():
        warnings.append({"type": "missing_input", "message": "No solver summary found at /tmp/solver-summary.txt", "severity": "high"})

    # Check: git diff exists
    if not diff_stat.strip():
        warnings.append({"type": "no_changes", "message": "No git diff detected — no files were changed", "severity": "high"})

    # Check: debug artifacts in diff (fast local scan)
    debug_patterns = [
        # Look for added debug lines in git diff (+ prefix = added line)
        (r'^\+\s*console\.log\s*\(', "console.log"),
        (r'^\+\s*debugger\b', "debugger statement"),
        (r'^\+\s*#\s*TODO\b', "# TODO comment"),
        (r'^\+\s*#\s*FIXME\b', "# FIXME comment"),
        (r'^\+\s*#\s*HACK\b', "# HACK comment"),
    ]
    for pattern, label in debug_patterns:
        if re.search(pattern, diff_full, re.MULTILINE):
            warnings.append({"type": "debug_artifact", "message": f"Found {label} in diff", "severity": "medium"})

    # Check: large file changes
    if diff_stat:
        for line in diff_stat.split("\n"):
            # Parse lines like "path/to/file | 523 ++++++++++++..."
            m = re.match(r'\s*(\S+)\s*\|\s*(\d+)\s', line)
            if m:
                filepath, changes = m.group(1), int(m.group(2))
                if changes > 500:
                    warnings.append({
                        "type": "large_change",
                        "message": f"File {filepath} has {changes} lines changed (>500 LOC threshold)",
                        "severity": "medium"
                    })

    return warnings


def build_prompt(mapper_text: str, solver_text: str, diff_stat: str, diff_full: str, test_output: str, local_warnings: list) -> str:
    """Build the structured verification prompt for the LLM."""
    prompt = f"""You are a code review verification agent. Analyze the following inputs and determine if the implementation is clean.

## Inputs

### 1. Solution Mapper Plan
{mapper_text[:2000] if mapper_text else "(none)"}

### 2. Solver Summary
{solver_text[:2000] if solver_text else "(none)"}

### 3. Git Diff Stat
{diff_stat[:1000] if diff_stat else "(no changes)"}

### 4. Git Diff (abbreviated)
{diff_full[:3000] if diff_full else "(no diff)"}

### 5. Test Output
{test_output[:1000] if test_output else "(not available)"}

### 6. Local Pre-Checks
{json.dumps(local_warnings, indent=2) if local_warnings else "No local warnings"}

## Verification Rules

Check the following and produce a JSON object:

1. **Files changed match plan (±1 tolerance)**: Extract filenames from the Mapper plan. Count how many files appear in git diff --stat. If 2+ files changed that were NOT mentioned in the plan, flag as "unexpected_files".
2. **Test pass count**: If test output is available, check if pass count seems reasonable. If 0 tests passed and >0 were expected, flag as "test_failure".
3. **Debug artifacts**: Check the diff for console.log, debugger statements, # TODO, # FIXME, # HACK comments that were added (not removed). Flag as "debug_artifact".
4. **Large file changes**: If any single file has >500 lines changed and the plan doesn't explicitly scope it as a refactor, flag as "large_change".

## Output Format

Respond with ONLY this JSON structure, no other text:

{{
  "status": "PASS",
  "warnings": []
}}

If issues found:

{{
  "status": "FLAG",
  "warnings": [
    {{"type": "unexpected_files", "message": "...", "severity": "medium"}},
    {{"type": "debug_artifact", "message": "...", "severity": "low"}}
  ]
}}

Severity must be one of: "low", "medium", "high".

## Instructions
- Be conservative: only flag clear issues, not stylistic preferences.
- If status is FLAG, each warning must have a specific, actionable message.
- If everything looks clean, return PASS with empty warnings.
- Do NOT flag test files or config files that the plan explicitly mentions.
"""
    return prompt


# ── CLI ───────────────────────────────────────────────────────────────────────

def cmd_check(args):
    """Run the full verification phase check."""
    api_key = load_env_api_key()
    if not api_key:
        print(json.dumps({
            "status": "FLAG",
            "warnings": [{"type": "config_error", "message": "OPENROUTER_API_KEY not found in env or ~/.hermes/.env", "severity": "high"}]
        }))
        sys.exit(1)

    # Read inputs
    mapper_text = read_file_safe(MAPPER_OUTPUT)
    solver_text = read_file_safe(SOLVER_SUMMARY)
    test_output = read_file_safe(TEST_OUTPUT)

    # Git diff
    project_repo = Path(args.repo) if args.repo else REPO_ROOT
    diff_stat = get_git_diff_stat(project_repo)
    diff_full = get_git_diff_full(project_repo)

    # Local checks
    local_warnings = local_checks(mapper_text, solver_text, diff_stat, diff_full, test_output)

    # Build prompt and call LLM
    prompt = build_prompt(mapper_text, solver_text, diff_stat, diff_full, test_output, local_warnings)
    result = call_llm(prompt, api_key)

    # Merge local warnings into result (LLM may catch more)
    llm_warnings = result.get("warnings", [])
    all_warnings = local_warnings + llm_warnings

    # Deduplicate by message
    seen = set()
    deduped = []
    for w in all_warnings:
        key = (w.get("type"), w.get("message"))
        if key not in seen:
            seen.add(key)
            deduped.append(w)

    output = {
        "status": result.get("status", "FLAG"),
        "warnings": deduped
    }

    print(json.dumps(output, indent=2))

    if output["status"] == "PASS":
        sys.exit(0)
    else:
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Verification Phase — inline check between Solver and Test"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    check_parser = sub.add_parser("check", help="Run verification check")
    check_parser.add_argument("--repo", default=None, help="Path to project repo (default: ~/repos/autonomous-dev-system)")
    check_parser.set_defaults(func=cmd_check)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
