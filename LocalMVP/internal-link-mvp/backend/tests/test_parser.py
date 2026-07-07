from app.services.parser import parse_article_blocks


def test_headings_are_recognized():
    blocks = parse_article_blocks("<h1>Title</h1><h2>Section</h2><p>Body paragraph here.</p>")

    headings = [block for block in blocks if block.block_type == "heading"]
    assert [block.heading_level for block in headings] == ["h1", "h2"]


def test_first_paragraph_marked():
    blocks = parse_article_blocks("<p>First paragraph text.</p><p>Second paragraph text.</p>")

    paragraphs = [block for block in blocks if block.block_type == "paragraph"]
    assert paragraphs[0].is_first_paragraph is True
    assert paragraphs[1].is_first_paragraph is False


def test_existing_link_detected():
    blocks = parse_article_blocks('<p>Read this <a href="/x">linked text</a>.</p>')

    assert blocks[0].has_existing_link is True
    assert blocks[0].link_count == 1


def test_table_is_skipped():
    blocks = parse_article_blocks("<table><tr><td>Skip me</td></tr></table><p>Keep me here.</p>")

    assert len(blocks) == 1
    assert blocks[0].content == "Keep me here."
