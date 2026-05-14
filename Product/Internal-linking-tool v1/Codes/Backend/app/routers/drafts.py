from fastapi import APIRouter

from app.models.tables import store


router = APIRouter()


@router.get("/projects/{project_id}/articles")
def list_articles(project_id: str) -> dict:
    articles = [article for article in store.articles.values() if article.project_id == project_id]
    return {"data": [store.to_jsonable(article) for article in articles]}

