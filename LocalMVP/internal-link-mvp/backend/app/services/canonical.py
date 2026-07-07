import hashlib
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from markdown_it import MarkdownIt

TRACKING_PARAMS = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "fbclid", "gclid"}


def canonicalize_url(url: str) -> str:
    raw = url.strip()
    if not re.match(r"^https?://", raw, re.I):
        raw = f"https://{raw}"

    parts = urlsplit(raw)
    scheme = parts.scheme or "https"
    host = parts.netloc.lower()
    path = parts.path or "/"

    product_match = re.match(r"^/collections/[^/]+/products/([^/?#]+)", path)
    if product_match:
        path = f"/products/{product_match.group(1)}"

    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")

    query_items = [(key, value) for key, value in parse_qsl(parts.query, keep_blank_values=True) if key.lower() not in TRACKING_PARAMS]
    query = urlencode(query_items)

    return urlunsplit((scheme, host, path, query, ""))


def content_hash(content: str | None) -> str:
    return hashlib.sha256((content or "").encode("utf-8")).hexdigest()


def looks_like_markdown(content: str | None) -> bool:
    if not content:
        return False
    if re.search(r"<(p|h1|h2|div|article|ul|ol|li|a)\b", content, re.I):
        return False
    return bool(re.search(r"(^#{1,6}\s|\[[^\]]+\]\([^)]+\)|^\s*[-*]\s+)", content, re.M))


def normalize_raw_content(content: str | None) -> str | None:
    if not content:
        return content
    if looks_like_markdown(content):
        return MarkdownIt().render(content)
    return content
