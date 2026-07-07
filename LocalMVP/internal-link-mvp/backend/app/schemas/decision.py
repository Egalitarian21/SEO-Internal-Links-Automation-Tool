from uuid import UUID

from pydantic import BaseModel


class DecisionInput(BaseModel):
    anchor_candidate_id: UUID
    decision: str
    selected_target_page_id: UUID | None = None
    manual_target_url: str | None = None
    reviewer_note: str | None = None


class DecisionsRequest(BaseModel):
    decisions: list[DecisionInput]


class DecisionsResponse(BaseModel):
    created: int
