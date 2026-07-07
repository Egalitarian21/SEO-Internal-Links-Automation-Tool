from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SnapshotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source_page_id: UUID
    snapshot_type: str
    before_html: str
    after_html: str
    preview_id: UUID | None = None
    created_at: datetime


class SnapshotListResponse(BaseModel):
    items: list[SnapshotOut]


class RollbackResponse(BaseModel):
    snapshot_id: UUID
    rollback_snapshot_id: UUID
    status: str
