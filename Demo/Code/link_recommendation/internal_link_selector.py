from utils.text_utils import normalize_url


def select_internal_links(candidates: list[dict], max_links: int = 8) -> list[dict]:
    """Select unique internal link candidates by normalized target URL."""
    selected: list[dict] = []
    seen: set[str] = set()
    for candidate in candidates:
        target_url = normalize_url(str(candidate.get("target_url", "")))
        if target_url and target_url not in seen:
            seen.add(target_url)
            selected.append({**candidate, "target_url": target_url})
        if len(selected) >= max_links:
            break
    return selected
