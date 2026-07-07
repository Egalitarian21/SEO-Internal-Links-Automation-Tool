import re
from dataclasses import dataclass

STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "how", "in", "is", "it",
    "of", "on", "or", "that", "the", "this", "to", "with", "your", "you", "can", "make",
}


@dataclass
class RecommendationScore:
    target_page_id: object
    score_total: float
    score_cluster: float
    score_keyword: float
    score_page_type: float
    score_semantic: float
    score_title: float
    score_history: float
    score_quality: float
    penalty_duplicate: float
    penalty_competition: float
    penalty_over_optimization: float
    penalty_distance: float
    reason_json: dict
    target_page: object


def tokens(text: str | None) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]+", (text or "").lower()) if token not in STOP_WORDS}


def score_target(source_page, anchor_candidate, target_page) -> RecommendationScore | None:
    source_html = source_page.raw_html or ""
    if target_page.id == source_page.id or not target_page.canonical_url:
        return None
    if target_page.canonical_url in source_html:
        return None

    anchor = anchor_candidate.anchor_text.lower()
    target_keyword = (target_page.keyword or "").lower()
    target_title = f"{target_page.title or ''} {target_page.h1 or ''}".strip()

    score_cluster = 0
    if target_page.cluster_name and source_page.cluster_name:
        score_cluster = 20 if target_page.cluster_name.lower() == source_page.cluster_name.lower() else 12

    score_keyword = 0
    if target_keyword and anchor == target_keyword:
        score_keyword = 20
    elif target_keyword and (anchor in target_keyword or target_keyword in anchor):
        score_keyword = 15
    elif tokens(anchor) & tokens(target_title):
        score_keyword = 12

    suggestion = anchor_candidate.link_type_suggestion
    if target_page.page_type == suggestion:
        score_page_type = 15
    elif suggestion == "collection" and target_page.page_type == "product":
        score_page_type = 10
    elif suggestion == "product" and target_page.page_type == "collection":
        score_page_type = 8
    elif suggestion == "blog" and target_page.page_type in {"collection", "product"}:
        score_page_type = 5
    else:
        score_page_type = 0

    source_tokens = tokens(f"{anchor_candidate.anchor_text} {anchor_candidate.context_text}")
    target_tokens = tokens(
        f"{target_page.title or ''} {target_page.h1 or ''} {target_page.meta_description or ''} {target_page.excerpt or ''} {target_page.keyword or ''}"
    )
    union = source_tokens | target_tokens
    similarity = len(source_tokens & target_tokens) / len(union) if union else 0
    score_semantic = similarity * 25

    anchor_tokens = tokens(anchor_candidate.anchor_text)
    title_tokens = tokens(target_title)
    score_title = (len(anchor_tokens & title_tokens) / len(anchor_tokens) * 10) if anchor_tokens else 0
    score_history = 2.5
    score_quality = sum(
        [
            1 if target_page.status == "published" else 0,
            1 if target_page.canonical_url else 0,
            1 if target_page.title else 0,
            1 if target_page.meta_description else 0,
            1 if target_page.h1 else 0,
        ]
    )
    penalty_duplicate = 0
    penalty_competition = 20 if target_page.page_type == "blog" and target_page.keyword and target_page.keyword == source_page.keyword else 0
    penalty_over_optimization = 0
    penalty_distance = 15 if score_semantic < 3 else 8 if score_semantic < 6 else 0

    total = (
        score_cluster
        + score_keyword
        + score_page_type
        + score_semantic
        + score_title
        + score_history
        + score_quality
        - penalty_duplicate
        - penalty_competition
        - penalty_over_optimization
        - penalty_distance
    )
    score_total = round(min(max(total, 0), 100), 2)

    matched_fields = []
    if score_cluster:
        matched_fields.append("cluster_name")
    if score_keyword:
        matched_fields.append("keyword/title/h1")
    if score_page_type:
        matched_fields.append("page_type")

    return RecommendationScore(
        target_page_id=target_page.id,
        score_total=score_total,
        score_cluster=score_cluster,
        score_keyword=score_keyword,
        score_page_type=score_page_type,
        score_semantic=round(score_semantic, 2),
        score_title=round(score_title, 2),
        score_history=score_history,
        score_quality=score_quality,
        penalty_duplicate=penalty_duplicate,
        penalty_competition=penalty_competition,
        penalty_over_optimization=penalty_over_optimization,
        penalty_distance=penalty_distance,
        reason_json={"summary": "根据主题集群、关键词、页面类型和文本相似度综合评分。", "matched_fields": matched_fields},
        target_page=target_page,
    )


def rank_recommendations(source_page, anchor_candidate, target_pages) -> list[RecommendationScore]:
    scored = [score for page in target_pages if (score := score_target(source_page, anchor_candidate, page))]
    scored.sort(
        key=lambda item: (
            item.score_total,
            item.target_page.page_type == anchor_candidate.link_type_suggestion,
            item.score_semantic,
            item.score_keyword,
        ),
        reverse=True,
    )
    return scored[:3]
