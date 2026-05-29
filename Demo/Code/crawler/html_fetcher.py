import httpx


def fetch_html(url: str, timeout_seconds: int = 30, user_agent: str = "InternalLinkTool/0.1") -> str:
    """Fetch HTML for a URL using a small synchronous HTTP client."""
    headers = {"User-Agent": user_agent}
    response = httpx.get(url, timeout=timeout_seconds, follow_redirects=True, headers=headers)
    response.raise_for_status()
    return response.text
