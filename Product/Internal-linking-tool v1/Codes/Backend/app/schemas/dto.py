from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class CreateProjectRequest(BaseModel):
    name: str = Field(min_length=2)
    domain: str = Field(min_length=3)
    owner: str = Field(min_length=2)
    description: str = Field(min_length=10)


class ImportRequest(BaseModel):
    urls: list[str] = Field(min_length=1)


class UpdateCardRequest(BaseModel):
    summary: str = Field(min_length=12)
    keywords: list[str] = Field(min_length=1)
    status: Literal["draft", "published", "review_needed"]


class GenerateSuggestionsRequest(BaseModel):
    article_id: str


class ReviewSuggestionRequest(BaseModel):
    action: Literal["approved", "rejected", "pending"]
    edited_anchor_text: str | None = None


class BatchReviewRequest(BaseModel):
    suggestion_ids: list[str] = Field(min_length=1)
    action: Literal["approved", "rejected"]


class PublishRequest(BaseModel):
    article_ids: list[str] = Field(min_length=1)


class TaskResponse(BaseModel):
    task_id: str
    message: str


class ApiEnvelope(BaseModel):
    data: Any

