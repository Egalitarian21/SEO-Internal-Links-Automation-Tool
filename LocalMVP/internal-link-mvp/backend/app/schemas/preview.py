from uuid import UUID

from pydantic import BaseModel


class RuleCheck(BaseModel):
    passed: bool
    errors: list[str]
    warnings: list[str]


class PreviewResponse(BaseModel):
    preview_id: UUID
    preview_html: str
    rule_check: RuleCheck


class LocalWriteRequest(BaseModel):
    preview_id: UUID


class LocalWriteResponse(BaseModel):
    snapshot_id: UUID
    status: str
