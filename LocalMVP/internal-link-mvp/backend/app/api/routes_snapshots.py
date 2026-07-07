from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import AuditLog, Page, Snapshot
from app.db.session import get_db
from app.schemas.snapshot import RollbackResponse, SnapshotListResponse
from app.services.canonical import content_hash

router = APIRouter(prefix="/snapshots", tags=["快照"])


@router.get("", response_model=SnapshotListResponse)
def list_snapshots(source_page_id: UUID | None = Query(default=None), db: Session = Depends(get_db)):
    statement = select(Snapshot).order_by(Snapshot.created_at.desc())
    if source_page_id:
        statement = statement.where(Snapshot.source_page_id == source_page_id)
    return SnapshotListResponse(items=list(db.scalars(statement).all()))


@router.post("/{snapshot_id}/rollback", response_model=RollbackResponse)
def rollback(snapshot_id: UUID, db: Session = Depends(get_db)):
    snapshot = db.get(Snapshot, snapshot_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail="快照不存在。")
    page = db.get(Page, snapshot.source_page_id)
    if not page:
        raise HTTPException(status_code=404, detail="页面不存在。")

    before = page.raw_html or ""
    page.raw_html = snapshot.before_html
    page.content_hash = content_hash(page.raw_html)
    rollback_snapshot = Snapshot(
        tenant_id=get_settings().default_tenant_id,
        source_page_id=page.id,
        snapshot_type="rollback",
        before_html=before,
        after_html=page.raw_html or "",
        preview_id=snapshot.preview_id,
    )
    audit = AuditLog(
        tenant_id=get_settings().default_tenant_id,
        action="rollback",
        entity_type="pages",
        entity_id=page.id,
        before_json={"raw_html": before, "snapshot_id": str(snapshot.id)},
        after_json={"raw_html": page.raw_html},
    )
    db.add_all([rollback_snapshot, audit])
    db.commit()
    db.refresh(rollback_snapshot)
    return RollbackResponse(snapshot_id=snapshot.id, rollback_snapshot_id=rollback_snapshot.id, status="rolled_back")
