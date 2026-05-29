from pathlib import Path

from utils.text_utils import normalize_url


def dedupe_urls(urls: list[str]) -> list[str]:
    """Normalize URLs and preserve first-seen order."""
    seen: set[str] = set()
    result: list[str] = []
    for raw_url in urls:
        url = normalize_url(raw_url)
        if url and url not in seen:
            seen.add(url)
            result.append(url)
    return result


def read_url_queue(path: str | Path) -> list[str]:
    """Read a plain-text URL queue, ignoring blank lines and comments."""
    queue_path = Path(path)
    if not queue_path.exists():
        return []
    urls = [
        line.strip().removeprefix("- ").strip()
        for line in queue_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    return dedupe_urls(urls)


def write_url_queue(path: str | Path, urls: list[str]) -> Path:
    """Write a deduplicated URL queue to disk."""
    queue_path = Path(path)
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    queue_path.write_text("\n".join(dedupe_urls(urls)) + "\n", encoding="utf-8")
    return queue_path
