from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import ImportJob, Page, Snapshot, utc_now
from app.db.session import get_db
from app.schemas.page import (
    DashboardStats,
    PageImportRequest,
    PageImportResponse,
    PageInput,
    PageListResponse,
    PageOut,
    PageUrlImportRequest,
    ImportJobOut,
)
from app.services.canonical import canonicalize_url, content_hash, normalize_raw_content
from app.services.import_jobs import create_import_job, run_import_url_job

router = APIRouter(prefix="/pages", tags=["页面"])
dashboard_router = APIRouter(prefix="/dashboard", tags=["仪表盘"])


@dashboard_router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    total_pages = db.scalar(select(func.count()).select_from(Page)) or 0
    blog_count = db.scalar(select(func.count()).select_from(Page).where(Page.page_type == "blog")) or 0
    collection_count = db.scalar(select(func.count()).select_from(Page).where(Page.page_type == "collection")) or 0
    product_count = db.scalar(select(func.count()).select_from(Page).where(Page.page_type == "product")) or 0
    snapshots = db.scalars(select(Snapshot).order_by(Snapshot.created_at.desc()).limit(5)).all()
    return DashboardStats(
        total_pages=total_pages,
        blog_count=blog_count,
        collection_count=collection_count,
        product_count=product_count,
        recent_snapshots=[
            {"id": str(item.id), "source_page_id": str(item.source_page_id), "snapshot_type": item.snapshot_type, "created_at": item.created_at.isoformat()}
            for item in snapshots
        ],
    )


@router.post("/import", response_model=PageImportResponse)
def import_pages(payload: PageImportRequest, db: Session = Depends(get_db)):
    created = 0
    updated = 0
    skipped = 0

    for item in payload.items:
        result = upsert_page(item, db)
        if result == "created":
            created += 1
        elif result == "updated":
            updated += 1
        else:
            skipped += 1

    db.commit()
    return PageImportResponse(created=created, updated=updated, skipped=skipped)


@router.post("/import-urls", response_model=ImportJobOut)
def import_urls(payload: PageUrlImportRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    job = create_import_job(payload.urls, db)
    if job.status != "completed":
        background_tasks.add_task(run_import_url_job, job.id, upsert_page)
    return load_import_job_or_404(job.id, db)


@router.get("/import-url-jobs/latest", response_model=ImportJobOut | None)
def get_latest_import_job(db: Session = Depends(get_db)):
    tenant_id = get_settings().default_tenant_id
    job = db.scalar(select(ImportJob).where(ImportJob.tenant_id == tenant_id).order_by(ImportJob.created_at.desc()))
    if not job:
        return None
    return load_import_job_or_404(job.id, db)


@router.get("/import-url-jobs/{job_id}", response_model=ImportJobOut)
def get_import_job(job_id: UUID, db: Session = Depends(get_db)):
    return load_import_job_or_404(job_id, db)


@router.get("", response_model=PageListResponse)
def list_pages(
    page_type: str | None = None,
    status: str | None = None,
    query: str | None = None,
    db: Session = Depends(get_db),
):
    statement = select(Page).order_by(Page.updated_at.desc())
    if page_type:
        statement = statement.where(Page.page_type == page_type)
    if status:
        statement = statement.where(Page.status == status)
    if query:
        like = f"%{query}%"
        statement = statement.where(or_(Page.title.ilike(like), Page.url.ilike(like), Page.keyword.ilike(like), Page.cluster_name.ilike(like)))
    return PageListResponse(items=list(db.scalars(statement).all()))


@router.get("/{page_id}", response_model=PageOut)
def get_page(page_id: UUID, db: Session = Depends(get_db)):
    page = db.get(Page, page_id)
    if not page:
        raise HTTPException(status_code=404, detail="页面不存在。")
    return page


@router.post("", response_model=PageOut)
def create_or_update_page(payload: PageInput, db: Session = Depends(get_db)):
    upsert_page(payload, db)
    db.commit()
    page = db.scalar(select(Page).where(Page.tenant_id == get_settings().default_tenant_id, Page.canonical_url == canonicalize_url(payload.url)))
    if not page:
        raise HTTPException(status_code=500, detail="页面保存失败。")
    return page


def load_import_job_or_404(job_id: UUID, db: Session) -> ImportJob:
    tenant_id = get_settings().default_tenant_id
    job = db.scalar(select(ImportJob).where(ImportJob.id == job_id, ImportJob.tenant_id == tenant_id))
    if not job:
        raise HTTPException(status_code=404, detail="导入任务不存在。")
    _ = job.items
    return job


def upsert_page(item: PageInput, db: Session) -> str:
    if item.page_type not in {"blog", "collection", "product"}:
        return "skipped"
    if item.status not in {"published", "draft", "archived"}:
        return "skipped"
    if not item.url or not item.title:
        return "skipped"

    tenant_id = get_settings().default_tenant_id
    canonical_url = canonicalize_url(item.url)
    raw_html = normalize_raw_content(item.raw_html)
    now = utc_now()
    page = db.scalar(select(Page).where(Page.tenant_id == tenant_id, Page.canonical_url == canonical_url))

    values = {
        "page_type": item.page_type,
        "url": item.url,
        "canonical_url": canonical_url,
        "handle": item.handle,
        "title": item.title,
        "meta_title": item.meta_title,
        "meta_description": item.meta_description,
        "h1": item.h1,
        "excerpt": item.excerpt,
        "status": item.status,
        "cluster_name": item.cluster_name,
        "keyword": item.keyword,
        "raw_html": raw_html,
        "content_hash": content_hash(raw_html),
        "updated_at": now,
    }

    if page:
        for key, value in values.items():
            setattr(page, key, value)
        return "updated"

    db.add(Page(tenant_id=tenant_id, created_at=now, **values))
    return "created"
