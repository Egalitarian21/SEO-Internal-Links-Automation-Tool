"""初始化 MVP 数据表

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-07-01
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def uuid_type():
    return postgresql.UUID(as_uuid=True)


def json_type():
    return postgresql.JSONB()


def upgrade() -> None:
    op.create_table(
        "pages",
        sa.Column("id", uuid_type(), primary_key=True),
        sa.Column("tenant_id", uuid_type(), nullable=False),
        sa.Column("page_type", sa.String(32), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("canonical_url", sa.Text(), nullable=False),
        sa.Column("handle", sa.String(255), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("meta_title", sa.Text(), nullable=True),
        sa.Column("meta_description", sa.Text(), nullable=True),
        sa.Column("h1", sa.Text(), nullable=True),
        sa.Column("excerpt", sa.Text(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("cluster_name", sa.Text(), nullable=True),
        sa.Column("keyword", sa.Text(), nullable=True),
        sa.Column("raw_html", sa.Text(), nullable=True),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("page_type IN ('blog', 'collection', 'product')", name="ck_pages_page_type"),
        sa.CheckConstraint("status IN ('published', 'draft', 'archived')", name="ck_pages_status"),
        sa.UniqueConstraint("tenant_id", "canonical_url", name="uq_pages_tenant_canonical_url"),
    )
    op.create_index("ix_pages_tenant_id", "pages", ["tenant_id"])

    op.create_table(
        "article_blocks",
        sa.Column("id", uuid_type(), primary_key=True),
        sa.Column("tenant_id", uuid_type(), nullable=False),
        sa.Column("page_id", uuid_type(), sa.ForeignKey("pages.id", ondelete="CASCADE"), nullable=False),
        sa.Column("block_index", sa.Integer(), nullable=False),
        sa.Column("block_type", sa.String(32), nullable=False),
        sa.Column("heading_level", sa.String(8), nullable=True),
        sa.Column("section_title", sa.Text(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("raw_html", sa.Text(), nullable=True),
        sa.Column("has_existing_link", sa.Boolean(), nullable=False),
        sa.Column("link_count", sa.Integer(), nullable=False),
        sa.Column("is_first_paragraph", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_article_blocks_page_id", "article_blocks", ["page_id"])
    op.create_index("ix_article_blocks_tenant_id", "article_blocks", ["tenant_id"])

    op.create_table(
        "anchor_candidates",
        sa.Column("id", uuid_type(), primary_key=True),
        sa.Column("tenant_id", uuid_type(), nullable=False),
        sa.Column("source_page_id", uuid_type(), sa.ForeignKey("pages.id", ondelete="CASCADE"), nullable=False),
        sa.Column("article_block_id", uuid_type(), sa.ForeignKey("article_blocks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("anchor_text", sa.Text(), nullable=False),
        sa.Column("context_text", sa.Text(), nullable=False),
        sa.Column("link_type_suggestion", sa.String(32), nullable=False),
        sa.Column("start_offset", sa.Integer(), nullable=False),
        sa.Column("end_offset", sa.Integer(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("confidence_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("end_offset > start_offset", name="ck_anchor_offsets"),
        sa.UniqueConstraint("article_block_id", "anchor_text", "start_offset", name="uq_anchor_block_text_offset"),
    )
    op.create_index("ix_anchor_candidates_article_block_id", "anchor_candidates", ["article_block_id"])
    op.create_index("ix_anchor_candidates_source_page_id", "anchor_candidates", ["source_page_id"])
    op.create_index("ix_anchor_candidates_tenant_id", "anchor_candidates", ["tenant_id"])

    op.create_table(
        "link_recommendations",
        sa.Column("id", uuid_type(), primary_key=True),
        sa.Column("tenant_id", uuid_type(), nullable=False),
        sa.Column("anchor_candidate_id", uuid_type(), sa.ForeignKey("anchor_candidates.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_page_id", uuid_type(), sa.ForeignKey("pages.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("score_total", sa.Numeric(5, 2), nullable=False),
        sa.Column("score_cluster", sa.Numeric(5, 2), nullable=False),
        sa.Column("score_keyword", sa.Numeric(5, 2), nullable=False),
        sa.Column("score_page_type", sa.Numeric(5, 2), nullable=False),
        sa.Column("score_semantic", sa.Numeric(5, 2), nullable=False),
        sa.Column("score_title", sa.Numeric(5, 2), nullable=False),
        sa.Column("score_history", sa.Numeric(5, 2), nullable=False),
        sa.Column("score_quality", sa.Numeric(5, 2), nullable=False),
        sa.Column("penalty_duplicate", sa.Numeric(5, 2), nullable=False),
        sa.Column("penalty_competition", sa.Numeric(5, 2), nullable=False),
        sa.Column("penalty_over_optimization", sa.Numeric(5, 2), nullable=False),
        sa.Column("penalty_distance", sa.Numeric(5, 2), nullable=False),
        sa.Column("reason_json", json_type(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_link_recommendations_anchor_candidate_id", "link_recommendations", ["anchor_candidate_id"])
    op.create_index("ix_link_recommendations_target_page_id", "link_recommendations", ["target_page_id"])
    op.create_index("ix_link_recommendations_tenant_id", "link_recommendations", ["tenant_id"])

    op.create_table(
        "link_decisions",
        sa.Column("id", uuid_type(), primary_key=True),
        sa.Column("tenant_id", uuid_type(), nullable=False),
        sa.Column("source_page_id", uuid_type(), sa.ForeignKey("pages.id", ondelete="CASCADE"), nullable=False),
        sa.Column("anchor_candidate_id", uuid_type(), sa.ForeignKey("anchor_candidates.id", ondelete="CASCADE"), nullable=False),
        sa.Column("selected_target_page_id", uuid_type(), sa.ForeignKey("pages.id"), nullable=True),
        sa.Column("manual_target_url", sa.Text(), nullable=True),
        sa.Column("decision", sa.String(32), nullable=False),
        sa.Column("reviewer_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_link_decisions_anchor_candidate_id", "link_decisions", ["anchor_candidate_id"])
    op.create_index("ix_link_decisions_source_page_id", "link_decisions", ["source_page_id"])
    op.create_index("ix_link_decisions_tenant_id", "link_decisions", ["tenant_id"])

    op.create_table(
        "insertion_previews",
        sa.Column("id", uuid_type(), primary_key=True),
        sa.Column("tenant_id", uuid_type(), nullable=False),
        sa.Column("source_page_id", uuid_type(), sa.ForeignKey("pages.id", ondelete="CASCADE"), nullable=False),
        sa.Column("before_html", sa.Text(), nullable=False),
        sa.Column("preview_html", sa.Text(), nullable=False),
        sa.Column("rule_check_json", json_type(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_insertion_previews_source_page_id", "insertion_previews", ["source_page_id"])
    op.create_index("ix_insertion_previews_tenant_id", "insertion_previews", ["tenant_id"])

    op.create_table(
        "snapshots",
        sa.Column("id", uuid_type(), primary_key=True),
        sa.Column("tenant_id", uuid_type(), nullable=False),
        sa.Column("source_page_id", uuid_type(), sa.ForeignKey("pages.id", ondelete="CASCADE"), nullable=False),
        sa.Column("snapshot_type", sa.String(32), nullable=False),
        sa.Column("before_html", sa.Text(), nullable=False),
        sa.Column("after_html", sa.Text(), nullable=False),
        sa.Column("preview_id", uuid_type(), sa.ForeignKey("insertion_previews.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_snapshots_source_page_id", "snapshots", ["source_page_id"])
    op.create_index("ix_snapshots_tenant_id", "snapshots", ["tenant_id"])

    op.create_table(
        "audit_logs",
        sa.Column("id", uuid_type(), primary_key=True),
        sa.Column("tenant_id", uuid_type(), nullable=False),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("entity_type", sa.String(64), nullable=False),
        sa.Column("entity_id", uuid_type(), nullable=True),
        sa.Column("before_json", json_type(), nullable=True),
        sa.Column("after_json", json_type(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_logs_tenant_id", "audit_logs", ["tenant_id"])

    op.create_table(
        "app_settings",
        sa.Column("id", uuid_type(), primary_key=True),
        sa.Column("tenant_id", uuid_type(), nullable=False),
        sa.Column("key", sa.String(128), nullable=False),
        sa.Column("value_json", json_type(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_app_settings_tenant_id", "app_settings", ["tenant_id"])


def downgrade() -> None:
    op.drop_table("app_settings")
    op.drop_table("audit_logs")
    op.drop_table("snapshots")
    op.drop_table("insertion_previews")
    op.drop_table("link_decisions")
    op.drop_table("link_recommendations")
    op.drop_table("anchor_candidates")
    op.drop_table("article_blocks")
    op.drop_table("pages")
