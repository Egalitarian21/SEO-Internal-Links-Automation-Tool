from urllib.parse import urlsplit, urlunsplit


def normalize_url(raw_url: str) -> str:
    value = (raw_url or "").strip()
    if not value:
        return ""

    parts = urlsplit(value)
    scheme = parts.scheme.lower() or "https"
    netloc = parts.netloc.lower()
    path = parts.path or "/"
    query = parts.query
    fragment = ""
    normalized = urlunsplit((scheme, netloc, path, query, fragment))
    if normalized.endswith("/") and path != "/":
        normalized = normalized[:-1]
    return normalized


def is_probably_url(value: str) -> bool:
    parts = urlsplit(value)
    return bool(parts.scheme and parts.netloc)

