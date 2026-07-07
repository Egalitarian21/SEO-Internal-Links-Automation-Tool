from dataclasses import dataclass

from bs4 import BeautifulSoup, Tag


@dataclass
class ParsedBlock:
    block_index: int
    block_type: str
    heading_level: str | None
    section_title: str | None
    content: str
    raw_html: str
    has_existing_link: bool
    link_count: int
    is_first_paragraph: bool


SKIP_TAGS = {"script", "style", "nav", "footer", "aside", "table"}


def parse_article_blocks(raw_html: str) -> list[ParsedBlock]:
    soup = BeautifulSoup(raw_html, "html.parser")
    for tag in soup.find_all(SKIP_TAGS):
        tag.decompose()

    blocks: list[ParsedBlock] = []
    section_title: str | None = None
    first_paragraph_seen = False

    for node in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li"]):
        if not isinstance(node, Tag):
            continue
        if _is_nested_in_collected_block(node):
            continue
        if _is_img_only(node):
            continue

        text = " ".join(node.get_text(" ", strip=True).split())
        if not text:
            continue

        tag_name = node.name.lower()
        block_type = "heading" if tag_name.startswith("h") else "paragraph" if tag_name == "p" else "list_item"
        heading_level = tag_name if block_type == "heading" else None
        is_first_paragraph = False

        if tag_name in {"h2", "h3"}:
            section_title = text

        if block_type == "paragraph" and not first_paragraph_seen:
            is_first_paragraph = True
            first_paragraph_seen = True

        link_count = len(node.find_all("a"))
        blocks.append(
            ParsedBlock(
                block_index=len(blocks) + 1,
                block_type=block_type,
                heading_level=heading_level,
                section_title=section_title,
                content=text,
                raw_html=str(node),
                has_existing_link=link_count > 0,
                link_count=link_count,
                is_first_paragraph=is_first_paragraph,
            )
        )

    return blocks


def _is_img_only(node: Tag) -> bool:
    text = node.get_text(strip=True)
    images = node.find_all("img")
    return not text and bool(images)


def _is_nested_in_collected_block(node: Tag) -> bool:
    parent = node.parent
    while isinstance(parent, Tag):
        if parent.name and parent.name.lower() in {"p", "li"}:
            return True
        parent = parent.parent
    return False
