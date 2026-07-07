"""新增 URL 导入任务表

Revision ID: 0002_import_jobs
Revises: 0001_initial_schema
Create Date: 2026-07-03
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0002_import_jobs"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def uuid_type():
    return postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "import_jobs",
        sa.Column("id", uuid_type(), primary_key=True),
        sa.Column("tenant_id", uuid_type(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("total", sa.Integer(), nullable=False),
        sa.Column("processed", sa.Integer(), nullable=False),
        sa.Column("created", sa.Integer(), nullable=False),
        sa.Column("updated", sa.Integer(), nullable=False),
        sa.Column("skipped", sa.Integer(), nullable=False),
        sa.Column("failed", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_import_jobs_tenant_id", "import_jobs", ["tenant_id"])

    op.create_table(
        "import_job_items",
        sa.Column("id", uuid_type(), primary_key=True),
        sa.Column("tenant_id", uuid_type(), nullable=False),
        sa.Column("job_id", uuid_type(), sa.ForeignKey("import_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("page_type", sa.String(32), nullable=True),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_import_job_items_job_id", "import_job_items", ["job_id"])
    op.create_index("ix_import_job_items_tenant_id", "import_job_items", ["tenant_id"])


def downgrade() -> None:
    op.drop_table("import_job_items")
    op.drop_table("import_jobs")
