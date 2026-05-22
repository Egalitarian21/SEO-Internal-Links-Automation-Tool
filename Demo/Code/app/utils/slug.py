import re
from urllib.parse import urlparse

from app.errors import AppError

INVALID_PATH_CHARS_PATTERN = re.compile(r'[\/\\:\*\?"<>\|]')
MULTI_DASH_PATTERN = re.compile(r"-{2,}")


def sanitize_customer_name(customer: str) -> str:
    value = (customer or "").strip()
    value = INVALID_PATH_CHARS_PATTERN.sub("-", value)
    value = value.strip(" .")
    value = MULTI_DASH_PATTERN.sub("-", value)
    if not value:
        raise AppError("INVALID_CUSTOMER_NAME", "Customer name is empty after sanitization.")
    return value


def slugify_text(value: str, max_len: int = 80) -> str:
    text = (value or "").strip().lower()
    text = text.replace("_", "-")
    text = re.sub(r"[^0-9a-z\u4e00-\u9fff\-]+", "-", text)
    text = MULTI_DASH_PATTERN.sub("-", text).strip("-")
    if not text:
        text = "untitled"
    return text[:max_len].rstrip("-")


def slugify_url(url: str, max_len: int = 80) -> str:
    parsed = urlparse(url)
    candidate = f"{parsed.netloc}{parsed.path}".strip("/")
    if not candidate:
        candidate = url
    return slugify_text(candidate, max_len=max_len)

