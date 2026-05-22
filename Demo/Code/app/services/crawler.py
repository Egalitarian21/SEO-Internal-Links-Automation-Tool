import re
from typing import Any

import httpx
from bs4 import BeautifulSoup

from app.config import get_settings
from app.errors import AppError

try:
    import trafilatura
except Exception:  # pragma: no cover
    trafilatura = None


class CrawlerService:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def fetch_html(self, url: str) -> str:
        headers = {"User-Agent": self.settings.crawler_user_agent}
        timeout = httpx.Timeout(self.settings.crawler_timeout)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, headers=headers) as client:
            response = await client.get(url)
            if response.status_code >= 400:
                raise AppError("URL_FETCH_FAILED", f"HTTP {response.status_code} for {url}")
            return response.text

    def _extract_body_text(self, html: str, soup: BeautifulSoup) -> str:
        if trafilatura is not None:
            text = trafilatura.extract(html, include_comments=False, include_links=False)
            if text:
                return text
        return re.sub(r"\s+", " ", soup.get_text(" ", strip=True))

    def parse(self, url: str, html: str) -> dict[str, Any]:
        soup = BeautifulSoup(html, "html.parser")
        title = ""
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
        if not title:
            h1 = soup.find("h1")
            title = h1.get_text(" ", strip=True) if h1 else url

        description = ""
        meta = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
        if meta and meta.get("content"):
            description = str(meta["content"]).strip()

        hierarchy: list[dict[str, Any]] = []
        for level in range(1, 7):
            for node in soup.find_all(f"h{level}"):
                text = node.get_text(" ", strip=True)
                if text:
                    hierarchy.append({"level": level, "text": text})

        body_text = self._extract_body_text(html, soup)
        return {
            "url": url,
            "title": title[:200],
            "description": description[:500],
            "h_hierarchy": hierarchy,
            "body_text": body_text,
        }

    async def crawl(self, url: str) -> dict[str, Any]:
        html = await self.fetch_html(url)
        return self.parse(url, html)

