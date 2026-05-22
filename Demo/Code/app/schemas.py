from datetime import datetime

from pydantic import BaseModel, Field


class HNode(BaseModel):
    level: int
    text: str


class WikiCard(BaseModel):
    customer: str
    url: str
    Title: str
    Description: str = ""
    H_Hierarchy: list[HNode] = Field(default_factory=list)
    Web_Abstract_AI_Generated: str


class FailedItem(BaseModel):
    url: str
    error_code: str
    message: str


class DiscardedItem(BaseModel):
    target_url: str = ""
    reason: str
    details: str = ""


class IntakeRequest(BaseModel):
    customer: str
    urls: list[str] | None = None
    blog_url: str | None = None
    blog_markdown: str | None = None


class IntakeResult(BaseModel):
    customer: str
    new_urls_added: int
    duplicate_urls_skipped: int
    total_urls_in_db: int
    blog_md_saved: bool
    dirs_ready: list[str]


class GenerateRequest(BaseModel):
    customer: str
    batch_size: int = 10
    only_missing: bool = True


class GenerateResult(BaseModel):
    customer: str
    total_todo: int
    success: int
    failed: list[FailedItem]
    cards_generated: list[str]
    elapsed_seconds: float


class RecommendRequest(BaseModel):
    customer: str
    blog_url: str
    blog_markdown: str
    blog_title: str | None = None
    score_threshold: float = 0.6
    max_recommendations: int = 8


class Recommendation(BaseModel):
    target_url: str
    target_title: str
    anchor_text: str
    insert_paragraph: str
    relevance_score: float
    reason: str


class RecommendResult(BaseModel):
    customer: str
    blog_url: str
    blog_title: str | None
    candidates_filtered: int
    recommendations: list[Recommendation]
    discarded: list[DiscardedItem]
    library_size: int
    elapsed_seconds: float


class ReportRequest(BaseModel):
    customer: str
    blog_url: str
    recommend_result: RecommendResult


class ReportResult(BaseModel):
    customer: str
    blog_url: str
    excel_path: str
    file_name: str
    rows_written: int
    file_size_bytes: int
    generated_at: datetime

