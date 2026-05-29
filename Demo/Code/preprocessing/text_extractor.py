from bs4 import BeautifulSoup


def extract_title(html: str) -> str:
    """Extract a page title with h1 fallback."""
    soup = BeautifulSoup(html or "", "html.parser")
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    h1 = soup.find("h1")
    return h1.get_text(" ", strip=True) if h1 else ""


def extract_headings(html: str) -> list[dict[str, str | int]]:
    """Extract h1-h6 headings as level/text dictionaries."""
    soup = BeautifulSoup(html or "", "html.parser")
    headings: list[dict[str, str | int]] = []
    for level in range(1, 7):
        for node in soup.find_all(f"h{level}"):
            text = node.get_text(" ", strip=True)
            if text:
                headings.append({"level": level, "text": text})
    return headings


def extract_text(html: str) -> str:
    """Extract visible text from HTML."""
    soup = BeautifulSoup(html or "", "html.parser")
    return soup.get_text(" ", strip=True)
