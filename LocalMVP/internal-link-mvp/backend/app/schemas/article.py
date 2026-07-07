from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ArticleBlockOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    block_index: int
    block_type: str
    heading_level: str | None = None
    section_title: str | None = None
    content: str
    raw_html: str | None = None
    has_existing_link: bool
    link_count: int
    is_first_paragraph: bool


class ParseArticleResponse(BaseModel):
    page_id: UUID
    block_count: int
    blocks: list[ArticleBlockOut]


class ArticleBlocksResponse(BaseModel):
    items: list[ArticleBlockOut]
