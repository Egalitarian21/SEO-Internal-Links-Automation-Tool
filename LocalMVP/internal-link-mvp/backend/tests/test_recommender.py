from dataclasses import dataclass
from uuid import uuid4

from app.services.recommender import rank_recommendations, score_target


@dataclass
class Page:
    id: object
    page_type: str
    title: str
    canonical_url: str
    keyword: str
    cluster_name: str = "Nursery Furniture"
    h1: str = ""
    meta_description: str = ""
    excerpt: str = ""
    status: str = "published"
    raw_html: str = ""


@dataclass
class Anchor:
    id: object
    anchor_text: str
    context_text: str
    link_type_suggestion: str = "collection"


def test_exact_keyword_match_scores_high():
    source = Page(uuid4(), "blog", "Source", "https://example.com/source", "source")
    target = Page(uuid4(), "collection", "Glider Recliners", "https://example.com/collections/glider", "glider recliner", h1="Glider Recliners")
    anchor = Anchor(uuid4(), "glider recliner", "Compare glider recliner options.")

    score = score_target(source, anchor, target)

    assert score is not None
    assert score.score_keyword == 20
    assert score.score_total > 50


def test_existing_target_is_excluded():
    source = Page(uuid4(), "blog", "Source", "https://example.com/source", "source", raw_html='<a href="https://example.com/collections/glider">Glider</a>')
    target = Page(uuid4(), "collection", "Glider Recliners", "https://example.com/collections/glider", "glider recliner")
    anchor = Anchor(uuid4(), "glider recliner", "Compare glider recliner options.")

    assert score_target(source, anchor, target) is None


def test_top_three_only():
    source = Page(uuid4(), "blog", "Source", "https://example.com/source", "source")
    anchor = Anchor(uuid4(), "glider recliner", "Compare glider recliner options.")
    targets = [Page(uuid4(), "collection", f"Glider Recliners {i}", f"https://example.com/{i}", "glider recliner") for i in range(5)]

    ranked = rank_recommendations(source, anchor, targets)

    assert len(ranked) == 3


def test_score_total_clamped():
    source = Page(uuid4(), "blog", "Source", "https://example.com/source", "source")
    target = Page(uuid4(), "collection", "Glider Recliner Glider Recliner", "https://example.com/target", "glider recliner", h1="Glider Recliner")
    anchor = Anchor(uuid4(), "glider recliner", "glider recliner " * 20)

    score = score_target(source, anchor, target)

    assert score is not None
    assert 0 <= score.score_total <= 100
