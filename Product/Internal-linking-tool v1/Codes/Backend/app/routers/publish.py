from fastapi import APIRouter, Query

from app.schemas.dto import PublishRequest
from app.services.publish_service import publish_service


router = APIRouter()


@router.get("/projects/{project_id}/publish/checklist")
def publish_checklist(project_id: str, article_ids: str | None = Query(default=None)) -> dict:
    selected = article_ids.split(",") if article_ids else None
    return {"data": publish_service.checklist(project_id, selected)}


@router.post("/projects/{project_id}/publish")
def publish(project_id: str, request: PublishRequest) -> dict:
    task_id = publish_service.start_publish(project_id, request.article_ids)
    return {"data": {"task_id": task_id, "message": "Publish task queued."}}


@router.post("/publish/jobs/{job_id}/rollback")
def rollback(job_id: str) -> dict:
    return {"data": publish_service.rollback(job_id)}

