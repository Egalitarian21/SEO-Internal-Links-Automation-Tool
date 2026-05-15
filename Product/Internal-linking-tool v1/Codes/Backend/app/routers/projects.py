from datetime import datetime

from fastapi import APIRouter

from app.models.tables import Project, now_iso, short_id, store
from app.schemas.dto import CreateProjectRequest


router = APIRouter()


@router.get("/dashboard")
def get_dashboard() -> dict:
    projects = store.project_list()
    tasks = list(store.tasks.values())
    active_tasks = [task for task in tasks if task.status in {"queued", "running"}]
    return {
        "data": {
            "summary": {
                "projects": len(projects),
                "articles": len(store.articles),
                "wiki_cards": len(store.cards),
                "approved_suggestions": len([item for item in store.suggestions.values() if item.status == "approved"]),
                "active_tasks": len(active_tasks),
            },
            "recent_tasks": [store.to_jsonable(task) for task in sorted(tasks, key=lambda item: item.updated_at, reverse=True)[:5]],
        }
    }


@router.get("/projects")
def list_projects() -> dict:
    return {"data": [store.to_jsonable(project) for project in store.project_list()]}


@router.post("/projects")
def create_project(request: CreateProjectRequest) -> dict:
    project = Project(
        id=short_id("proj"),
        name=request.name,
        domain=request.domain,
        owner=request.owner,
        status="active",
        created_at=now_iso(),
        last_activity_at=now_iso(),
        health_score=75,
        imported_urls=0,
        wiki_cards=0,
        approved_suggestions=0,
        publish_success_rate=0,
        description=request.description,
    )
    with store.lock:
        store.projects[project.id] = project
        store.imported_urls[project.id] = []
        store.review_logs[project.id] = []
        store.persist()
    return {"data": store.to_jsonable(project)}


@router.get("/projects/{project_id}")
def get_project(project_id: str) -> dict:
    project = store.projects[project_id]
    project_articles = [article for article in store.articles.values() if article.project_id == project_id]
    project_suggestions = [item for item in store.suggestions.values() if item.project_id == project_id]
    return {
        "data": {
            **store.to_jsonable(project),
            "metrics": {
                "articles": len(project_articles),
                "pending_review": len([item for item in project_suggestions if item.status == "pending"]),
                "approved": len([item for item in project_suggestions if item.status == "approved"]),
                "tasks_today": len(
                    [
                        task
                        for task in store.tasks.values()
                        if task.project_id == project_id
                        and datetime.fromisoformat(task.created_at.replace("Z", "")) >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                    ]
                ),
            },
        }
    }
