from bs4 import BeautifulSoup


def clean_html(html: str) -> str:
    """Remove script/style/noscript tags and return normalized HTML."""
    soup = BeautifulSoup(html or "", "html.parser")
    for node in soup(["script", "style", "noscript"]):
        node.decompose()
    return str(soup)
