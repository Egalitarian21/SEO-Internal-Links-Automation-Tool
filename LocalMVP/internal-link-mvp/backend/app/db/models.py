from datetime import datetime, timezone
from uuid import UUID
from uuid import uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base

JSON_FIELD = JSON().with_variant(JSONB(), "postgresql")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Page(Base):
    __tablename__ = "pages"
    __table_args__ = (
        CheckConstraint("page_type IN ('blog', 'collection', 'product')", name="ck_pages_page_type"),
        CheckConstraint("status IN ('published', 'draft', 'archived')", name="ck_pages_status"),
        UniqueConstraint("tenant_id", "canonical_url", name="uq_pages_tenant_canonical_url"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    page_type: Mapped[str] = mapped_column(String(32), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    canonical_url: Mapped[str] = mapped_column(Text, nullable=False)
    handle: Mapped[str | None] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(Text, nullable=False)
    meta_title: Mapped[str | None] = mapped_column(Text)
    meta_description: Mapped[str | None] = mapped_column(Text)
    h1: Mapped[str | None] = mapped_column(Text)
    excerpt: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="published")
    cluster_name: Mapped[str | None] = mapped_column(Text)
    keyword: Mapped[str | None] = mapped_column(Text)
    raw_html: Mapped[str | None] = mapped_column(Text)
    content_hash: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    blocks: Mapped[list["ArticleBlock"]] = relationship(back_populates="page", cascade="all, delete-orphan")


class ArticleBlock(Base):
    __tablename__ = "article_blocks"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    page_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("pages.id", ondelete="CASCADE"), nullable=False, index=True)
    block_index: Mapped[int] = mapped_column(Integer, nullable=False)
    block_type: Mapped[str] = mapped_column(String(32), nullable=False)
    heading_level: Mapped[str | None] = mapped_column(String(8))
    section_title: Mapped[str | None] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    raw_html: Mapped[str | None] = mapped_column(Text)
    has_existing_link: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    link_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_first_paragraph: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    page: Mapped[Page] = relationship(back_populates="blocks")


class AnchorCandidate(Base):
    __tablename__ = "anchor_candidates"
    __table_args__ = (
        CheckConstraint("end_offset > start_offset", name="ck_anchor_offsets"),
        UniqueConstraint("article_block_id", "anchor_text", "start_offset", name="uq_anchor_block_text_offset"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    source_page_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("pages.id", ondelete="CASCADE"), nullable=False, index=True)
    article_block_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("article_blocks.id", ondelete="CASCADE"), nullable=False, index=True)
    anchor_text: Mapped[str] = mapped_column(Text, nullable=False)
    context_text: Mapped[str] = mapped_column(Text, nullable=False)
    link_type_suggestion: Mapped[str] = mapped_column(String(32), nullable=False)
    start_offset: Mapped[int] = mapped_column(Integer, nullable=False)
    end_offset: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    confidence_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class LinkRecommendation(Base):
    __tablename__ = "link_recommendations"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    anchor_candidate_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("anchor_candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    target_page_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("pages.id", ondelete="CASCADE"), nullable=False, index=True)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    score_total: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    score_cluster: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    score_keyword: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    score_page_type: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    score_semantic: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    score_title: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    score_history: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    score_quality: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    penalty_duplicate: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    penalty_competition: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    penalty_over_optimization: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    penalty_distance: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    reason_json: Mapped[dict] = mapped_column(JSON_FIELD, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class LinkDecision(Base):
    __tablename__ = "link_decisions"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    source_page_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("pages.id", ondelete="CASCADE"), nullable=False, index=True)
    anchor_candidate_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("anchor_candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    selected_target_page_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("pages.id"))
    manual_target_url: Mapped[str | None] = mapped_column(Text)
    decision: Mapped[str] = mapped_column(String(32), nullable=False)
    reviewer_note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class InsertionPreview(Base):
    __tablename__ = "insertion_previews"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    source_page_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("pages.id", ondelete="CASCADE"), nullable=False, index=True)
    before_html: Mapped[str] = mapped_column(Text, nullable=False)
    preview_html: Mapped[str] = mapped_column(Text, nullable=False)
    rule_check_json: Mapped[dict] = mapped_column(JSON_FIELD, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class Snapshot(Base):
    __tablename__ = "snapshots"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    source_page_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("pages.id", ondelete="CASCADE"), nullable=False, index=True)
    snapshot_type: Mapped[str] = mapped_column(String(32), nullable=False)
    before_html: Mapped[str] = mapped_column(Text, nullable=False)
    after_html: Mapped[str] = mapped_column(Text, nullable=False)
    preview_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("insertion_previews.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    before_json: Mapped[dict | None] = mapped_column(JSON_FIELD)
    after_json: Mapped[dict | None] = mapped_column(JSON_FIELD)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class AppSetting(Base):
    __tablename__ = "app_settings"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    key: Mapped[str] = mapped_column(String(128), nullable=False)
    value_json: Mapped[dict] = mapped_column(JSON_FIELD, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)


class ImportJob(Base):
    __tablename__ = "import_jobs"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    processed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    skipped: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    items: Mapped[list["ImportJobItem"]] = relationship(back_populates="job", cascade="all, delete-orphan")


class ImportJobItem(Base):
    __tablename__ = "import_job_items"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    job_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("import_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    page_type: Mapped[str | None] = mapped_column(String(32))
    title: Mapped[str | None] = mapped_column(Text)
    reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    job: Mapped[ImportJob] = relationship(back_populates="items")
