from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AnchorCandidateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source_page_id: UUID
    article_block_id: UUID
    anchor_text: str
    context_text: str
    link_type_suggestion: str
    start_offset: int
    end_offset: int
    reason: str | None = None
    confidence_score: float
    status: str


class AnchorGenerateResponse(BaseModel):
    source_page_id: UUID
    created: int
    items: list[AnchorCandidateOut]


class AnchorListResponse(BaseModel):
    items: list[AnchorCandidateOut]
