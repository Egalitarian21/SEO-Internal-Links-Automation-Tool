from pathlib import Path
from xml.etree import ElementTree


def parse_sitemap(source: str | Path) -> list[str]:
    """Parse a Sitemap XML file/string and return URL locations."""
    text = Path(source).read_text(encoding="utf-8") if Path(str(source)).exists() else str(source)
    root = ElementTree.fromstring(text)
    urls: list[str] = []
    for node in root.iter():
        if node.tag.endswith("loc") and node.text:
            urls.append(node.text.strip())
    return [url for url in urls if url]
