from fastapi import APIRouter

from app.models.tables import now_iso, store
from app.schemas.dto import BatchReviewRequest, ReviewSuggestionRequest


router = APIRouter()


@router.post("/review/suggestions/{suggestion_id}")
def review_suggestion(suggestion_id: str, request: ReviewSuggestionRequest) -> dict:
    with store.lock:
        suggestion = store.suggestions[suggestion_id]
        suggestion.status = request.action
        suggestion.edited_anchor_text = request.edited_anchor_text
        store.projects[suggestion.project_id].last_activity_at = now_iso()
        approved_count = len(
            [
                item
                for item in store.suggestions.values()
                if item.project_id == suggestion.project_id and item.status == "approved"
            ]
        )
        store.projects[suggestion.project_id].approved_suggestions = approved_count
        store.append_review_log(
            suggestion.project_id,
            {
                "suggestion_id": suggestion_id,
                "action": request.action,
                "reviewer": "demo-user",
                "edited_anchor": request.edited_anchor_text,
                "time": now_iso(),
            },
        )
        store.persist()
    return {"data": store.to_jsonable(suggestion)}


@router.post("/review/batch")
def batch_review(request: BatchReviewRequest) -> dict:
    updated = []
    with store.lock:
        project_id = None
        for suggestion_id in request.suggestion_ids:
            suggestion = store.suggestions[suggestion_id]
            suggestion.status = request.action
            project_id = suggestion.project_id
            store.append_review_log(
                suggestion.project_id,
                {
                    "suggestion_id": suggestion_id,
                    "action": request.action,
                    "reviewer": "demo-user",
                    "edited_anchor": suggestion.edited_anchor_text,
                    "time": now_iso(),
                },
            )
            updated.append(store.to_jsonable(suggestion))
        if project_id:
            store.projects[project_id].approved_suggestions = len(
                [
                    item
                    for item in store.suggestions.values()
                    if item.project_id == project_id and item.status == "approved"
                ]
            )
            store.projects[project_id].last_activity_at = now_iso()
        store.persist()
    return {"data": {"updated": updated, "count": len(updated)}}
