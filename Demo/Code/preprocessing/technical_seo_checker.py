from preprocessing.text_extractor import extract_headings, extract_title


def check_basic_seo(html: str) -> dict[str, bool | int]:
    """Run minimal technical SEO checks for skeleton development."""
    headings = extract_headings(html)
    return {
        "has_title": bool(extract_title(html)),
        "h1_count": sum(1 for item in headings if item["level"] == 1),
        "has_headings": bool(headings),
    }
