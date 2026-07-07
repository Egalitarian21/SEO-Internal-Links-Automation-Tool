from bs4 import BeautifulSoup, NavigableString


def build_anchor_html(target_url: str, anchor_text: str) -> str:
    return f'<a href="{target_url}">{anchor_text}</a>'


def insert_anchor_in_block(block_raw_html: str, anchor_text: str, target_url: str) -> tuple[str | None, str | None]:
    soup = BeautifulSoup(block_raw_html, "html.parser")
    replacement_html = build_anchor_html(target_url, anchor_text)

    for text_node in soup.find_all(string=True):
        if not isinstance(text_node, NavigableString):
            continue
        if text_node.find(anchor_text) == -1:
            continue
        if text_node.find_parent("a"):
            return None, "锚文本位于已有链接内部，不能插入。"
        if text_node.find_parent(["h1", "h2", "h3", "h4", "h5", "h6"]):
            return None, "标题内部不能插入链接。"

        before, after = str(text_node).split(anchor_text, 1)
        fragment = BeautifulSoup(f"{before}{replacement_html}{after}", "html.parser")
        text_node.replace_with(fragment)
        return str(soup), None

    return None, "锚文本跨多个 HTML text node 或无法在块中精确定位。"


def generate_preview_html(source_html: str, insertions: list[dict]) -> tuple[str, dict]:
    errors: list[str] = []
    warnings: list[str] = []
    preview_html = source_html
    used_target_urls = {item["target_url"] for item in insertions if item["target_url"] in source_html}
    grouped: dict[str, dict] = {}

    for item in insertions:
        block = item["block"]
        key = block.raw_html or ""
        grouped.setdefault(key, {"block": block, "items": []})["items"].append(item)

    for block_raw_html, group in grouped.items():
        block = group["block"]
        if not block_raw_html or block_raw_html not in preview_html:
            errors.append("无法在原文中定位正文块。")
            continue

        next_block_html = block_raw_html
        for item in group["items"]:
            target_url = item["target_url"]
            candidate = item["candidate"]

            if target_url in used_target_urls:
                warnings.append(f"目标 URL 已存在，已跳过：{target_url}")
                continue
            if block.content[candidate.start_offset : candidate.end_offset] != candidate.anchor_text:
                errors.append(f"offset 已失效，无法插入：{candidate.anchor_text}")
                continue

            new_block_html, error = insert_anchor_in_block(next_block_html, candidate.anchor_text, target_url)
            if error:
                errors.append(error)
                continue
            next_block_html = new_block_html or next_block_html
            used_target_urls.add(target_url)

        preview_html = preview_html.replace(block_raw_html, next_block_html, 1)

    return preview_html, {"passed": not errors, "errors": errors, "warnings": warnings}
