from link_recommendation.anchor_candidate_generator import generate_anchor_candidates
from link_recommendation.internal_link_selector import select_internal_links


def recommend_internal_links(blog_text: str, page_candidates: list[dict], max_links: int = 8) -> list[dict]:
    """Create a minimal internal-link recommendation list from page candidates."""
    anchors = generate_anchor_candidates(blog_text)
    candidates: list[dict] = []
    for index, page in enumerate(page_candidates):
        anchor = anchors[index] if index < len(anchors) else str(page.get("title", ""))
        candidates.append(
            {
                "anchor_text": anchor,
                "target_url": page.get("url", ""),
                "target_title": page.get("title", ""),
            }
        )
    return select_internal_links(candidates, max_links=max_links)
