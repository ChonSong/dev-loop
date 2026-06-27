#!/usr/bin/env python3
"""
DevKnowledge Store — Lingxi Phase 1

Reads checkpoint.json (completed tasks with SHAs), extracts git diffs,
embeds them into ChromaDB for semantic retrieval of similar past fixes.

Usage:
    python3 dev-knowledge-store.py --build    # Build/rebuild the knowledge store
    python3 dev-knowledge-store.py --query "<task description>"  # Find similar past fixes
    python3 dev-knowledge-store.py --stats    # Show store statistics
"""
import argparse, json, subprocess, sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# Paths
REPO_ROOT = Path.home() / "repos"
MONOREPO = REPO_ROOT / "autonomous-dev-system"
KNOWLEDGE_DIR = MONOREPO / "sie" / "knowledge-store"
TRAJECTORY_DIR = MONOREPO / "sie" / "trajectories"

# Projects to index
PROJECTS = [
    {"name": "gto-wizard-clone", "repo": REPO_ROOT / "gto-wizard-clone", "checkpoint": REPO_ROOT / "gto-wizard-clone" / ".checkpoint.json"},
    {"name": "polytopia-clone", "repo": REPO_ROOT / "polytopia-clone", "checkpoint": REPO_ROOT / "polytopia-clone" / ".checkpoint.json"},
]


def load_checkpoints() -> list[dict]:
    """Load completed tasks from all project checkpoints."""
    all_tasks = []
    for project in PROJECTS:
        cp_path = project["checkpoint"]
        if not cp_path.exists():
            print(f"  Skipping {project['name']}: no checkpoint at {cp_path}")
            continue
        with open(cp_path) as f:
            data = json.load(f)
        tasks = [t for t in data.get("completed", []) if t.get("sha") and t["sha"] not in ("inferred-done", "partial")]
        for t in tasks:
            t["_project"] = project["name"]
            t["_repo"] = project["repo"]
        all_tasks.extend(tasks)
    return all_tasks


def get_diff(repo: Path, sha: str) -> Optional[str]:
    """Get the git diff for a specific commit SHA."""
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo), "show", "--format=", sha],
            capture_output=True, text=True, timeout=10
        )
        diff = proc.stdout.strip()
        return diff if diff else None
    except Exception as e:
        print(f"  Warning: could not get diff for {sha}: {e}", file=sys.stderr)
        return None


def get_changed_files(repo: Path, sha: str) -> list[str]:
    """Get list of files changed in a commit."""
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo), "diff-tree", "--no-commit-id", "--name-only", "-r", sha],
            capture_output=True, text=True, timeout=5
        )
        return [f for f in proc.stdout.strip().split("\n") if f]
    except Exception:
        return []


def build_knowledge_store():
    """Build ChromaDB knowledge store from checkpoint history."""
    from chromadb import PersistentClient
    from chromadb.utils import embedding_functions

    tasks = load_checkpoints()
    print(f"Found {len(tasks)} completed tasks with SHAs")

    # Setup embedding function (all-MiniLM-L6-v2 — small, fast, local)
    ef = embedding_functions.DefaultEmbeddingFunction()

    # Setup ChromaDB
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    client = PersistentClient(path=str(KNOWLEDGE_DIR))

    # Delete existing collection if rebuilding
    try:
        client.delete_collection("dev_knowledge")
        print("Deleted existing knowledge store")
    except Exception:
        pass

    collection = client.create_collection(
        name="dev_knowledge",
        embedding_function=ef,
        metadata={"description": "Development knowledge — extracted from checkpoint history across all projects"}
    )

    ids = []
    documents = []
    metadatas = []

    for i, task in enumerate(tasks):
        sha = task["sha"]
        summary = task.get("summary", "")
        task_id = task.get("task", sha)
        date = task.get("date", "")
        project = task.get("_project", "unknown")
        repo = task["_repo"]

        diff = get_diff(repo, sha)
        if not diff:
            continue

        files = get_changed_files(repo, sha)
        changed_files = ", ".join(files[:5])
        if len(files) > 5:
            changed_files += f" (+{len(files) - 5} more)"

        # Document = task description + summary for semantic matching
        doc = f"[{project}] Task: {task_id}\nSummary: {summary}\nFiles changed: {changed_files}\nDate: {date}"

        ids.append(f"{project}-{sha[:8]}")
        documents.append(doc)
        metadatas.append({
            "task_id": task_id,
            "project": project,
            "sha": sha,
            "date": date,
            "summary": summary,
            "files": changed_files,
            "diff_snippet": diff[:2000],  # First 2000 chars of diff for preview
            "repo": project,
        })

        print(f"  [{i+1}/{len(tasks)}] {task_id} ({sha[:8]}) — {len(diff)} bytes diff, {len(files)} files")

    if ids:
        collection.add(ids=ids, documents=documents, metadatas=metadatas)
        print(f"\nBuilt knowledge store: {len(ids)} entries from checkpoint history")

    # Phase 2: Index trajectory files (richer format with guidance)
    traj_count = index_trajectories(collection)
    if traj_count:
        print(f"Indexed {traj_count} trajectories from {TRAJECTORY_DIR}")
    print(f"Total: {collection.count()} entries in {KNOWLEDGE_DIR}")
    if not ids and not traj_count:
        print("No entries added")


def index_trajectories(collection) -> int:
    """Index trajectory JSON files into the knowledge store."""
    if not TRAJECTORY_DIR.exists():
        return 0

    count = 0
    for traj_path in sorted(TRAJECTORY_DIR.glob("*.json")):
        try:
            data = json.loads(traj_path.read_text())
        except json.JSONDecodeError:
            continue

        project = data.get("project", "unknown")
        task_id = data.get("task_id", "")
        verdict = data.get("verdict", "")
        decoder = data.get("phases", {}).get("decoder", {})
        guidance = data.get("guidance", {})

        # Build rich document from trajectory phases
        doc_parts = [f"[{project}] Task: {task_id} (verdict: {verdict})"]
        if decoder.get("problem_statement"):
            doc_parts.append(f"Problem: {decoder['problem_statement']}")

        # Add guidance if available
        tips = []
        for key in ["diagnostic_tip", "strategy", "pitfall", "regression_risk"]:
            val = guidance.get(key, "")
            if val:
                tips.append(f"{key.replace('_', ' ')}: {val}")
        if tips:
            doc_parts.append(" | ".join(tips))

        doc = "\n".join(doc_parts)

        traj_id = f"traj-{project}-{task_id}"[:64]
        meta = {
            "task_id": task_id,
            "project": project,
            "date": data.get("timestamp", ""),
            "verdict": verdict,
            "sha": data.get("phases", {}).get("solver", {}).get("sha", ""),
            "summary": decoder.get("problem_statement", ""),
            "files": ", ".join(decoder.get("relevant_files", [])[:5]),
            "guidance": guidance.get("strategy", "") + " | " +
                        guidance.get("diagnostic_tip", "") + " | " +
                        guidance.get("pitfall", "") + " | " +
                        guidance.get("regression_risk", ""),
            "diff_snippet": data.get("phases", {}).get("solver", {}).get("full_output", "")[:2000],
            "repo": project,
            "source": "trajectory",
        }

        # Check if already indexed
        existing = collection.get([traj_id])
        if existing["ids"]:
            continue  # Skip duplicates

        collection.add(ids=[traj_id], documents=[doc], metadatas=[meta])
        count += 1

    return count


def query_knowledge_store(query: str, n_results: int = 3):
    """Query the knowledge store for similar past fixes."""
    from chromadb import PersistentClient
    from chromadb.utils import embedding_functions

    if not KNOWLEDGE_DIR.exists():
        print("Knowledge store not built yet. Run --build first.", file=sys.stderr)
        sys.exit(1)

    ef = embedding_functions.DefaultEmbeddingFunction()
    client = PersistentClient(path=str(KNOWLEDGE_DIR))
    collection = client.get_collection("dev_knowledge", embedding_function=ef)

    results = collection.query(query_texts=[query], n_results=n_results)

    print(f"\nQuery: \"{query}\"\n")
    for i, (doc_id, doc, meta, distance) in enumerate(zip(
        results["ids"][0], results["documents"][0],
        results["metadatas"][0], results["distances"][0]
    )):
        similarity = 1 - distance
        print(f"  #{i+1} [{similarity:.2f}] {meta.get('task_id')} ({meta.get('sha','')[:8]})")
        print(f"        {meta.get('summary', '')[:100]}")
        print(f"        Files: {meta.get('files', '')}")
        if meta.get("diff_snippet"):
            # Show first few lines of diff
            lines = meta["diff_snippet"].split("\n")[:5]
            for line in lines:
                print(f"        {line[:90]}")
            if len(lines) > 5:
                print(f"        ...")
        print()


def show_stats():
    """Show knowledge store statistics."""
    from chromadb import PersistentClient

    if not KNOWLEDGE_DIR.exists():
        print("Knowledge store not built yet. Run --build first.")
        return

    client = PersistentClient(path=str(KNOWLEDGE_DIR))
    try:
        collection = client.get_collection("dev_knowledge")
        count = collection.count()
        print(f"Knowledge store: {count} entries")
        print(f"Location: {KNOWLEDGE_DIR}")
    except Exception:
        print("No dev_knowledge collection found. Run --build first.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DevKnowledge Store")
    parser.add_argument("--build", action="store_true", help="Build/re-build the knowledge store")
    parser.add_argument("--query", type=str, help="Query for similar past fixes")
    parser.add_argument("--stats", action="store_true", help="Show store statistics")
    args = parser.parse_args()

    if args.build:
        build_knowledge_store()
    elif args.query:
        query_knowledge_store(args.query)
    elif args.stats:
        show_stats()
    else:
        parser.print_help()
