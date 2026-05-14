from fastapi import APIRouter

from app.schemas.dto import UpdateCardRequest
from app.services.card_service import card_service


router = APIRouter()


@router.get("/projects/{project_id}/cards")
def list_cards(project_id: str) -> dict:
    return {"data": card_service.list_cards(project_id)}


@router.patch("/cards/{card_id}")
def update_card(card_id: str, request: UpdateCardRequest) -> dict:
    card = card_service.update_card(card_id, request.summary, request.keywords, request.status)
    return {"data": card}

