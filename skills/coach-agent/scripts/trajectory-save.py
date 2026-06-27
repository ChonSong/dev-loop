#!/usr/bin/env python3
"""
Trajectory Save Tool — Lingxi Phase 4

Saves a completed repair trajectory (Decoder → Mapper → Solver → Coach)
into the DevKnowledge store for future retrieval by the Problem Decoder.

Usage:
    python3 trajectory-save.py --task <task-id> --project <name> \
        --decoder analysis.txt --mapper plan.txt --solver summary.txt \
        [--coach verdict.json] [--guidance guidance.txt]
"""

import argparse, json, sys
from pathlib import Path
from datetime import datetime, timezone


# Paths
REPO_ROOT = Path.home() / "repos"
MONOREPO = REPO_ROOT / "autonomous-dev-system"
TRAJECTORY_DIR = MONOREPO / "sie" / "trajectories"
KNOWLEDGE_DIR = MONOREPO / "sie" / "knowledge-store"


def save_trajectory(
    project: str,
    task_id: str,
    decoder: str,
    mapper: str,
    solver: str,
    coach: str = "",
    guidance: str = "",
    verdict: str = "",
) -> Path:
    """Save a full trajectory to disk and return the path."""
    TRAJECTORY_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).isoformat()
    slug = task_id.replace("/", "-").replace(" ", "-")[:60]

    # Parse decoder XML for structured fields
    problem_statement = _extract_xml(decoder, "problem_statement")
    relevant_files = _extract_xml_list(decoder, "relevant_files")
    past_patterns = _extract_xml_list(decoder, "past_patterns")
    expected_behavior = _extract_xml(decoder, "expected_behavior")

    # Parse mapper plan
    approach = _extract_section(mapper, "General approach")
    reproduction = _extract_section(mapper, "Reproduction")
    files_to_change = _parse_files_to_change(mapper)
    edge_cases = _extract_section(mapper, "Edge cases")
    verification = _extract_section(mapper, "Verification")

    # Parse solver summary
    files_changed_actual = _extract_section(solver, "files_changed")
    test_results = _extract_section(solver, "test_results")
    live_verification = _extract_section(solver, "live_verification")
    issues = _extract_section(solver, "issues")

    # Build trajectory JSON
    trajectory = {
        "version": 1,
        "project": project,
        "task_id": task_id,
        "timestamp": timestamp,
        "verdict": verdict,
        "phases": {
            "decoder": {
                "problem_statement": problem_statement,
                "relevant_files": relevant_files,
                "past_patterns_used": past_patterns,
                "expected_behavior": expected_behavior,
                "full_output": decoder,
            },
            "mapper": {
                "approach": approach,
                "files_to_change": files_to_change,
                "reproduction": reproduction,
                "edge_cases": edge_cases,
                "verification": verification,
                "full_output": mapper,
            },
            "solver": {
                "files_changed_actual": files_changed_actual,
                "test_results": test_results,
                "live_verification": live_verification,
                "issues": issues,
                "full_output": solver,
            },
        },
        "guidance": {
            "diagnostic_tip": "",
            "pitfall": "",
            "strategy": approach,
            "regression_risk": "",
            "raw": guidance,
        },
    }

    # If coach data provided, add it
    if coach:
        try:
            coach_data = json.loads(coach)
            trajectory["phases"]["coach"] = coach_data
        except json.JSONDecodeError:
            trajectory["phases"]["coach"] = {"verdict": verdict, "raw": coach}

    # Parse guidance hints if provided
    if guidance:
        trajectory["guidance"]["diagnostic_tip"] = _extract_section(guidance, "diagnostic_tip") or ""
        trajectory["guidance"]["pitfall"] = _extract_section(guidance, "pitfall") or ""
        trajectory["guidance"]["regression_risk"] = _extract_section(guidance, "regression_risk") or ""

    # Save
    out_path = TRAJECTORY_DIR / f"{project}-{slug}-{timestamp[:10]}.json"
    out_path.write_text(json.dumps(trajectory, indent=2))
    print(f"Trajectory saved: {out_path}")
    return out_path


def _extract_xml(text: str, tag: str) -> str:
    """Extract content from <tag>...</tag> XML block."""
    import re
    pattern = rf"<{tag}>\s*(.*?)\s*</{tag}>"
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else ""


def _extract_xml_list(text: str, tag: str) -> list[str]:
    """Extract list items from XML block (lines starting with -)."""
    content = _extract_xml(text, tag)
    if not content:
        return []
    return [line.strip("- *").strip() for line in content.split("\n")
            if line.strip().startswith("-")]


def _extract_section(text: str, heading: str) -> str:
    """Extract content under a markdown heading."""
    import re
    # Match "## heading" or "### heading" blocks, capture until next ##
    pattern = rf"#{{2,3}}\s+{re.escape(heading)}.*?\n(.*?)(?=\n#{{2,3}}\s|\Z)"
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else ""


def _parse_files_to_change(mapper_text: str) -> list[str]:
    """Parse out file paths from the mapper's plan."""
    import re
    files = set()
    # Match "### path/to/file.tsx" pattern
    for match in re.finditer(r"###\s+(apps/\S+)", mapper_text):
        files.add(match.group(1))
    return sorted(files)


def inject_trajectory(project: str, task_id: str, n_results: int = 3) -> str:
    """
    Query ChromaDB for similar past trajectories.
    Returns formatted text for injection into the Decoder prompt.
    """
    from chromadb import PersistentClient
    from chromadb.utils import embedding_functions

    if not KNOWLEDGE_DIR.exists():
        return ""

    ef = embedding_functions.DefaultEmbeddingFunction()
    client = PersistentClient(path=str(KNOWLEDGE_DIR))

    try:
        collection = client.get_collection("dev_knowledge", embedding_function=ef)
    except Exception:
        return ""

    # Query with project filter
    results = collection.query(
        query_texts=[task_id],
        n_results=n_results,
        where={"project": project} if project else None,
    )

    if not results["ids"] or not results["ids"][0]:
        return ""

    out = []
    for i, (doc_id, meta) in enumerate(zip(results["ids"][0], results["metadatas"][0])):
        guidance = meta.get("guidance", "")
        if not guidance:
            continue
        out.append(f"### Similar past fix #{i+1}: {meta.get('task_id', doc_id)}")
        out.append(f"Date: {meta.get('date', 'unknown')}")
        out.append(guidance)
        out.append("")

    return "\n".join(out) if out else ""


def main():
    parser = argparse.ArgumentParser(description="Trajectory Save Tool")
    sub = parser.add_subparsers(dest="command")

    save_parser = sub.add_parser("save", help="Save a completed trajectory")
    save_parser.add_argument("--task", required=True, help="Task ID")
    save_parser.add_argument("--project", required=True, help="Project name")
    save_parser.add_argument("--decoder", help="Decoder analysis file")
    save_parser.add_argument("--mapper", help="Mapper plan file")
    save_parser.add_argument("--solver", help="Solver summary file")
    save_parser.add_argument("--coach", help="Coach verdict JSON file")
    save_parser.add_argument("--guidance", help="Distilled guidance text")
    save_parser.add_argument("--verdict", help="Coach verdict (APPROVE/FIX/REVERT)")

    retrieve_parser = sub.add_parser("retrieve", help="Query trajectories")
    retrieve_parser.add_argument("--task", required=True, help="Task ID or description")
    retrieve_parser.add_argument("--project", help="Filter by project")
    retrieve_parser.add_argument("--n", type=int, default=3, help="Number of results")

    args = parser.parse_args()

    if args.command == "save":
        decoder = Path(args.decoder).read_text() if args.decoder else ""
        mapper = Path(args.mapper).read_text() if args.mapper else ""
        solver = Path(args.solver).read_text() if args.solver else ""
        coach = Path(args.coach).read_text() if args.coach else ""
        guidance = Path(args.guidance).read_text() if args.guidance else ""
        save_trajectory(args.project, args.task, decoder, mapper, solver, coach, guidance, args.verdict or "")

    elif args.command == "retrieve":
        result = inject_trajectory(args.project or "", args.task, args.n)
        if result:
            print(result)
        else:
            print("No similar trajectories found.")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
