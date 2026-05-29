from utils.text_utils import normalize_url


def select_external_links(candidates: list[dict], whitelist: list[str], max_links: int = 3) -> list[dict]:
    """Select external links whose hosts appear in the configured whitelist."""
    selected: list[dict] = []
    allowed = {item.lower() for item in whitelist}
    for candidate in candidates:
        target_url = normalize_url(str(candidate.get("target_url", "")))
        if not target_url:
            continue
        if any(host in target_url.lower() for host in allowed):
            selected.append({**candidate, "target_url": target_url})
        if len(selected) >= max_links:
            break
    return selected
