from fastapi import APIRouter

from app.models.tables import store


router = APIRouter()


@router.get("/projects/{project_id}/tasks")
def list_project_tasks(project_id: str) -> dict:
    tasks = [task for task in store.tasks.values() if task.project_id == project_id]
    tasks.sort(key=lambda item: item.updated_at, reverse=True)
    return {"data": [store.to_jsonable(task) for task in tasks]}


@router.get("/tasks/{task_id}")
def get_task(task_id: str) -> dict:
    return {"data": store.to_jsonable(store.tasks[task_id])}

