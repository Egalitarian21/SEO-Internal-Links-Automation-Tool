from uuid import UUID

from pydantic import BaseModel


class RecommendationGenerateResponse(BaseModel):
    source_page_id: UUID
    created: int


class RecommendationOut(BaseModel):
    id: UUID
    target_page_id: UUID
    rank: int
    url: str
    title: str
    page_type: str
    meta_description: str | None = None
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


class AnchorRecommendationGroup(BaseModel):
    anchor_candidate_id: UUID
    anchor_text: str
    context_text: str
    link_type_suggestion: str
    reason: str | None = None
    status: str
    recommendations: list[RecommendationOut]


class RecommendationListResponse(BaseModel):
    items: list[AnchorRecommendationGroup]
