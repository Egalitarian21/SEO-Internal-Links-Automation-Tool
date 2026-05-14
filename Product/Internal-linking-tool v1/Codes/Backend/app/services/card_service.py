from app.models.tables import store


class CardService:
    def list_cards(self, project_id: str) -> list[dict]:
        cards = [card for card in store.cards.values() if card.project_id == project_id]
        return [store.to_jsonable(card) for card in cards]

    def update_card(self, card_id: str, summary: str, keywords: list[str], status: str) -> dict:
        with store.lock:
            card = store.cards[card_id]
            card.summary = summary
            card.keywords = keywords
            card.status = status
            return store.to_jsonable(card)


card_service = CardService()

