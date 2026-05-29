import re
from urllib.parse import urlsplit, urlunsplit


def normalize_whitespace(value: str) -> str:
    """Collapse repeated whitespace into single spaces."""
    return re.sub(r"\s+", " ", value or "").strip()


def normalize_url(raw_url: str) -> str:
    """Normalize URL scheme, host casing, fragment, and trailing slash."""
    value = (raw_url or "").strip()
    if not value:
        return ""
    parts = urlsplit(value)
    scheme = parts.scheme.lower() or "https"
    netloc = parts.netloc.lower()
    path = parts.path or "/"
    normalized = urlunsplit((scheme, netloc, path, parts.query, ""))
    if normalized.endswith("/") and path != "/":
        normalized = normalized[:-1]
    return normalized


def safe_name(value: str) -> str:
    """Convert user-provided names into filesystem-safe names."""
    cleaned = re.sub(r'[\/\\:\*\?"<>\|]+', "-", value or "").strip(" .")
    cleaned = re.sub(r"-{2,}", "-", cleaned)
    return cleaned or "brand_name"
