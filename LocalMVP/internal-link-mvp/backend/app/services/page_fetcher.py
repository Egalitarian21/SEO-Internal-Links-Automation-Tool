from dataclasses import dataclass
from urllib.parse import urlsplit

import httpx
from bs4 import BeautifulSoup

from app.schemas.page import PageInput

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"


@dataclass
class FetchedPage:
    page: PageInput | None
    reason: str | None = None


def infer_page_type(url: str) -> str | None:
    path = urlsplit(url.strip()).path.lower()
    segments = [segment for segment in path.split("/") if segment]

    if "products" in segments:
        return "product"
    if "blogs" in segments:
        return "blog"
    if "collections" in segments:
        return "collection"
    return None


def fetch_url_as_page_input(url: str, client: httpx.Client | None = None) -> FetchedPage:
    cleaned_url = url.strip()
    if not cleaned_url:
        return FetchedPage(page=None, reason="URL 为空。")

    page_type = infer_page_type(cleaned_url)
    if not page_type:
        return FetchedPage(page=None, reason="无法从 URL 路径判断页面类型。")

    owns_client = client is None
    active_client = client or httpx.Client(
        follow_redirects=True,
        timeout=8,
        headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"},
    )

    try:
        response = active_client.get(cleaned_url)
    except httpx.HTTPError as exc:
        return FetchedPage(page=None, reason=f"抓取失败：{exc}")
    finally:
        if owns_client:
            active_client.close()

    if response.status_code < 200 or response.status_code >= 300:
        return FetchedPage(page=None, reason=f"抓取失败，HTTP 状态码 {response.status_code}。")

    page = parse_html_to_page_input(cleaned_url, page_type, response.text)
    if not page.title:
        return FetchedPage(page=None, reason="未解析到页面标题。")
    return FetchedPage(page=page)


def parse_html_to_page_input(url: str, page_type: str, html: str) -> PageInput:
    soup = BeautifulSoup(html, "html.parser")
    title_tag = soup.find("title")
    meta_title = normalize_text(title_tag.get_text(" ", strip=True) if title_tag else None)
    og_title = get_meta_content(soup, "property", "og:title")
    h1 = first_text(soup, "h1")
    title = first_present(meta_title, og_title, h1, url)
    meta_description = first_present(
        get_meta_content(soup, "name", "description"),
        get_meta_content(soup, "property", "og:description"),
    )
    excerpt = first_present(meta_description, body_excerpt(soup))

    return PageInput(
        page_type=page_type,
        url=url,
        title=title,
        meta_title=meta_title,
        meta_description=meta_description,
        h1=h1,
        excerpt=excerpt,
        status="published",
        cluster_name=None,
        keyword=first_present(h1, title),
        raw_html=None,
    )


def get_meta_content(soup: BeautifulSoup, attr_name: str, attr_value: str) -> str | None:
    tag = soup.find("meta", attrs={attr_name: attr_value})
    if not tag:
        return None
    return normalize_text(tag.get("content"))


def first_text(soup: BeautifulSoup, tag_name: str) -> str | None:
    tag = soup.find(tag_name)
    if not tag:
        return None
    return normalize_text(tag.get_text(" ", strip=True))


def body_excerpt(soup: BeautifulSoup) -> str | None:
    for tag in soup.find_all(["script", "style", "nav", "footer", "aside"]):
        tag.decompose()
    body = soup.body or soup
    text = normalize_text(body.get_text(" ", strip=True))
    if not text:
        return None
    return text[:160]


def normalize_text(value: object) -> str | None:
    if value is None:
        return None
    text = " ".join(str(value).split())
    return text or None


def first_present(*values: str | None) -> str:
    for value in values:
        if value:
            return value
    return ""
