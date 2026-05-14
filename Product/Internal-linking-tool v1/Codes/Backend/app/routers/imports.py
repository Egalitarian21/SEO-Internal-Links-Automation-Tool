from fastapi import APIRouter

from app.schemas.dto import ImportRequest
from app.services.import_service import import_service


router = APIRouter()


@router.post("/projects/{project_id}/import")
def start_import(project_id: str, request: ImportRequest) -> dict:
    task_id = import_service.start_import(project_id, request.urls)
    return {"data": {"task_id": task_id, "message": "Import job queued."}}

