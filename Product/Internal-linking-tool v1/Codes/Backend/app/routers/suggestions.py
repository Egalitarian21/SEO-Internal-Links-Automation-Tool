from fastapi import APIRouter, Query

from app.schemas.dto import GenerateSuggestionsRequest
from app.services.recommend_service import recommend_service


router = APIRouter()


@router.post("/projects/{project_id}/suggestions/generate")
def generate_suggestions(project_id: str, request: GenerateSuggestionsRequest) -> dict:
    task_id = recommend_service.start_generation(project_id, request.article_id)
    return {"data": {"task_id": task_id, "message": "Recommendation task queued."}}


@router.get("/projects/{project_id}/suggestions")
def list_suggestions(project_id: str, article_id: str | None = None) -> dict:
    return {"data": recommend_service.list_suggestions(project_id, article_id=article_id)}


@router.get("/projects/{project_id}/review-queue")
def review_queue(project_id: str) -> dict:
    return {"data": recommend_service.list_suggestions(project_id, review_only=True)}


@router.get("/projects/{project_id}/reverse-links")
def reverse_links(project_id: str) -> dict:
    return {"data": recommend_service.reverse_links(project_id)}

