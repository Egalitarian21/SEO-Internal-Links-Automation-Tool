from app.models.tables import Card, store


class VectorRepo:
    def find_candidates(self, project_id: str, query: str) -> list[Card]:
        query_tokens = set(query.lower().split())
        ranked = []
        for card in store.cards.values():
            if card.project_id != project_id:
                continue
            score = len(query_tokens & set(" ".join(card.keywords).lower().split()))
            if score:
                ranked.append((score, card))
        ranked.sort(key=lambda item: item[0], reverse=True)
        return [card for _, card in ranked[:5]]


vector_repo = VectorRepo()

