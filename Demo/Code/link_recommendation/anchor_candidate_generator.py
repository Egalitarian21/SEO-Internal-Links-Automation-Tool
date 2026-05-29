import re


def generate_anchor_candidates(text: str, min_length: int = 2) -> list[str]:
    """Generate simple phrase candidates from blog text."""
    candidates = re.findall(r"[A-Za-z][A-Za-z0-9' -]{1,80}", text or "")
    cleaned = [" ".join(candidate.split()) for candidate in candidates]
    return list(dict.fromkeys(item for item in cleaned if len(item) >= min_length))
