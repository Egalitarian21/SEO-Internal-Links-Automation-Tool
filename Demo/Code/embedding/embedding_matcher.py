from math import sqrt


def cosine_similarity(left: list[float], right: list[float]) -> float:
    """Compute cosine similarity for two vectors."""
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = sqrt(sum(a * a for a in left))
    right_norm = sqrt(sum(b * b for b in right))
    if not left_norm or not right_norm:
        return 0.0
    return dot / (left_norm * right_norm)


def rank_matches(query_embedding: list[float], candidates: list[dict], limit: int = 10) -> list[dict]:
    """Rank candidate dictionaries that contain an `embedding` key."""
    scored = [
        {**candidate, "score": cosine_similarity(query_embedding, candidate.get("embedding", []))}
        for candidate in candidates
    ]
    return sorted(scored, key=lambda item: item["score"], reverse=True)[:limit]
