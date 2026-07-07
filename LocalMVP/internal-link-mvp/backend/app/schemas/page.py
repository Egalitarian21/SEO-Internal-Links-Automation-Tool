from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PageInput(BaseModel):
    page_type: str
    url: str
    title: str
    meta_title: str | None = None
    meta_description: str | None = None
    h1: str | None = None
    excerpt: str | None = None
    status: str = "published"
    cluster_name: str | None = None
    keyword: str | None = None
    raw_html: str | None = None
    handle: str | None = None


class PageImportRequest(BaseModel):
    items: list[PageInput] = Field(default_factory=list)


class PageImportResponse(BaseModel):
    created: int
    updated: int
    skipped: int


class PageUrlImportRequest(BaseModel):
    urls: list[str] = Field(default_factory=list)


class PageUrlImportItem(BaseModel):
    url: str
    status: str
    page_type: str | None = None
    title: str | None = None
    reason: str | None = None


class PageUrlImportResponse(BaseModel):
    created: int
    updated: int
    skipped: int
    failed: int
    items: list[PageUrlImportItem]


class ImportJobItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    url: str
    status: str
    page_type: str | None = None
    title: str | None = None
    reason: str | None = None
    created_at: datetime
    updated_at: datetime


class ImportJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: str
    total: int
    processed: int
    created: int
    updated: int
    skipped: int
    failed: int
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    items: list[ImportJobItemOut]


class PageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    page_type: str
    url: str
    canonical_url: str
    handle: str | None = None
    title: str
    meta_title: str | None = None
    meta_description: str | None = None
    h1: str | None = None
    excerpt: str | None = None
    status: str
    cluster_name: str | None = None
    keyword: str | None = None
    raw_html: str | None = None
    content_hash: str | None = None
    created_at: datetime
    updated_at: datetime


class PageListResponse(BaseModel):
    items: list[PageOut]


class DashboardStats(BaseModel):
    total_pages: int
    blog_count: int
    collection_count: int
    product_count: int
    recent_snapshots: list[dict]
