#!/usr/bin/env python3
"""
Requirements Engine — Grand SIE Phase 2.

Evaluates Opportunity Radar signals, produces formal specs,
and generates AGENTS.md task breakdowns via LLM.

Usage:
    requirements-engine.py evaluate <radar.json>         # Score BUILD items
    requirements-engine.py spec <evaluated.json>         # Produce formal specs
    requirements-engine.py create-tasks <spec.md>        # Generate AGENTS.md entries
    requirements-engine.py pipeline <radar.json>         # evaluate → spec → create-tasks
    requirements-engine.py pipeline --stdin              # Read radar JSON from stdin

Environment:
    OPENROUTER_API_KEY — API key for OpenRouter (LLM calls)
    OPENROUTER_MODEL    — Model to use (default: google/gemma-3-27b-it:free)

Exit codes:
    0 — success
    1 — no items passed threshold
    2 — error
"""

import argparse
import json
import os
import re
import subprocess
import sys
import textwrap
import urllib.request
import urllib.error
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ── Configuration ──────────────────────────────────────────────────────

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.environ.get(
    "OPENROUTER_MODEL", "google/gemma-4-26b-a4b-it:free"
)
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SPEC_TEMPLATE_PATH = (
    Path(__file__).resolve().parent / "references" / "spec-template.md"
)
SIEGEN_DIR = REPO_ROOT / "siegen"  # output directory for specs and tasks

# ── Data Models ────────────────────────────────────────────────────────


@dataclass
class EvaluationScore:
    """Scoring result for one BUILD signal."""

    signal_title: str
    domain: str
    domain_alignment: int = 0
    build_complexity: int = 3
    data_dependency: int = 4
    learning_roi: int = 2
    reasoning: dict = field(default_factory=dict)

    @property
    def combined_score(self) -> int:
        return (
            self.domain_alignment
            + self.build_complexity
            + self.data_dependency
            + self.learning_roi
        )

    @property
    def verdict(self) -> str:
        s = self.combined_score
        if s >= 12:
            return "ACCEPT"
        elif s >= 9:
            return "REVIEW"
        return "REJECT"


@dataclass
class EvaluationResult:
    """Full evaluation output."""

    date: str
    items: list[dict] = field(default_factory=list)
    accepted: list[dict] = field(default_factory=list)
    review: list[dict] = field(default_factory=list)
    rejected: list[dict] = field(default_factory=list)


# ── Domain Alignment Scoring ───────────────────────────────────────────

DOMAIN_SCORES = {
    "poker": 5,
    "gto": 5,
    "game-dev": 4,
    "game_dev": 4,
    "gamedev": 4,
    "ai-agents": 3,
    "ai_agents": 3,
    "ai-infra": 3,
    "ai_infra": 3,
    "ai": 3,
    "3dcp": 2,
    "3d-printing": 2,
    "3d_printing": 2,
}


def score_domain_alignment(domain: str) -> tuple[int, str]:
    """Map a domain string to its alignment score."""
    domain_lower = domain.lower().replace(" ", "-").replace("_", "-")
    score = DOMAIN_SCORES.get(domain_lower, 0)
    if score == 5:
        reason = "poker/GTO — highest strategic priority"
    elif score == 4:
        reason = "game development — strong secondary domain"
    elif score == 3:
        reason = "AI infrastructure — relevant to agent capabilities"
    elif score == 2:
        reason = "3DCP — niche but active domain"
    else:
        reason = f"unrecognized domain '{domain}' — no strategic alignment"
    return score, reason


# ── Build Complexity Estimation ────────────────────────────────────────

COMPLEXITY_KEYWORDS = {
    # (score, keywords...)
    1: ["cli", "tool", "script", "utility", "command-line", "command line"],
    2: [
        "web", "dashboard", "page", "frontend", "single-page",
        "single page", "spa", "static site",
    ],
    3: [
        "api", "backend", "database", "full-stack", "full stack",
        "fullstack", "server", "rest", "graphql",
    ],
    4: [
        "game", "engine", "render", "3d", "simulation", "physics",
        "real-time", "realtime",
    ],
    5: [
        "platform", "service", "orchestration", "microservice",
        "multi-service", "multi service", "distributed",
    ],
}


def estimate_build_complexity(
    title: str, description: str, explicit: Optional[int] = None
) -> tuple[int, str]:
    """Estimate build complexity from title, description, and optional explicit score."""
    if explicit is not None and 1 <= explicit <= 5:
        return explicit, f"explicitly set to {explicit}"

    combined = f"{title} {description}".lower()

    # Check from highest to lowest score to catch most specific first
    for score in [5, 4, 3, 2, 1]:
        for kw in COMPLEXITY_KEYWORDS[score]:
            if kw in combined:
                return score, f"matched keyword '{kw}' → score {score}"

    return 3, "no keywords matched → default full-stack (3)"


# ── Data / API Dependency Estimation ───────────────────────────────────

DATA_DOMAIN_DEFAULTS = {
    "poker": (4, "free data available: hand histories, solver outputs"),
    "gto": (4, "free data available: solver databases, training sets"),
    "game-dev": (5, "self-contained — no external data required"),
    "game_dev": (5, "self-contained — no external data required"),
    "gamedev": (5, "self-contained — no external data required"),
    "ai-agents": (4, "free APIs: OpenRouter free tier, HuggingFace"),
    "ai_agents": (4, "free APIs: OpenRouter free tier, HuggingFace"),
    "ai-infra": (4, "free APIs available"),
    "ai_infra": (4, "free APIs available"),
    "3dcp": (2, "often requires hardware/sensor data or paid CAD software"),
    "3d-printing": (2, "may require paid slicing software"),
}

DATA_PAID_KEYWORDS = [
    "stripe", "openai", "paid", "subscription", "premium",
    "license", "aws", "gcp", "azure", "enterprise",
]

DATA_NO_SOURCE_KEYWORDS = [
    "proprietary", "classified", "internal only", "no data",
]


def estimate_data_dependency(
    domain: str,
    description: str,
    explicit: Optional[int] = None,
) -> tuple[int, str]:
    """Estimate data/API dependency."""
    if explicit is not None and explicit in (0, 2, 4, 5):
        return explicit, f"explicitly set to {explicit}"

    domain_lower = domain.lower().replace(" ", "-").replace("_", "-")
    desc_lower = (description or "").lower()

    # Check for no-source indicators
    for kw in DATA_NO_SOURCE_KEYWORDS:
        if kw in desc_lower:
            return 0, f"matched '{kw}' — no accessible data source"

    # Check for paid indicators
    for kw in DATA_PAID_KEYWORDS:
        if kw in desc_lower:
            return 2, f"matched '{kw}' — likely paid dependency"

    # Domain default
    if domain_lower in DATA_DOMAIN_DEFAULTS:
        score, reason = DATA_DOMAIN_DEFAULTS[domain_lower]
        return score, reason

    return 4, "unknown domain → optimistic free-API estimate (4)"


# ── Learning ROI Estimation ────────────────────────────────────────────

ROI_DOMAIN_DEFAULTS = {
    "poker": (5, "broad ML/strategy skills, transferable"),
    "gto": (5, "broad math/ML skills, transferable"),
    "game-dev": (4, "graphics, UX, performance — broad software skills"),
    "game_dev": (4, "graphics, UX, performance — broad software skills"),
    "gamedev": (4, "graphics, UX, performance — broad software skills"),
    "ai-agents": (5, "agent architectures, LLM skills — high transfer"),
    "ai_agents": (5, "agent architectures, LLM skills — high transfer"),
    "ai-infra": (5, "infra skills highly transferable"),
    "ai_infra": (5, "infra skills highly transferable"),
    "3dcp": (2, "niche domain, hardware-coupled — limited reuse"),
    "3d-printing": (2, "niche domain, hardware-coupled — limited reuse"),
}


def estimate_learning_roi(
    domain: str, explicit: Optional[int] = None
) -> tuple[int, str]:
    """Estimate learning ROI."""
    if explicit is not None and explicit in (2, 5):
        return explicit, f"explicitly set to {explicit}"

    domain_lower = domain.lower().replace(" ", "-").replace("_", "-")
    if domain_lower in ROI_DOMAIN_DEFAULTS:
        score, reason = ROI_DOMAIN_DEFAULTS[domain_lower]
        return score, reason

    return 2, "unknown domain → conservative estimate (2)"


# ── Evaluation Engine ──────────────────────────────────────────────────


def evaluate_signal(signal: dict) -> EvaluationScore:
    """Score a single BUILD signal."""
    title = signal.get("title", "Untitled")
    domain = signal.get("domain", "unknown")
    desc = signal.get("description", "") or ""

    da_score, da_reason = score_domain_alignment(domain)
    bc_score, bc_reason = estimate_build_complexity(
        title, desc, signal.get("build_complexity")
    )
    dd_score, dd_reason = estimate_data_dependency(
        domain, desc, signal.get("data_dependency")
    )
    lr_score, lr_reason = estimate_learning_roi(
        domain, signal.get("learning_roi")
    )

    return EvaluationScore(
        signal_title=title,
        domain=domain,
        domain_alignment=signal.get("domain_alignment", da_score),
        build_complexity=signal.get("build_complexity", bc_score),
        data_dependency=signal.get("data_dependency", dd_score),
        learning_roi=signal.get("learning_roi", lr_score),
        reasoning={
            "domain_alignment": da_reason,
            "build_complexity": bc_reason,
            "data_dependency": dd_reason,
            "learning_roi": lr_reason,
        },
    )


def deduplicate_signals(signals: list[dict]) -> list[dict]:
    """Remove duplicate titles, keeping the one with highest combined score."""
    seen: dict[str, dict] = {}
    for sig in signals:
        key = sig.get("title", "").strip().lower()
        if not key:
            continue
        if key in seen:
            # Keep the one with higher relevance or combined score
            existing = seen[key]
            new_sum = sum(
                sig.get(k, 0) for k in ("relevance", "novelty", "actionability")
            )
            old_sum = sum(
                existing.get(k, 0)
                for k in ("relevance", "novelty", "actionability")
            )
            if new_sum > old_sum:
                seen[key] = sig
        else:
            seen[key] = sig
    return list(seen.values())


def evaluate(radar_json: dict) -> EvaluationResult:
    """Evaluate all BUILD signals in a radar output."""
    signals = radar_json.get("signals", [])
    build_signals = [
        s for s in signals if s.get("recommendation", "").upper() == "BUILD"
    ]

    if not build_signals:
        print("[WARN] No BUILD signals found in radar output", file=sys.stderr)

    # Deduplicate
    build_signals = deduplicate_signals(build_signals)

    result = EvaluationResult(
        date=radar_json.get("date", datetime.now(timezone.utc).strftime("%Y-%m-%d")),
    )

    for sig in build_signals:
        score = evaluate_signal(sig)
        item = {
            **sig,
            "evaluation": {
                "domain_alignment": score.domain_alignment,
                "build_complexity": score.build_complexity,
                "data_dependency": score.data_dependency,
                "learning_roi": score.learning_roi,
                "combined_score": score.combined_score,
                "verdict": score.verdict,
                "reasoning": score.reasoning,
            },
        }
        result.items.append(item)

        if score.verdict == "ACCEPT":
            result.accepted.append(item)
        elif score.verdict == "REVIEW":
            result.review.append(item)
        else:
            result.rejected.append(item)

    return result


# ── Spec Generator ─────────────────────────────────────────────────────


def load_spec_template() -> str:
    """Load the spec template markdown."""
    if SPEC_TEMPLATE_PATH.exists():
        return SPEC_TEMPLATE_PATH.read_text()
    # Fallback embedded template
    return textwrap.dedent("""\
        # {{TITLE}}

        **Generated by:** Requirements Engine (Grand SIE Phase 2)
        **Date:** {{DATE}}
        **Source Signal:** {{SIGNAL_URL}}
        **Domain:** {{DOMAIN}}
        **Combined Score:** {{COMBINED_SCORE}}/20

        ---

        ## Strategic Rationale

        ### Why This Matters

        {{STRATEGIC_RATIONALE}}

        ### Opportunity Window

        {{OPPORTUNITY_WINDOW}}

        ---

        ## User Stories

        ### Story 1 — {{STORY_1_TITLE}}

        As a **{{PERSONA_1}}**, I want to **{{ACTION_1}}** so that **{{GOAL_1}}**.

        ### Story 2 — {{STORY_2_TITLE}}

        As a **{{PERSONA_2}}**, I want to **{{ACTION_2}}** so that **{{GOAL_2}}**.

        ---

        ## Acceptance Criteria

        - [ ] **AC-1:** {{AC_1}}
        - [ ] **AC-2:** {{AC_2}}
        - [ ] **AC-3:** {{AC_3}}

        ---

        ## Reference Behavior

        ### Input / Output Contract

        ```
        INPUT:  {{INPUT_DESCRIPTION}}
        OUTPUT: {{OUTPUT_DESCRIPTION}}
        ```

        ### Edge Cases

        1. **{{EDGE_CASE_1_TITLE}}:** {{EDGE_CASE_1_BEHAVIOR}}

        ### Example Usage

        ```bash
        {{EXAMPLE_USAGE}}
        ```

        ---

        ## Technical Constraints

        | Constraint          | Value            | Rationale                       |
        |---------------------|------------------|----------------------------------|
        | Language / Runtime  | {{LANGUAGE}}     | {{LANGUAGE_RATIONALE}}           |
        | Max build time      | {{MAX_BUILD}}    | {{BUILD_TIME_RATIONALE}}         |
        | External services   | {{SERVICES}}     | {{SERVICES_RATIONALE}}           |
        | Target platform     | {{PLATFORM}}     | {{PLATFORM_RATIONALE}}           |

        ---

        ## AGENTS.md Task Breakdown

        <!-- GENERATED by requirements-engine create-tasks -->

        {{TASK_BREAKDOWN}}

        ---

        ## Appendix: Evaluation Scores

        | Dimension            | Score | Reasoning                          |
        |----------------------|-------|------------------------------------|
        | Domain Alignment     | {{SCORE_DOMAIN}}/5  | {{REASON_DOMAIN}}               |
        | Build Complexity     | {{SCORE_COMPLEXITY}}/5  | {{REASON_COMPLEXITY}}           |
        | Data/API Dependency  | {{SCORE_DATA}}/5  | {{REASON_DATA}}                 |
        | Learning ROI         | {{SCORE_ROI}}/5  | {{REASON_ROI}}                  |
        | **Combined**         | **{{SCORE_COMBINED}}/20** | **{{RESULT}}**              |

        ---

        *Spec generated by Grand SIE Requirements Engine v1.0*
    """)


def infer_tech_stack(domain: str, title: str) -> dict:
    """Infer reasonable technical constraints from domain and title."""
    domain_lower = domain.lower().replace(" ", "-").replace("_", "-")
    title_lower = title.lower()

    # Defaults
    stack = {
        "language": "Python 3.11+",
        "language_rationale": "Primary development language",
        "max_build": "4 hours",
        "build_time_rationale": "Single-session build target",
        "services": "None",
        "services_rationale": "Self-contained",
        "platform": "Linux (primary), macOS (secondary)",
        "platform_rationale": "Development and deployment target",
        "dependencies": "stdlib + pip packages",
        "dependencies_rationale": "Minimal external dependencies",
    }

    # Web / frontend signals
    if any(kw in title_lower for kw in ["web", "dashboard", "page", "frontend"]):
        stack["language"] = "TypeScript (React) or Python (Flask/FastAPI)"
        stack["language_rationale"] = "Web-based UI indicated"

    # CLI tools
    if any(kw in title_lower for kw in ["cli", "command", "tool", "script"]):
        stack["language"] = "Python 3.11+"
        stack["language_rationale"] = "CLI tool — Python with argparse/click"

    # Game dev
    if domain_lower in ("game-dev", "game_dev", "gamedev"):
        stack["language"] = "TypeScript/JavaScript (Canvas/WebGL) or Python (Pygame)"
        stack["language_rationale"] = "Game development — browser or desktop target"
        stack["max_build"] = "8 hours"
        stack["build_time_rationale"] = "Game prototypes require more iteration"

    # AI / ML
    if domain_lower in ("ai-agents", "ai_agents", "ai-infra", "ai_infra"):
        stack["dependencies"] = "langchain, openai, or custom LLM client"
        stack["dependencies_rationale"] = "AI/agent workloads"

    return stack


def generate_spec(item: dict, template: str) -> str:
    """Fill the spec template for a single accepted item."""
    eval_data = item.get("evaluation", {})
    domain = item.get("domain", "unknown")
    title = item.get("title", "Untitled")
    tech = infer_tech_stack(domain, title)

    # Build replacements
    replacements = {
        "{{TITLE}}": title,
        "{{DATE}}": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "{{SIGNAL_URL}}": item.get("url", "N/A"),
        "{{DOMAIN}}": domain.upper(),
        "{{COMBINED_SCORE}}": str(eval_data.get("combined_score", "?")),
        "{{STRATEGIC_RATIONALE}}": (
            f"Signal '{title}' in domain '{domain}' was identified by the "
            f"Opportunity Radar as worth building. "
            f"Rationale: {item.get('rationale', 'No rationale provided.')}"
        ),
        "{{OPPORTUNITY_WINDOW}}": (
            "Immediate — radar signal indicates current relevance. "
            "Build within 2 weeks to capitalize on momentum."
        ),
        "{{STORY_1_TITLE}}": "Core Functionality",
        "{{PERSONA_1}}": "end user",
        "{{ACTION_1}}": f"use {title} to accomplish a key task",
        "{{GOAL_1}}": "I can achieve my objective efficiently",
        "{{STORY_2_TITLE}}": "Edge Case Handling",
        "{{PERSONA_2}}": "developer",
        "{{ACTION_2}}": f"understand how {title} handles unexpected inputs",
        "{{GOAL_2}}": "the system degrades gracefully without data loss",
        "{{STORY_3_TITLE}}": "Integration (if applicable)",
        "{{PERSONA_3}}": "system integrator",
        "{{ACTION_3}}": f"connect {title} to existing toolchain",
        "{{GOAL_3}}": "data flows seamlessly between systems",
        "{{AC_1}}": f"{title} accepts valid input and produces correct output",
        "{{AC_2}}": f"{title} handles malformed input with a clear error message, no crash",
        "{{AC_3}}": (
            f"{title} completes a typical operation within acceptable time "
            f"(< 5 seconds for CLI, < 2 seconds for web)"
        ),
        "{{AC_4}}": f"{title} logs its actions for debugging",
        "{{AC_5}}": f"{title} works on target platform(s) without manual setup beyond README instructions",
        "{{INPUT_DESCRIPTION}}": f"User provides input specific to {title}",
        "{{OUTPUT_DESCRIPTION}}": f"{title} produces structured, verifiable output",
        "{{EDGE_CASE_1_TITLE}}": "Empty input",
        "{{EDGE_CASE_1_BEHAVIOR}}": "Returns a clear message indicating no input was provided. Does not crash.",
        "{{EDGE_CASE_2_TITLE}}": "Very large input",
        "{{EDGE_CASE_2_BEHAVIOR}}": "Processes within timeout or returns partial results with a warning.",
        "{{EXAMPLE_USAGE}}": f"$ python {title.lower().replace(' ', '-')}.py --input data.json",
        "{{LANGUAGE}}": tech["language"],
        "{{LANGUAGE_RATIONALE}}": tech["language_rationale"],
        "{{MAX_BUILD}}": tech["max_build"],
        "{{BUILD_TIME_RATIONALE}}": tech["build_time_rationale"],
        "{{SERVICES}}": tech["services"],
        "{{SERVICES_RATIONALE}}": tech["services_rationale"],
        "{{PLATFORM}}": tech["platform"],
        "{{PLATFORM_RATIONALE}}": tech["platform_rationale"],
        "{{DEPENDENCIES}}": tech["dependencies"],
        "{{DEPENDENCIES_RATIONALE}}": tech["dependencies_rationale"],
        "{{TASK_BREAKDOWN}}": "<!-- Run: requirements-engine.py create-tasks <spec.md> -->",
        "{{SCORE_DOMAIN}}": str(eval_data.get("domain_alignment", "?")),
        "{{REASON_DOMAIN}}": eval_data.get("reasoning", {}).get(
            "domain_alignment", "N/A"
        ),
        "{{SCORE_COMPLEXITY}}": str(eval_data.get("build_complexity", "?")),
        "{{REASON_COMPLEXITY}}": eval_data.get("reasoning", {}).get(
            "build_complexity", "N/A"
        ),
        "{{SCORE_DATA}}": str(eval_data.get("data_dependency", "?")),
        "{{REASON_DATA}}": eval_data.get("reasoning", {}).get(
            "data_dependency", "N/A"
        ),
        "{{SCORE_ROI}}": str(eval_data.get("learning_roi", "?")),
        "{{REASON_ROI}}": eval_data.get("reasoning", {}).get(
            "learning_roi", "N/A"
        ),
        "{{SCORE_COMBINED}}": str(eval_data.get("combined_score", "?")),
        "{{RESULT}}": eval_data.get("verdict", "PENDING"),
    }

    result = template
    for placeholder, value in replacements.items():
        result = result.replace(placeholder, str(value))

    return result


# ── LLM Task Generator ─────────────────────────────────────────────────


def _call_openrouter(prompt: str, system: str = "") -> str:
    """Call OpenRouter API for LLM completion."""
    if not OPENROUTER_API_KEY:
        raise RuntimeError(
            "OPENROUTER_API_KEY not set. Set it in ~/.hermes/.env "
            "or export it in your shell."
        )

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [],
        "temperature": 0.3,
        "max_tokens": 2048,
    }
    if system:
        payload["messages"].append({"role": "system", "content": system})
    payload["messages"].append({"role": "user", "content": prompt})

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        OPENROUTER_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://github.com/nousresearch/hermes-agent",
            "X-Title": "Grand SIE Requirements Engine",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        content = body["choices"][0]["message"]["content"]
        return content
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        raise RuntimeError(
            f"OpenRouter HTTP {e.code}: {error_body[:500]}"
        ) from e
    except Exception as e:
        raise RuntimeError(f"OpenRouter call failed: {e}") from e


def generate_tasks_from_spec(spec_md: str, signal_title: str) -> str:
    """Use LLM to generate AGENTS.md task entries from a spec."""
    system_prompt = textwrap.dedent("""\
        You are a technical task-breakdown assistant for the Grand SIE autonomous
        development system. Given a project specification, you produce a list of
        concrete, actionable coding tasks suitable for an AGENTS.md file.

        Each task must follow this exact format:

        ### Task: [lowercase-kebab-id]
        **Description:** One-sentence description of what to build.
        **Success Criteria:** One testable condition that proves completion.
        **Priority:** HIGH | MEDIUM | LOW

        Rules:
        - Produce exactly 3-6 tasks.
        - Tasks must be concrete, not vague. "Set up project structure" is fine.
          "Make it good" is not.
        - Order by dependency: foundational tasks first.
        - Each task should be completable in 30-90 minutes.
        - Return ONLY the task list, no preamble or commentary.
        - Use the exact format above: ### Task: id, **Description:**, **Success Criteria:**, **Priority:**.
    """)

    user_prompt = f"""Project: {signal_title}

Specification:
{spec_md[:4000]}

Generate AGENTS.md task breakdown:
"""

    try:
        response = _call_openrouter(user_prompt, system=system_prompt)
        return response.strip()
    except RuntimeError as e:
        print(f"[WARN] LLM call failed: {e}", file=sys.stderr)
        return _fallback_tasks(signal_title)


def _fallback_tasks(title: str) -> str:
    """Generate fallback tasks when LLM is unavailable."""
    slug = title.lower().replace(" ", "-").replace("_", "-")
    return textwrap.dedent(f"""\
        ### Task: {slug}-project-setup
        **Description:** Initialize project structure with README, requirements, and entry point.
        **Success Criteria:** `python {slug}.py --help` prints usage.
        **Priority:** HIGH

        ### Task: {slug}-core-logic
        **Description:** Implement the core algorithm / business logic.
        **Success Criteria:** Core function passes unit tests with >= 80% coverage.
        **Priority:** HIGH

        ### Task: {slug}-input-validation
        **Description:** Add input validation and error handling for all user-facing entry points.
        **Success Criteria:** Malformed input produces a clear error message, no traceback.
        **Priority:** MEDIUM

        ### Task: {slug}-output-formatting
        **Description:** Format output for readability (JSON, table, or markdown).
        **Success Criteria:** Output is parseable and matches documented schema.
        **Priority:** MEDIUM

        ### Task: {slug}-tests-and-docs
        **Description:** Write unit tests and update README with usage examples.
        **Success Criteria:** `pytest` passes all tests; README has runnable examples.
        **Priority:** LOW
    """)


# ── CLI Commands ───────────────────────────────────────────────────────


def cmd_evaluate(args):
    """Evaluate BUILD signals from radar JSON."""
    input_path = "-" if getattr(args, "stdin", False) else args.input
    data = _load_json(input_path)
    result = evaluate(data)

    output = _format_evaluation(result, args.format)
    _write_output(output, args.output)

    print(
        f"[OK] Evaluated {len(result.items)} BUILD signals: "
        f"{len(result.accepted)} accepted, "
        f"{len(result.review)} review, "
        f"{len(result.rejected)} rejected",
        file=sys.stderr,
    )

    return 0 if result.accepted else 1


def cmd_spec(args):
    """Generate formal specs from evaluated JSON."""
    input_path = "-" if getattr(args, "stdin", False) else args.input
    data = _load_json(input_path)
    items = data.get("accepted", data.get("items", []))
    if not items:
        items = data.get("signals", [])
        # Filter to accepted if evaluation is embedded
        items = [
            i for i in items
            if i.get("evaluation", {}).get("verdict") == "ACCEPT"
            or i.get("recommendation", "").upper() == "BUILD"
        ]

    if not items:
        print("[ERROR] No accepted items to generate specs for", file=sys.stderr)
        return 1

    template = load_spec_template()
    specs = []

    for item in items:
        spec_md = generate_spec(item, template)
        specs.append(spec_md)

        title = item.get("title", "untitled")
        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")

        # Write individual spec file
        out_dir = args.output_dir or str(SIEGEN_DIR / "specs")
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f"{slug}-spec.md")
        with open(out_path, "w") as f:
            f.write(spec_md)
        print(f"  [spec] {out_path}", file=sys.stderr)

    # Also output concatenated
    combined = "\n\n---\n\n".join(specs)
    if args.output:
        _write_output(combined, args.output)
    else:
        print(combined)

    print(
        f"[OK] Generated {len(specs)} spec(s)",
        file=sys.stderr,
    )
    return 0


def cmd_create_tasks(args):
    """Generate AGENTS.md tasks from spec markdown."""
    input_path = "-" if getattr(args, "stdin", False) else args.input
    spec_md = _load_text(input_path)
    title_match = re.search(r"^# (.+)$", spec_md, re.MULTILINE)
    title = title_match.group(1) if title_match else "Untitled"

    tasks = generate_tasks_from_spec(spec_md, title)
    print(tasks)

    if args.output:
        _write_output(tasks, args.output)

    print(f"[OK] Generated tasks for '{title}'", file=sys.stderr)
    return 0


def cmd_pipeline(args):
    """Run the full pipeline: evaluate → spec → create-tasks."""
    # Step 1: Evaluate
    data = _load_json(args.input)
    result = evaluate(data)

    print(
        f"[Pipeline] Step 1/3 — Evaluated: "
        f"{len(result.accepted)} accepted, "
        f"{len(result.review)} review, "
        f"{len(result.rejected)} rejected",
        file=sys.stderr,
    )

    if not result.accepted:
        print("[Pipeline] No items passed threshold. Stopping.", file=sys.stderr)
        return 1

    # Step 2: Spec
    template = load_spec_template()
    specs = []
    out_dir = args.output_dir or str(SIEGEN_DIR / "pipeline-output")
    os.makedirs(out_dir, exist_ok=True)

    for item in result.accepted:
        spec_md = generate_spec(item, template)
        specs.append(spec_md)

        title = item.get("title", "untitled")
        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
        spec_path = os.path.join(out_dir, f"{slug}-spec.md")
        with open(spec_path, "w") as f:
            f.write(spec_md)
        print(f"  [pipeline:spec] {spec_path}", file=sys.stderr)

    # Save evaluation result
    eval_path = os.path.join(out_dir, "evaluation.json")
    with open(eval_path, "w") as f:
        json.dump(asdict(result), f, indent=2, default=str)
    print(f"  [pipeline:eval] {eval_path}", file=sys.stderr)

    print(
        f"[Pipeline] Step 2/3 — Generated {len(specs)} spec(s)",
        file=sys.stderr,
    )

    # Step 3: Create tasks for each spec
    all_tasks = []
    for item, spec_md in zip(result.accepted, specs):
        title = item.get("title", "Untitled")
        tasks = generate_tasks_from_spec(spec_md, title)
        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
        tasks_path = os.path.join(out_dir, f"{slug}-tasks.md")
        with open(tasks_path, "w") as f:
            f.write(f"# Tasks for: {title}\n\n{tasks}\n")
        all_tasks.append(f"## {title}\n\n{tasks}")
        print(f"  [pipeline:tasks] {tasks_path}", file=sys.stderr)

    # Write combined AGENTS.md
    combined_tasks_path = os.path.join(out_dir, "AGENTS.md")
    combined_content = (
        f"# AGENTS.md — Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n\n"
        + "\n\n---\n\n".join(all_tasks)
        + "\n"
    )
    with open(combined_tasks_path, "w") as f:
        f.write(combined_content)

    print(
        f"[Pipeline] Step 3/3 — Generated tasks for {len(result.accepted)} item(s)",
        file=sys.stderr,
    )
    print(f"[Pipeline] Output directory: {out_dir}", file=sys.stderr)
    print(f"[Pipeline] Combined AGENTS.md: {combined_tasks_path}", file=sys.stderr)

    # Print summary to stdout
    summary = {
        "date": result.date,
        "accepted_count": len(result.accepted),
        "review_count": len(result.review),
        "rejected_count": len(result.rejected),
        "output_dir": out_dir,
        "accepted_titles": [
            item.get("title") for item in result.accepted
        ],
    }
    print(json.dumps(summary, indent=2))

    return 0


# ── Helpers ────────────────────────────────────────────────────────────


def _load_json(path: str) -> dict:
    """Load JSON from file path or stdin ('-' or --stdin)."""
    if path in ("-", "--stdin"):
        return json.load(sys.stdin)
    with open(path) as f:
        return json.load(f)


def _load_text(path: str) -> str:
    """Load text from file path or stdin."""
    if path in ("-", "--stdin"):
        return sys.stdin.read()
    with open(path) as f:
        return f.read()


def _write_output(content: str, path: Optional[str]):
    """Write output to file or stdout."""
    if path and path != "-":
        with open(path, "w") as f:
            f.write(content)
    elif path == "-":
        print(content)


def _format_evaluation(result: EvaluationResult, fmt: str) -> str:
    """Format evaluation result."""
    if fmt == "json":
        return json.dumps(asdict(result), indent=2, default=str)

    # Pretty table format
    lines = [
        f"Requirements Engine — Evaluation ({result.date})",
        "=" * 60,
        "",
    ]

    if result.accepted:
        lines.append(f"## ACCEPTED ({len(result.accepted)} items)")
        for item in result.accepted:
            ev = item["evaluation"]
            lines.append(
                f"  ✅ {item['title']} [{item['domain']}] "
                f"— Score: {ev['combined_score']}/20"
            )
        lines.append("")

    if result.review:
        lines.append(f"## REVIEW ({len(result.review)} items)")
        for item in result.review:
            ev = item["evaluation"]
            lines.append(
                f"  ⚠️  {item['title']} [{item['domain']}] "
                f"— Score: {ev['combined_score']}/20"
            )
        lines.append("")

    if result.rejected:
        lines.append(f"## REJECTED ({len(result.rejected)} items)")
        for item in result.rejected:
            ev = item["evaluation"]
            lines.append(
                f"  ❌ {item['title']} [{item['domain']}] "
                f"— Score: {ev['combined_score']}/20"
            )
        lines.append("")

    return "\n".join(lines)


# ── Main ───────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Requirements Engine — Grand SIE Phase 2",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              requirements-engine.py evaluate radar-output.json
              requirements-engine.py spec evaluation.json -o specs/
              requirements-engine.py create-tasks spec.md
              requirements-engine.py pipeline radar-output.json
              cat radar.json | requirements-engine.py pipeline --stdin
        """),
    )
    sub = parser.add_subparsers(dest="command", help="Command to run")

    # evaluate
    p_eval = sub.add_parser("evaluate", help="Score BUILD items from radar JSON")
    p_eval.add_argument("input", help="Radar JSON file path (use '-' or '--stdin' for stdin)")
    p_eval.add_argument("--stdin", action="store_true", help="Read radar JSON from stdin")
    p_eval.add_argument("--format", choices=["pretty", "json"], default="pretty",
                        help="Output format (default: pretty)")
    p_eval.add_argument("-o", "--output", help="Write output to file")

    # spec
    p_spec = sub.add_parser("spec", help="Generate formal specs from evaluated JSON")
    p_spec.add_argument("input", help="Evaluated JSON or radar JSON file path")
    p_spec.add_argument("--stdin", action="store_true", help="Read input from stdin")
    p_spec.add_argument("-o", "--output", help="Write combined spec to file")
    p_spec.add_argument("--output-dir", help="Directory for individual spec files")

    # create-tasks
    p_tasks = sub.add_parser("create-tasks", help="Generate AGENTS.md tasks from spec")
    p_tasks.add_argument("input", help="Spec markdown file path")
    p_tasks.add_argument("--stdin", action="store_true", help="Read spec from stdin")
    p_tasks.add_argument("-o", "--output", help="Write tasks to file")

    # pipeline
    p_pipe = sub.add_parser("pipeline", help="Run evaluate → spec → create-tasks")
    p_pipe.add_argument("input", help="Radar JSON file path")
    p_pipe.add_argument("--stdin", action="store_true", help="Read radar JSON from stdin")
    p_pipe.add_argument("--output-dir", help="Output directory for all artifacts")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 2

    # Handle --stdin for pipeline
    if args.command == "pipeline" and getattr(args, "stdin", False):
        args.input = "-"

    try:
        if args.command == "evaluate":
            return cmd_evaluate(args)
        elif args.command == "spec":
            return cmd_spec(args)
        elif args.command == "create-tasks":
            return cmd_create_tasks(args)
        elif args.command == "pipeline":
            return cmd_pipeline(args)
        else:
            parser.print_help()
            return 2
    except FileNotFoundError as e:
        print(f"[ERROR] File not found: {e}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON: {e}", file=sys.stderr)
        return 2
    except RuntimeError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\n[ABORT] Interrupted", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
