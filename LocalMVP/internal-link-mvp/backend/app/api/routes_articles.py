from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import ArticleBlock, Page
from app.db.session import get_db
from app.schemas.article import ArticleBlocksResponse, ParseArticleResponse
from app.services.parser import parse_article_blocks

router = APIRouter(prefix="/articles", tags=["正文解析"])


@router.post("/{page_id}/parse", response_model=ParseArticleResponse)
def parse_article(page_id: UUID, db: Session = Depends(get_db)):
    page = db.get(Page, page_id)
    if not page:
        raise HTTPException(status_code=404, detail="页面不存在。")
    if page.page_type != "blog":
        raise HTTPException(status_code=400, detail="只有 blog 页面可以解析正文。")
    if not page.raw_html:
        raise HTTPException(status_code=400, detail="raw_html 不能为空。")

    db.execute(delete(ArticleBlock).where(ArticleBlock.page_id == page.id))
    parsed_blocks = parse_article_blocks(page.raw_html)
    blocks = [
        ArticleBlock(
            tenant_id=get_settings().default_tenant_id,
            page_id=page.id,
            block_index=item.block_index,
            block_type=item.block_type,
            heading_level=item.heading_level,
            section_title=item.section_title,
            content=item.content,
            raw_html=item.raw_html,
            has_existing_link=item.has_existing_link,
            link_count=item.link_count,
            is_first_paragraph=item.is_first_paragraph,
        )
        for item in parsed_blocks
    ]
    db.add_all(blocks)
    db.commit()
    for block in blocks:
        db.refresh(block)
    return ParseArticleResponse(page_id=page.id, block_count=len(blocks), blocks=blocks)


@router.get("/{page_id}/blocks", response_model=ArticleBlocksResponse)
def list_blocks(page_id: UUID, db: Session = Depends(get_db)):
    blocks = db.scalars(select(ArticleBlock).where(ArticleBlock.page_id == page_id).order_by(ArticleBlock.block_index)).all()
    return ArticleBlocksResponse(items=list(blocks))
