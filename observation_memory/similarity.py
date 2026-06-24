"""Jaccard similarity for observation dedup.

Mirrors agent-qa's similarity.ts: tokenized, case-normalized, punctuation-stripped.
Three-way comparison maximizes recall: title, content, and title+content.
"""

import re


def tokenize(text: str) -> set[str]:
    """Tokenize text: lowercase, strip punctuation, split on whitespace."""
    cleaned = re.sub(r"[^\w\s]", " ", text.lower())
    words = cleaned.split()
    return set(words)


def jaccard_similarity(a: str, b: str) -> float:
    """Jaccard similarity between two strings."""
    set_a = tokenize(a)
    set_b = tokenize(b)

    if not set_a or not set_b:
        return 0.0

    intersection = len(set_a & set_b)
    union = len(set_a | set_b)

    if union == 0:
        return 0.0

    return intersection / union


def find_similar(
    query: str,
    observations: list[dict],
    threshold: float = 0.85,
) -> list[dict]:
    """Find observations similar to query above threshold.

    Each observation dict must have: id, title, content, trust.
    Returns sorted by similarity descending.
    """
    if not observations:
        return []

    results = []
    for obs in observations:
        similarity = max(
            jaccard_similarity(query, obs["title"]),
            jaccard_similarity(query, obs["content"]),
            jaccard_similarity(query, f"{obs['title']} {obs['content']}"),
        )
        if similarity >= threshold:
            results.append({**obs, "similarity": similarity})

    results.sort(key=lambda x: x["similarity"], reverse=True)
    return results
