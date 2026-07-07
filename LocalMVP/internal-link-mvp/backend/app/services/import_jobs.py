from uuid import UUID

from sqlalchemy import select

from app.core.config import get_settings
from app.db.models import ImportJob, ImportJobItem, utc_now
from app.db.session import SessionLocal
from app.services.page_fetcher import fetch_url_as_page_input


def run_import_url_job(job_id: UUID, upsert_page_func) -> None:
    db = SessionLocal()
    try:
        job = db.get(ImportJob, job_id)
        if not job:
            return
        job.status = "running"
        job.updated_at = utc_now()
        db.commit()

        items = db.scalars(
            select(ImportJobItem)
            .where(ImportJobItem.job_id == job_id, ImportJobItem.status == "queued")
            .order_by(ImportJobItem.created_at)
        ).all()
        for item in items:
            item.status = "running"
            item.updated_at = utc_now()
            db.commit()

            try:
                fetched = fetch_url_as_page_input(item.url)
                if not fetched.page:
                    item.status = "failed"
                    item.reason = fetched.reason or "抓取失败。"
                    job.failed += 1
                else:
                    result = upsert_page_func(fetched.page, db)
                    item.status = result
                    item.page_type = fetched.page.page_type
                    item.title = fetched.page.title
                    item.reason = None if result in {"created", "updated"} else "页面数据不符合入库规则。"
                    if result == "created":
                        job.created += 1
                    elif result == "updated":
                        job.updated += 1
                    else:
                        job.skipped += 1
                job.processed += 1
                item.updated_at = utc_now()
                job.updated_at = utc_now()
                db.commit()
            except Exception as exc:  # pragma: no cover - defensive background-task guard
                db.rollback()
                item = db.get(ImportJobItem, item.id)
                job = db.get(ImportJob, job_id)
                if item and job:
                    item.status = "failed"
                    item.reason = f"导入失败：{exc}"
                    item.updated_at = utc_now()
                    job.failed += 1
                    job.processed += 1
                    job.updated_at = utc_now()
                    db.commit()

        job = db.get(ImportJob, job_id)
        if job:
            job.status = "completed"
            job.completed_at = utc_now()
            job.updated_at = utc_now()
            db.commit()
    except Exception as exc:  # pragma: no cover - defensive background-task guard
        db.rollback()
        job = db.get(ImportJob, job_id)
        if job:
            job.status = "failed"
            job.error_message = str(exc)
            job.completed_at = utc_now()
            job.updated_at = utc_now()
            db.commit()
    finally:
        db.close()


def create_import_job(urls: list[str], db) -> ImportJob:
    tenant_id = get_settings().default_tenant_id
    seen_urls: set[str] = set()
    normalized_urls: list[tuple[str, str]] = []
    for raw_url in urls:
        url = raw_url.strip()
        if not url:
            continue
        if url in seen_urls:
            normalized_urls.append((url, "duplicate"))
            continue
        seen_urls.add(url)
        normalized_urls.append((url, "queued"))

    job = ImportJob(
        tenant_id=tenant_id,
        status="queued",
        total=len(normalized_urls),
        processed=0,
        created=0,
        updated=0,
        skipped=0,
        failed=0,
    )
    db.add(job)
    db.flush()

    for url, status in normalized_urls:
        item = ImportJobItem(
            tenant_id=tenant_id,
            job_id=job.id,
            url=url,
            status="skipped" if status == "duplicate" else "queued",
            reason="重复 URL，已跳过。" if status == "duplicate" else None,
        )
        db.add(item)
        if status == "duplicate":
            job.processed += 1
            job.skipped += 1

    if job.total == job.processed:
        job.status = "completed"
        job.completed_at = utc_now()

    db.commit()
    db.refresh(job)
    return job
